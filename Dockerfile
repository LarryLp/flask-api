FROM frolvlad/alpine-python3:latest

RUN pip install flask
RUN pip install flask_apscheduler
RUN pip install pyyaml
RUN pip install pyjwt

WORKDIR /app
COPY utils.py .
COPY api.py .

CMD [ "python", "./api.py"]
