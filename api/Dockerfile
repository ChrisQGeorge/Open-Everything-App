FROM python:3.11
WORKDIR /app
COPY . .
RUN pip install fastapi pymongo uvicorn python-multipart pydantic bcrypt authlib passlib python-dotenv
EXPOSE 5000
CMD ["python", "main.py"]