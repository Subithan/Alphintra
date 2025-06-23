FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    wget \
    autotools-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Install TA-Lib C library (required for ta-lib Python package)
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    cp /usr/share/misc/config.guess . && \
    cp /usr/share/misc/config.sub . && \
    ./configure --prefix=/usr --build=aarch64-unknown-linux-gnu && \
    make && \
    make install && \
    ldconfig && \
    cd .. && \
    rm -rf ta-lib ta-lib-0.4.0-src.tar.gz

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]