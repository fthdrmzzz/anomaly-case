FROM python:3.8-slim
WORKDIR /app
EXPOSE 5006
COPY requirements.txt .
RUN pip install -r requirements.txt  
COPY . .
CMD ["panel", "serve", "dashboard.py"]
