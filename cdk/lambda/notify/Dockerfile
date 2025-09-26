FROM public.ecr.aws/lambda/python:3.11

# Copia solo il codice
COPY app.py ${LAMBDA_TASK_ROOT}

# Comando di avvio Lambda
CMD ["app.handler"]
