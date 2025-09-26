# Immagine base leggera con Python 3.12 per Lambda
FROM public.ecr.aws/lambda/python:3.12

# Copia i file nel container
COPY app.py ${LAMBDA_TASK_ROOT}

# Installa boto3 (anche se in Lambda è già presente, ma non fa male)
RUN pip install boto3

# Imposta l'entrypoint della Lambda (file app.py → funzione handler)
CMD ["app.handler"]
