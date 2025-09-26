FROM public.ecr.aws/lambda/python:3.12

# Copia solo il codice
COPY app.py ${LAMBDA_TASK_ROOT}

# Comando di default per Lambda
CMD ["app.handler"]
