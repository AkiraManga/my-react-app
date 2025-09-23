FROM public.ecr.aws/lambda/python:3.9

# Installiamo boto3 per DynamoDB
RUN pip install boto3

# Copia il codice dentro il container
COPY app.py ${LAMBDA_TASK_ROOT}

CMD ["app.handler"]
