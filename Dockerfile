FROM frolvlad/alpine-python3:latest

WORKDIR /app
COPY main.py .

CMD [ "python", "./main.py", "ALL"]
