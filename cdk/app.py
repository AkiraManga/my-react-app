#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk.cdk_stack import CdkStack


app = cdk.App()
CdkStack(app, "CdkStack",
    # Passa l'ambiente (account e regione)
    env=cdk.Environment(account='384981131796', region='eu-west-3'),

    # Per un ambiente dinamico, puoi usare:
    # env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
    )

app.synth()