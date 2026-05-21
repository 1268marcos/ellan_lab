FROM postgis/postgis:15-3.4

# Instala TimescaleDB + pg_cron
RUN apt-get update && \
    apt-get install -y gnupg curl && \
    curl -s https://packagecloud.io/install/repositories/timescale/timescaledb/script.deb.sh | bash && \
    apt-get update && \
    apt-get install -y \
        timescaledb-2-postgresql-15 \
        postgresql-15-cron && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Cria diretório de configuração
RUN mkdir -p /etc/postgresql/15/main/

# Configura via SQL (mais seguro que modificar postgresql.conf)
RUN echo "ALTER SYSTEM SET shared_preload_libraries = 'timescaledb,pg_cron';" > /docker-entrypoint-initdb.d/00-config.sql && \
    echo "ALTER SYSTEM SET cron.database_name = 'locker_central';" >> /docker-entrypoint-initdb.d/00-config.sql



# FROM postgis/postgis:15-3.4
# 
# Instalar TimescaleDB e pg_cron
# RUN apt-get update && \
#     apt-get install -y wget gnupg curl && \
#     echo "deb https://packagecloud.io/timescale/timescaledb/debian/ $(lsb_release -c -s) main" | tee /etc/apt/sources.list.d/timescaledb.list && \
#     wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | apt-key add - && \
#     apt-get update && \
#     apt-get install -y timescaledb-2-postgresql-15 postgresql-15-cron && \
#     apt-get clean && rm -rf /var/lib/apt/lists/*
# 
# Configurações serão feitas via SQL init script, não no Dockerfile