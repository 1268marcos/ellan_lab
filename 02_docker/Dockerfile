FROM postgis/postgis:15-3.4

# Instala TimescaleDB no mesmo SO (Debian Bookworm)
RUN apt-get update && \
    apt-get install -y gnupg curl && \
    curl -s https://packagecloud.io/install/repositories/timescale/timescaledb/script.deb.sh | bash && \
    apt-get update && \
    apt-get install -y timescaledb-2-postgresql-15 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*
    