FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=./

COPY src/ /app/src/

CMD ["streamlit", "run", "src/main.py"]