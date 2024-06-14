FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
COPY . .
RUN touch main.log
ENV ENV_FILE_PATH .env
CMD ["sh", "-c", "if [ -f $ENV_FILE_PATH ]; then export $(cat $ENV_FILE_PATH | xargs); fi && python main.py"]
