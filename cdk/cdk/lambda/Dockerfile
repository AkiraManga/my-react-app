# Usa l’immagine base per Lambda Python 3.11
FROM public.ecr.aws/lambda/python:3.11

# Copia il codice nel container
COPY app.py ./

# Indica il punto di ingresso (app.handler)
CMD ["app.handler"]
