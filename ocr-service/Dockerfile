FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV OCR_THREADS=8
ENV OMP_NUM_THREADS=8
ENV ORT_NUM_THREADS=8

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]