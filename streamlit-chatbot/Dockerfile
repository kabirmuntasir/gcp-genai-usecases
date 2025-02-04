FROM python:3.9-slim

WORKDIR /app

COPY src/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY src/ .

CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]