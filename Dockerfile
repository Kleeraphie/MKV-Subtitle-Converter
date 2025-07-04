FROM debian:12

ENV DISPLAY=:0

RUN apt update && \
    apt install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-tk \
    tesseract-ocr-all \
    ffmpeg && \
    apt-get clean

WORKDIR /app

COPY main.py .
COPY config.py .
COPY backend backend
COPY controller controller
COPY gui gui
COPY languages languages
COPY licenses licenses
COPY requirements.txt requirements.txt

# Create a virtual environment and activate it
RUN python3 -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"

# Install Python dependencies
RUN python3 -m pip install -r requirements.txt

CMD ["python3", "main.py"]