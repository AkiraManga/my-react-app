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
        # S3 Bucket per il frontend
        # --------------------------
        website_bucket = s3.Bucket(
            self, "FrontendBucket",
            bucket_name="rate-your-music101",  # deve essere unico globalmente
            website_index_document="index.html",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        # --------------------------
        # CloudFront Distribution
        # --------------------------
        distribution = cloudfront.Distribution(
            self, "FrontendDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(website_bucket)
            ),
            default_root_object="index.html",
        )

        # --------------------------
        # Deployment automatico dei file buildati
        # --------------------------
        s3deploy.BucketDeployment(
            self, "DeployFrontend",
            sources=[s3deploy.Source.asset("../../rate-your-music-app/dist")],  # cartella buildata
            destination_bucket=website_bucket,
            distribution=distribution,          # invalida cache CloudFront
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
        CfnOutput(self, "CloudFrontURL", value=distribution.distribution_domain_name)
