FROM frolvlad/alpine-python3:latest

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir flask
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir flask_apscheduler
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir pyyaml
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir jwt

WORKDIR /app
COPY utils.py .
COPY api.py .

CMD [ "python", "./api.py"]
