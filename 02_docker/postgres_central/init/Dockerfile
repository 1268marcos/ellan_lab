# Dockerfile.postgis
FROM postgres:15

# Instalar PostGIS
RUN apt-get update && \
    apt-get install -y postgresql-15-postgis-3 postgresql-15-postgis-3-scripts && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Criar extensões automaticamente no banco inicial
COPY init-postgis.sh /docker-entrypoint-initdb.d/