# Dockerfile for Azure IoT Hub Device Simulator
FROM python:3.10-slim

WORKDIR /app
COPY ../backend/data_generator.py .
COPY ../.env .

RUN pip install azure-iot-device python-dotenv

CMD ["python", "data_generator.py"]
