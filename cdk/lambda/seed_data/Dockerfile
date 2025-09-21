FROM public.ecr.aws/lambda/python:3.12

# Copio codice e dati
COPY index.py albums.json ${LAMBDA_TASK_ROOT}

# boto3 è già incluso nell'immagine Lambda
CMD ["index.handler"]
