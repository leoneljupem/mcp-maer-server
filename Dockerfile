# Dockerfile para MAER MCP Server
# Ejecuta MAER en un entorno Linux aislado y compatible con cualquier sistema operativo (Windows/Mac/Linux)

FROM python:3.12-slim

# Instalar dependencias del sistema requeridas para OCR y Node.js
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-spa \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copiar archivos de requerimientos
COPY requirements.txt package.json ./

# Instalar dependencias
RUN npm install
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir thefuzz python-Levenshtein pdfplumber pytesseract easyocr

# Copiar el código fuente
COPY . .

# Exponer el puerto del Dashboard Web
EXPOSE 8765

# Iniciar servidor web en segundo plano y servidor MCP en primer plano
CMD ["/bin/bash", "-c", "python maer_backend/web_ui/server.py & node index.mjs"]
