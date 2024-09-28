# Użyj oficjalnego obrazu Pythona jako bazowego
FROM python:3.12.6

# Ustaw zmienną środowiskową dla nieinteraktywnego apt
ENV DEBIAN_FRONTEND=noninteractive

# Zainstaluj zależności systemowe, w tym GDAL i GEOS
RUN apt-get update && apt-get install -y \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    binutils \
    libproj-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Ustaw zmienne środowiskowe dla ścieżek do GDAL i GEOS
ENV CPLUS_INCLUDE_PATH=/usr/include/gdal
ENV C_INCLUDE_PATH=/usr/include/gdal

# Zainstaluj zależności Pythona
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Skopiuj pliki aplikacji do obrazu
COPY . /app
WORKDIR /app

# Otwórz port dla aplikacji Django
EXPOSE 8000

# Komenda uruchomienia serwera Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
