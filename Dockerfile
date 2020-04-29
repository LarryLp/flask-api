FROM frolvlad/alpine-python3:latest

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir flask
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir flask_apscheduler
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir yaml
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir requests
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir hashlib
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir jwt
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir time

WORKDIR /app
COPY utils.py .
COPY api.py .

CMD [ "python", "./api.py"]
