# Garante engine SQLite para coleta/execução de testes sem Postgres local.
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
