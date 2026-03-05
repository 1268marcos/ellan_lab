import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////data/sqlite/order_pickup/orders.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Cria todas as tabelas definidas nos models.
    IMPORTANTE: precisa importar os models antes do create_all,
    para que eles sejam registrados no Base.metadata.
    """
    # imports “side-effect” (registram tabelas)
    from app.models import order  # noqa: F401
    from app.models import allocation  # noqa: F401
    from app.models import pickup_token  # noqa: F401
    
    # acrescimo do MARCOS ao ver a pasta models
    from app.models import credit  # noqa: F401
    from app.models import kiosk_antifraud_event  # noqa: F401
    from app.models import login_otp  # noqa: F401
    from app.models import user  # noqa: F401

    Base.metadata.create_all(bind=engine)