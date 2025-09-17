from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    RemovalPolicy,
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

        # API Gateway REST che punta alla Lambda
        api = apigw.LambdaRestApi(
            self, "RateYourMusicApi",
            handler=lambda_fn,
            proxy=True
        )
