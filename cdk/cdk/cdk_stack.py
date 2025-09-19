from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_cognito as cognito,
    aws_sqs as sqs,
    aws_lambda_event_sources as lambda_event_sources,
    aws_s3_deployment as s3deploy,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    Duration,
    RemovalPolicy,
)
from constructs import Construct


class CdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        # --------------------------
        # S3 Bucket per il frontend (privato)
        # --------------------------
        website_bucket = s3.Bucket(
            self, "FrontendBucket",
            bucket_name="rate-your-music101",  # deve essere unico globalmente
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # privato
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # --------------------------
        # Origin Access Control (OAC) per CloudFront -> S3
        # --------------------------
        oac = cloudfront.CfnOriginAccessControl(
            self, "MyOAC",
            origin_access_control_config=cloudfront.CfnOriginAccessControl.OriginAccessControlConfigProperty(
                name="MyOAC",
                origin_access_control_origin_type="s3",
                signing_behavior="always",
                signing_protocol="sigv4",
                description="OAC per CloudFront -> S3"
            )
        )

        # --------------------------
        # CloudFront Distribution SOLO con OAC
        # --------------------------
        distribution = cloudfront.CfnDistribution(
            self, "FrontendDistribution",
            distribution_config=cloudfront.CfnDistribution.DistributionConfigProperty(
                enabled=True,
                default_root_object="index.html",
                origins=[cloudfront.CfnDistribution.OriginProperty(
                    id="S3Origin",
                    domain_name=website_bucket.bucket_regional_domain_name,
                    s3_origin_config=cloudfront.CfnDistribution.S3OriginConfigProperty(
                        origin_access_identity=""  # ⚠️ vuoto → NO OAI
                    ),
                    origin_access_control_id=oac.get_att("Id").to_string()
                )],
                default_cache_behavior=cloudfront.CfnDistribution.DefaultCacheBehaviorProperty(
                    target_origin_id="S3Origin",
                    viewer_protocol_policy="redirect-to-https",
                    allowed_methods=["GET", "HEAD", "OPTIONS"],
                    cached_methods=["GET", "HEAD", "OPTIONS"],
                    forwarded_values=cloudfront.CfnDistribution.ForwardedValuesProperty(
                        query_string=False,
                        cookies=cloudfront.CfnDistribution.CookiesProperty(forward="none")
                    )
                ),
                custom_error_responses=[
                    cloudfront.CfnDistribution.CustomErrorResponseProperty(
                        error_code=403,
                        response_code=200,
                        response_page_path="/index.html",
                    ),
                    cloudfront.CfnDistribution.CustomErrorResponseProperty(
                        error_code=404,
                        response_code=200,
                        response_page_path="/index.html",
                    )
                ]
            )
        )
         # --------------------------
        # Bucket Policy per permettere a CloudFront di leggere dal bucket
        # --------------------------
        website_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[f"{website_bucket.bucket_arn}/*"],
                principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{distribution.ref}"
                    }
                },
            )
        )

        # --------------------------
        # Deployment automatico dei file buildati
        # --------------------------
        s3deploy.BucketDeployment(
            self, "DeployFrontend",
            sources=[s3deploy.Source.asset("../rate-your-music-app/dist")],  # cartella buildata
            destination_bucket=website_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
        )




        # --------------------------
        # Cognito User Pool
        # --------------------------
        user_pool = cognito.UserPool(
            self, "RateYourMusicUserPool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
            auto_verify=cognito.AutoVerifiedAttrs(email=True),
            password_policy=cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_digits=True
            ),
            removal_policy=RemovalPolicy.DESTROY
        )

        user_pool_client = user_pool.add_client(
            "RateYourMusicClient",
            generate_secret=False,
            auth_flows=cognito.AuthFlow(user_password=True),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,
                    implicit_code_grant=True
                ),
                scopes=[
                    cognito.OAuthScope.OPENID,
                    cognito.OAuthScope.EMAIL,
                    cognito.OAuthScope.PROFILE,
                ],
                callback_urls=["http://localhost:5173/callback"],
                logout_urls=["http://localhost:5173"],
            ),
        )

        domain = user_pool.add_domain(
            "RateYourMusicDomain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix="rateyourmusic101"  # deve essere univoco a livello AWS
            ),
        )

        # --------------------------
        # DynamoDB
        # --------------------------
        users_table = dynamodb.Table(
            self, "UsersTable",
            partition_key={"name": "user_id", "type": dynamodb.AttributeType.STRING},
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        albums_table = dynamodb.Table(
            self, "AlbumsTable",
            partition_key={"name": "album_id", "type": dynamodb.AttributeType.STRING},
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        ratings_table = dynamodb.Table(
            self, "RatingsTable",
            partition_key={"name": "album_id", "type": dynamodb.AttributeType.STRING},
            sort_key={"name": "user_id", "type": dynamodb.AttributeType.STRING},
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # --------------------------
        # Lambda Functions (Docker)
        # --------------------------
        albums_fn = _lambda.DockerImageFunction(
            self, "AlbumsLambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda/albums"),
        )
        albums_table.grant_read_data(albums_fn)

        vote_fn = _lambda.DockerImageFunction(
            self, "VoteLambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda/vote"),
        )
        ratings_table.grant_read_write_data(vote_fn)
        albums_table.grant_read_write_data(vote_fn)

        favorites_fn = _lambda.DockerImageFunction(
            self, "FavoritesLambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda/favorites"),
        )
        users_table.grant_read_write_data(favorites_fn)


        # --------------------------
        # Auth Callback Lambda
        # --------------------------
        auth_fn = _lambda.DockerImageFunction(
            self, "AuthLambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda/auth"),
            environment={
                "COGNITO_DOMAIN": f"{domain.domain_name}.auth.eu-west-3.amazoncognito.com",
                "COGNITO_CLIENT_ID": user_pool_client.user_pool_client_id,
                "REDIRECT_URI": "http://localhost:5173/callback"  # poi sostituirai col dominio reale
            },
            timeout=Duration.seconds(30),
            memory_size=512,
        )
                # --------------------------
        # SQS Queue
        # --------------------------
        queue = sqs.Queue(
            self, "AppQueue",
            visibility_timeout=Duration.seconds(30)
        )

        # --------------------------
        # Producer Lambda (invia messaggi a SQS)
        # --------------------------
        producer_fn = _lambda.DockerImageFunction(
            self, "ProducerLambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda/producer"),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "QUEUE_URL": queue.queue_url
            }
        )
        queue.grant_send_messages(producer_fn)

        # --------------------------
        # Consumer Lambda (consuma messaggi da SQS)
        # --------------------------
        consumer_fn = _lambda.DockerImageFunction(
            self, "ConsumerLambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda/consumer"),
            timeout=Duration.seconds(30),
            memory_size=256
        )

        # Collega la coda alla consumer Lambda
        consumer_fn.add_event_source(lambda_event_sources.SqsEventSource(queue))



        # --------------------------
        # API Gateway + Cognito Authorizer
        # --------------------------
        authorizer = apigw.CognitoUserPoolsAuthorizer(
            self, "RateYourMusicAuthorizer",
            cognito_user_pools=[user_pool],
        )

        api = apigw.RestApi(self, "RateYourMusicApi")

        producer_resource = api.root.add_resource("producer")
        producer_resource.add_method(
            "POST",
            apigw.LambdaIntegration(producer_fn),
            # opzionale: se vuoi proteggerlo con Cognito
            # authorizer=authorizer,
            # authorization_type=apigw.AuthorizationType.COGNITO,
        )


        # Endpoint pubblico per lo scambio code → token
        auth_resource = api.root.add_resource("auth")
        auth_callback = auth_resource.add_resource("callback")
        auth_callback.add_method("GET", apigw.LambdaIntegration(auth_fn))

        api.root.add_resource("albums").add_method(
            "GET",
            apigw.LambdaIntegration(albums_fn),
            authorizer=authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
        )

        api.root.add_resource("vote").add_method(
            "POST",
            apigw.LambdaIntegration(vote_fn),
            authorizer=authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
        )

        api.root.add_resource("favorites").add_method(
            "POST",
            apigw.LambdaIntegration(favorites_fn),
            authorizer=authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
        )
        # Output (così vedi l’URL finale dopo il deploy)
        from aws_cdk import CfnOutput
        CfnOutput(self, "CloudFrontURL", value=distribution.attr_domain_name)

