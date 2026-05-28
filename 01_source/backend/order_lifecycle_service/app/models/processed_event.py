# 01_source/backend/order_lifecycle/app/models/processed_event.py
# criado em local errado?????
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base
"""
Análise das opções:

**Resumo do problema:**
- O modelo `ProcessedEvent` está no serviço `order_lifecycle_service`, mas referencia e persiste dados na tabela `"billing_processed_events"` do domínio de billing.
- Se a tabela (e esquema) não existir neste serviço, pode causar erros do tipo "Table not found".
- Há confusão de boundaries de domínio (padrão Strangler Fig + Ownership).

-------------------
# Opção 1 — Mover para billing_service (**RECOMENDADA, mais segura**)

## Passos para mover corretamente:

1. **Copiar o modelo ProcessedEvent para `billing_fiscal_service/app/models/processed_event.py`.**
2. **Registrar o modelo no `app/models/__init__.py` do billing_service:**  
   Adicione:  
   ```python
   from .processed_event import ProcessedEvent
   ```
3. **Atualizar qualquer código/integrador que consuma ou grava nessa tabela para importar de `billing_service` em vez de `order_lifecycle_service`.**
4. **Criar (ou garantir) a migração Alembic de criação da tabela em `billing_fiscal_service`.**  
   Exemplo (arquivo de migração Alembic em `billing_fiscal_service`):
   ```python
   from alembic import op
   import sqlalchemy as sa

   revision = 'add_billing_processed_events'
   down_revision = None  # Atualizar para o último revision id

   def upgrade():
       op.create_table(
           'billing_processed_events',
           sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
           sa.Column('event_key', sa.String(length=200), nullable=False),
           sa.Column('order_id', sa.String(length=100), nullable=False),
           sa.Column('status', sa.String(length=50), nullable=False),
           sa.Column('error_message', sa.String(length=500), nullable=True),
           sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
           sa.UniqueConstraint('event_key', name='uq_billing_processed_event_key'),
       )
       op.create_index('ix_billing_processed_events_order_id', 'billing_processed_events', ['order_id'])

   def downgrade():
       op.drop_index('ix_billing_processed_events_order_id', table_name='billing_processed_events')
       op.drop_table('billing_processed_events')
   ```
5. **Remover o modelo deste serviço (lifecycle) para evitar uso cruzado.**

-------------------
# Opção 2 — Criar a tabela no lifecycle (NÃO recomendado para arquitetura, mas tecnicamente possível)

Crie uma migração Alembic em `order_lifecycle_service` com:

```python
from alembic import op
import sqlalchemy as sa

revision = 'add_billing_processed_events'
down_revision = None  # Atualizar conforme o último revision id

def upgrade():
    op.create_table(
        'billing_processed_events',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('event_key', sa.String(length=200), nullable=False),
        sa.Column('order_id', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('event_key', name='uq_billing_processed_event_key'),
    )
    op.create_index('ix_billing_processed_events_order_id', 'billing_processed_events', ['order_id'])

def downgrade():
    op.drop_index('ix_billing_processed_events_order_id', table_name='billing_processed_events')
    op.drop_table('billing_processed_events')
```

-------------------
# Qual opção é mais segura?

**A Opção 1 (mover para billing_service) é mais segura.**  
Ela preserva o ownership correto do domínio e evita inconsistências e acoplamentos indevidos entre domínios do monorepo, em especial considerando o padrão Strangler Fig/DDD.  
Nunca o serviço de order/lifecycle deveria ser responsável por persistir tabelas do domínio de billing.

-------------------
# Resumidamente:

- **Movimente o modelo `ProcessedEvent` para `billing_fiscal_service`**
- **Adicione o modelo ao `__init__.py` do billing**
- **Crie a migração de tabela em billing, se necessário**
- **Remova o modelo deste serviço para garantir boundary correto**

-------------------

# Exemplo de registro no `billing_fiscal_service/app/models/__init__.py`:

```python
from .processed_event import ProcessedEvent
```


class ProcessedEvent(Base):
    __tablename__ = "billing_processed_events"

    __table_args__ = (
        UniqueConstraint("event_key", name="uq_billing_processed_event_key"),
        Index("ix_billing_processed_events_order_id", "order_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_key: Mapped[str] = mapped_column(String(200), nullable=False)
    order_id: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)  # PROCESSED | FAILED | DEAD
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
