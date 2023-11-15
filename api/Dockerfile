FROM python:3.8
WORKDIR /app
COPY . .
RUN pip install flask pymongo
EXPOSE 5000
CMD ["python", "main.py"]