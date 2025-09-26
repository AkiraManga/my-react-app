# Base ufficiale AWS Lambda Python 3.12 (contiene già boto3/botocore)
FROM public.ecr.aws/lambda/python:3.12

# Copia il codice della Lambda (handler = app.handler)
COPY app.py ${LAMBDA_TASK_ROOT}/

# Se in futuro ti servono dipendenze aggiuntive (non boto3), puoi:
# RUN python -m pip install --no-cache-dir <package> -t ${LAMBDA_TASK_ROOT}

# Imposta l'handler
CMD ["app.handler"]
