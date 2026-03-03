FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 预设环境变量，指向容器内的数据目录
ENV DATABASE_URL=sqlite:////app/data/labtrack.db
ENV UPLOAD_DIR=/app/data/uploads

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
