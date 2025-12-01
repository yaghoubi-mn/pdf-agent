FROM python:3.12-slim

RUN apt-get update && DEBIAN_FRONTEND=noninteractive TESSERACT_LANGUAGES=all apt-get install -y fonts-noto-cjk

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=./

COPY src/ /app/src/

CMD ["streamlit", "run", "src/main.py"]