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
    aws_sns as sns,                       # 👈 aggiunto
    aws_sns_subscriptions as subs,        # 👈 aggiunto
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_events as events,
    aws_events_targets as targets,
    aws_logs as logs,
    aws_ecs_patterns as ecs_patterns,
    aws_secretsmanager as secretsmanager,
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
        # SNS Topic per notifiche Like
        # --------------------------
        likes_topic = sns.Topic(
            self, "CommentLikesTopic",
            topic_name="comment-likes-topic"
        )

        # (Opzionale) Aggiungi una subscription email fissa per test
        # Ricorda che chi riceve dovrà confermare l’iscrizione cliccando sull’email
        likes_topic.add_subscription(
            subs.EmailSubscription("tua_email_di_test@example.com")
        )


        # --------------------------
        # CloudFront Distribution SOLO con OAC
        # --------------------------
        distribution = cloudfront.CfnDistribution(
            self, "FrontendDistribution",
            distribution_config=cloudfront.CfnDistribution.DistributionConfigProperty(
                enabled=True,
                default_root_object="index.html",
                origins=[
                    cloudfront.CfnDistribution.OriginProperty(
                        id="S3Origin",
                        domain_name=website_bucket.bucket_regional_domain_name,
                        s3_origin_config=cloudfront.CfnDistribution.S3OriginConfigProperty(
                            origin_access_identity=""  # vuoto perché usi OAC
                        ),
                        origin_access_control_id=oac.get_att("Id").to_string()
                    )
                ],
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
                        response_page_path="/index.html"
                    ),
                    cloudfront.CfnDistribution.CustomErrorResponseProperty(
                        error_code=404,
                        response_code=200,
                        response_page_path="/index.html"
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
                callback_urls=[f"https://{distribution.attr_domain_name}/callback"],  # ✅ URL CloudFront
                logout_urls=[f"https://{distribution.attr_domain_name}"],             # ✅ URL CloudFront
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
        charts_table = dynamodb.Table(
            self, "ChartsTable",
            partition_key={"name": "chart_key", "type": dynamodb.AttributeType.STRING},
            sort_key={"name": "rank", "type": dynamodb.AttributeType.NUMBER},  # 👈 AGGIUNTO
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # IMPORT del secret già esistente (nessuna creazione)
        spotify_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "SpotifyCredentialsImported",   # id diverso solo per chiarezza
            "spotify/credentials"
        )


        vpc = ec2.Vpc(
            self, "SpotifyScraperVpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[ec2.SubnetConfiguration(name="public", subnet_type=ec2.SubnetType.PUBLIC)],
        )

        cluster = ecs.Cluster(self, "SpotifyScraperCluster", vpc=vpc)



        # 🔹 GSI per ricerche case-insensitive sul titolo
        albums_table.add_global_secondary_index(
            index_name="TitleLowerIndex",
            partition_key=dynamodb.Attribute(
                name="title_lower",
                type=dynamodb.AttributeType.STRING,
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # 🔹 GSI per ricerche via slug (URL friendly)
        albums_table.add_global_secondary_index(
            index_name="TitleSlugIndex",
            partition_key=dynamodb.Attribute(
                name="title_slug",
                type=dynamodb.AttributeType.STRING,
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # --------------------------
        # Lambda: Notify (invia email con SES)
        # --------------------------
        notify_fn = _lambda.DockerImageFunction(
            self, "NotifyLambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda/notify"),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                "SES_SOURCE_EMAIL": "tua_email_verificata@dominio.com"
            },
        )

        # Permessi SES per inviare email
        notify_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ses:SendEmail", "ses:SendRawEmail"],
                resources=["*"]
            )
        )

        # --------------------------
        # Lambda Ratings
        # --------------------------
        ratings_fn = _lambda.DockerImageFunction(
            self, "RatingsLambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda/ratings"),
            environment={
                "RATINGS_TABLE": ratings_table.table_name,
                "ALBUMS_TABLE": albums_table.table_name,   # 👈 aggiungi la virgola qui
                "USERS_TABLE": users_table.table_name,
                "SNS_TOPIC_ARN": likes_topic.topic_arn,   # 👈 nuovo
            },

            timeout=Duration.seconds(30),
            memory_size=256,
        )

        ratings_table.grant_read_write_data(ratings_fn)
        albums_table.grant_read_write_data(ratings_fn)
        users_table.grant_read_data(ratings_fn)
        likes_topic.grant_publish(ratings_fn)


        # Collego notify_fn a ratings_fn
        ratings_fn.add_environment("NOTIFY_LAMBDA_NAME", notify_fn.function_name)
        notify_fn.grant_invoke(ratings_fn)




        # --------------------------
        # Lambda per leggere album (SOLO Docker)
        # --------------------------
        get_albums_fn = _lambda.DockerImageFunction(
            self, "GetAlbumsLambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda/albums"),
            environment={
                "ALBUMS_TABLE": albums_table.table_name
            },
            timeout=Duration.seconds(30),
            memory_size=512,
        )
        albums_table.grant_read_data(get_albums_fn)

        # --------------------------
        # Lambda Functions (Docker)
        # --------------------------
        vote_fn = _lambda.DockerImageFunction(
            self, "VoteLambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda/vote"),
        )
        ratings_table.grant_read_write_data(vote_fn)
        albums_table.grant_read_write_data(vote_fn)

        favorites_fn = _lambda.DockerImageFunction(
            self, "FavoritesLambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda/favorites"),
            environment={              # 👈 aggiunto
                "USERS_TABLE": users_table.table_name
            },
            timeout=Duration.seconds(30),   # (facoltativo: aggiungi timeout e memoria)
            memory_size=256,
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
                "REDIRECT_URI": f"https://{distribution.attr_domain_name}/callback"
            },
            timeout=Duration.seconds(30),
            memory_size=512,
        )

        # --------------------------
        # Lambda per popolare DynamoDB con seed iniziale
        # --------------------------
        seed_data_fn = _lambda.DockerImageFunction(
            self, "SeedDataLambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda/seed_data"),
            environment={
                "ALBUMS_TABLE": albums_table.table_name,
                "USERS_TABLE": users_table.table_name,
                "RATINGS_TABLE": ratings_table.table_name,
            },
            timeout=Duration.minutes(2),
            memory_size=512,
        )
        albums_table.grant_write_data(seed_data_fn)
        users_table.grant_write_data(seed_data_fn)
        ratings_table.grant_write_data(seed_data_fn)

        post_confirmation_fn = _lambda.DockerImageFunction(
            self, "PostConfirmationLambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda/post_confirmation"),
            environment={
                "USERS_TABLE": users_table.table_name,
                "SNS_TOPIC_ARN": likes_topic.topic_arn,   # 👈 nuovo
            },
            timeout=Duration.seconds(30),
            memory_size=256,
        )




        # Permessi DynamoDB + SNS
        users_table.grant_write_data(post_confirmation_fn)
        likes_topic.grant_subscribe(post_confirmation_fn)

        # Collega la Lambda al PostConfirmation di Cognito
        user_pool.add_trigger(cognito.UserPoolOperation.POST_CONFIRMATION, post_confirmation_fn)




        # --------------------------
        # Lambda per migrare da ChartsTable → AlbumsTable
        # --------------------------
        seed_from_charts_fn = _lambda.DockerImageFunction(
            self, "SeedFromChartsLambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda/seed_from_charts"),
            environment={
                "CHARTS_TABLE": charts_table.table_name,
                "ALBUMS_TABLE": albums_table.table_name,
            },
            timeout=Duration.minutes(5),
            memory_size=512,
        )

        charts_table.grant_read_data(seed_from_charts_fn)
        # Permessi completi su AlbumsTable (read + write)
        albums_table.grant_read_write_data(seed_from_charts_fn)

        # --------------------------
        # Lambda SNS Subscribe (Docker)
        # --------------------------
        sns_subscribe_fn = _lambda.DockerImageFunction(
            self, "SnsSubscribeLambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda/sns"),
            environment={
                "USERS_TABLE": users_table.table_name,
                "SNS_TOPIC_ARN": likes_topic.topic_arn,
            },
            timeout=Duration.seconds(30),
            memory_size=256,
        )

        # Permessi: lettura DynamoDB + subscribe a SNS
        users_table.grant_read_data(sns_subscribe_fn)
        likes_topic.grant_subscribe(sns_subscribe_fn)

        # Task per lo scraper Spotify (scrive su ALBUMS_TABLE)
        spotify_task_def = ecs.FargateTaskDefinition(
            self, "SpotifyScraperTaskDef",
            memory_limit_mib=512,
            cpu=256,
        )

        spotify_container = spotify_task_def.add_container(
            "SpotifyScraperContainer",
            image=ecs.ContainerImage.from_asset("containers"),
            logging=ecs.LogDriver.aws_logs(
                stream_prefix="SpotifyScraper",
                log_retention=logs.RetentionDays.ONE_WEEK
            ),
            environment={
                "CHARTS_TABLE": charts_table.table_name,
                "START_YEAR": "1970",
                "END_YEAR": "2025",
                "PER_MARKET_FETCH": "100",
                "TOP_K": "20",
                "AWS_REGION": self.region,
            },
            secrets={
                "SPOTIPY_CLIENT_ID": ecs.Secret.from_secrets_manager(spotify_secret, "SPOTIPY_CLIENT_ID"),
                "SPOTIPY_CLIENT_SECRET": ecs.Secret.from_secrets_manager(spotify_secret, "SPOTIPY_CLIENT_SECRET"),
            },
        )

        # ⬇️ permessi corretti alla task role
        charts_table.grant_read_write_data(spotify_task_def.task_role)
        # (rimuovi la grant su albums_table se non serve più)


        # Permessi DynamoDB per scrivere/leggere gli album
        albums_table.grant_read_write_data(spotify_task_def.task_role)

        # SG di uscita verso Internet
        spotify_sg = ec2.SecurityGroup(self, "SpotifyScraperSG", vpc=vpc, allow_all_outbound=True)


        spotify_rule = events.Rule(
            self, "SpotifyScraperSchedule",
            schedule=events.Schedule.cron(minute="0", hour="3")
        )

        spotify_rule.add_target(targets.EcsTask(
            cluster=cluster,
            task_definition=spotify_task_def,
            subnet_selection=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            security_groups=[spotify_sg],
            assign_public_ip=True,
        ))





        # --------------------------
        # SQS Queue
        # --------------------------
        queue = sqs.Queue(
            self, "AppQueue",
            visibility_timeout=Duration.seconds(30)
        )

        # Producer Lambda
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

        # Consumer Lambda
        consumer_fn = _lambda.DockerImageFunction(
            self, "ConsumerLambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda/consumer"),
            timeout=Duration.seconds(30),
            memory_size=256
        )
        consumer_fn.add_event_source(lambda_event_sources.SqsEventSource(queue))


        # Lambda Charts Read (Docker)
        charts_read_fn = _lambda.DockerImageFunction(
            self, "ChartsReadLambda",
            code=_lambda.DockerImageCode.from_image_asset("lambda/charts_read"),
            environment={
                "CHARTS_TABLE": charts_table.table_name
            },
            timeout=Duration.seconds(30),
            memory_size=256,
        )
        charts_table.grant_read_data(charts_read_fn)




        # --------------------------
        # API Gateway + Cognito Authorizer
        # --------------------------
        authorizer = apigw.CognitoUserPoolsAuthorizer(
            self, "RateYourMusicAuthorizer",
            cognito_user_pools=[user_pool],
        )

        api = apigw.RestApi(
            self, "RateYourMusicApi",
            rest_api_name="RateYourMusicApi",
            deploy_options=apigw.StageOptions(stage_name="prod"),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=["*"],  # oppure [f"https://{distribution.attr_domain_name}"]
                allow_methods=["GET", "POST", "OPTIONS"],
                allow_headers=["Content-Type", "Authorization"],
            )
        )

        # Endpoint GET /albums e /albums/{id} (pubblico)
        albums_resource = api.root.add_resource("albums")
        albums_resource.add_method("GET", apigw.LambdaIntegration(get_albums_fn))
        album_resource = albums_resource.add_resource("{id}")
        album_resource.add_method("GET", apigw.LambdaIntegration(get_albums_fn))
        # ✅ Nuovo endpoint GET /albums/by-title/{title}
        album_by_title = albums_resource.add_resource("by-title").add_resource("{title}")
        album_by_title.add_method("GET", apigw.LambdaIntegration(get_albums_fn))


        # ✅ GET /albums/by-slug/{slug}
        album_by_slug = albums_resource.add_resource("by-slug").add_resource("{slug}")
        album_by_slug.add_method("GET", apigw.LambdaIntegration(get_albums_fn))



        # /ratings
        ratings_resource = api.root.add_resource("ratings")
        # /ratings/{album_id}
        ratings_id = ratings_resource.add_resource("{album_id}")

        ratings_id.add_method(
            "GET",
            apigw.LambdaIntegration(ratings_fn)
        )
        ratings_id.add_method(
            "POST",
            apigw.LambdaIntegration(ratings_fn),
            authorizer=authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
        )

        # /ratings/{album_id}/{review_user_id}/like
        review_user = ratings_id.add_resource("{review_user_id}").add_resource("like")
        review_user.add_method(
            "POST",
            apigw.LambdaIntegration(ratings_fn),
            authorizer=authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
        )





        # /users/favorites/{album_id}
        users_resource = api.root.add_resource("users")

        # aggiungo CORS al livello di /users/favorites
        favorites_resource = users_resource.add_resource(
            "favorites",
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=["*"],   # meglio: [f"https://{distribution.attr_domain_name}"]
                allow_methods=["OPTIONS", "POST"],
                allow_headers=["Content-Type", "Authorization"],
            )
        )

        fav_id = favorites_resource.add_resource("{album_id}")
        fav_id.add_method(
            "POST",
            apigw.LambdaIntegration(favorites_fn),
            authorizer=authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
        )


        # Producer
        producer_resource = api.root.add_resource("producer")
        producer_resource.add_method("POST", apigw.LambdaIntegration(producer_fn))

        # Endpoint pubblico per lo scambio code → token
        auth_resource = api.root.add_resource("auth")
        auth_callback = auth_resource.add_resource("callback")
        auth_callback.add_method("GET", apigw.LambdaIntegration(auth_fn))

        # Vote (protetto)
        api.root.add_resource("vote").add_method(
            "POST",
            apigw.LambdaIntegration(vote_fn),
            authorizer=authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
        )

        # Favorites (protetto)
        api.root.add_resource("favorites").add_method(
            "POST",
            apigw.LambdaIntegration(favorites_fn),
            authorizer=authorizer,
            authorization_type=apigw.AuthorizationType.COGNITO,
        )






        # --- API: /charts/{year} (senza region) ---
        charts_resource = api.root.add_resource("charts")
        charts_year = charts_resource.add_resource("{year}")
        charts_year.add_method(
            "GET",
            apigw.LambdaIntegration(charts_read_fn),
            authorization_type=apigw.AuthorizationType.NONE,
        )



        # --------------------------
        # Deployment automatico del frontend + config.json
        # --------------------------
        import json
        config_data = {
            "cognitoDomain": f"{domain.domain_name}.auth.eu-west-3.amazoncognito.com",
            "clientId": user_pool_client.user_pool_client_id,
            "redirectUri": f"https://{distribution.attr_domain_name}/callback",
            "logoutRedirect": f"https://{distribution.attr_domain_name}",
            "apiBaseUrl": api.url
        }

        s3deploy.BucketDeployment(
            self, "DeployFrontendAndConfig",
            sources=[
                s3deploy.Source.asset("../rate-your-music-app/dist"),
                s3deploy.Source.data("config.json", json.dumps(config_data))
            ],
            destination_bucket=website_bucket,
            distribution=distribution,
            distribution_paths=["/*"],
        )

        from aws_cdk import CfnOutput
        CfnOutput(self, "CloudFrontURL", value=distribution.attr_domain_name)
