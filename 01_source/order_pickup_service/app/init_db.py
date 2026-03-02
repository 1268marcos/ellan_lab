# init_db.py
import os
import sqlalchemy as sa
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, Float, Boolean
import datetime

def init_database():
    """Cria as tabelas necessárias se não existirem"""
    
    # Pega a URL do banco das variáveis de ambiente
    database_url = os.getenv('DATABASE_URL', 'sqlite:////data/sqlite/order_pickup/orders.db')
    
    # Para SQLite, precisamos garantir que o diretório existe
    if database_url.startswith('sqlite'):
        db_path = database_url.replace('sqlite:///', '')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    engine = create_engine(database_url)
    
    # Define as tabelas
    metadata = MetaData()
    
    orders = Table(
        'orders', metadata,
        Column('id', String(50), primary_key=True),
        Column('user_id', String(50), nullable=True),
        Column('channel', String(20), nullable=False),
        Column('region', String(10), nullable=False),
        Column('totem_id', String(50), nullable=False),
        Column('sku_id', String(50), nullable=False),
        Column('amount_cents', Integer, nullable=False),
        Column('status', String(50), nullable=False),
        Column('gateway_transaction_id', String(100), nullable=True),
        Column('paid_at', DateTime, nullable=True),
        Column('pickup_deadline_at', DateTime, nullable=True),
        Column('guest_session_id', String(100), nullable=True),
        Column('receipt_email', String(255), nullable=True),
        Column('receipt_phone', String(50), nullable=True),
        Column('consent_marketing', Boolean, default=False),
        Column('guest_phone', String(50), nullable=True),
        Column('guest_email', String(255), nullable=True),
        Column('created_at', DateTime, default=datetime.datetime.utcnow),
    )
    
    # Cria as tabelas
    metadata.create_all(engine)
    print(f"Tabelas criadas/verificadas em {database_url}")
    
    return engine

if __name__ == "__main__":
    init_database()