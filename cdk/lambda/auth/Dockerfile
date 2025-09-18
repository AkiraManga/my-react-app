# Usa l'immagine base AWS Lambda per Python 3.12
FROM public.ecr.aws/lambda/python:3.12

# Copia i file della Lambda dentro il container
COPY auth.py ${LAMBDA_TASK_ROOT}

# (Opzionale) Installa dipendenze, es. requests
# Se hai un requirements.txt nella stessa cartella:
# COPY requirements.txt  .
# RUN pip install -r requirements.txt

# Specifica l'handler: file.funzione
CMD ["auth.handler"]
