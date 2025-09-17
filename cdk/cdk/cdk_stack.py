from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    RemovalPolicy,
    aws_cognito as cognito
)
from constructs import Construct

class CdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Rimuovi l'accesso pubblico
        website_bucket = s3.Bucket(self, "FrontendBucket",
            bucket_name="rate-your-music101",  # Deve essere unico globalmente
            website_index_document="index.html",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True
        )

        # Crea una policy per consentire l'accesso al tuo utente IAM
        website_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject"],
                resources=[website_bucket.arn_for_objects("*")],
                principals=[iam.ArnPrincipal("arn:aws:iam::384981131796:user/Salvatore")]
            )
        )

        # Lambda function (codice in lambda/app.py, funzione "handler")
        lambda_fn = _lambda.Function(
            self, "MyLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="app.handler",  # app.py → funzione handler
            code=_lambda.Code.from_asset("lambda")
        )
                # Cognito User Pool
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

        # Client per il frontend React
        user_pool_client = cognito.UserPoolClient(
            self, "RateYourMusicClient",
            user_pool=user_pool,
            generate_secret=False,
            auth_flows=cognito.AuthFlow(user_password=True)
        )

        # Authorizer per API Gateway
        authorizer = apigw.CognitoUserPoolsAuthorizer(
            self, "RateYourMusicAuthorizer",
            cognito_user_pools=[user_pool]
        )
        # API Gateway protetto da Cognito
        api = apigw.LambdaRestApi(
            self, "RateYourMusicApi",
            handler=lambda_fn,
            proxy=True,
            default_method_options={
                "authorizer": authorizer,
                "authorization_type": apigw.AuthorizationType.COGNITO
            }
        )



