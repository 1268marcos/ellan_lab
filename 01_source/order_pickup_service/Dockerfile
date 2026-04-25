FROM python:3.11-slim

WORKDIR /app

# Instalar dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY app app  
COPY stress stress
COPY tests tests
# COPY app ./app

# 🔥 CRIAR USUÁRIO NÃO-ROOT COM UID FIXO
RUN addgroup --gid 1000 appuser && \
    adduser --uid 1000 --gid 1000 --disabled-password --gecos "" appuser

# 🔥 CRIAR DIRETÓRIO DO BANCO E DAR PERMISSÃO
RUN mkdir -p /data/sqlite/order_pickup && \
    chown -R appuser:appuser /data && \
    chmod 755 /data/sqlite /data/sqlite/order_pickup

# 🔥 EXECUTAR SCRIPT DE INICIALIZAÇÃO DO BANCO
# RUN python app/init_db.py    EXCLUIR O ARQUIVO DEPOIS

# Mudar para usuário não-root
USER appuser

# 🔥 CRIAR ARQUIVO DO BANCO VAZIO (opcional, mas ajuda)
RUN touch /data/sqlite/order_pickup/orders.db && \
    chmod 664 /data/sqlite/order_pickup/orders.db

# Comando para rodar a aplicação
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
