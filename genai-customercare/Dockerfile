FROM python:3.9-slim

WORKDIR /app

COPY src/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY src/ .
COPY local-terminus-448520-p6-cf8100914c1d.json /app/service-account-key.json

ENV GOOGLE_APPLICATION_CREDENTIALS="/app/service-account-key.json"

CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]