# completo (dados + produtos)
# 01_source/order_pickup_service/app/core/locker_seed.py
"""
Seed inicial completo: Lockers, Operadores, Categorias de Produtos e Configurações.

Explicação das adições
BAKED_GOODS: Para cookies e bolos mais estáveis (sem creme), permitidos em lockers normais.
CAKES_TARTS: Bolos e tortas doces com recheio/creme – precisam de refrigeração para evitar derretimento ou mofo.
EMPADAS_PIES: Empadas (salgadas ou doces) – semi-perecíveis, exigem frio.
FOOD_DRY e SNACKS: Genéricos para itens secos/embalados do seu negócio.
Mantive campos como requires_temp_control para lockers especiais (ex: "refrigerated" ou "none").

Medicamentos: restrição crítica: medicamentos, especialmente os que requerem refrigeração, não devem ser enviados por correio ou armazenados em lockers padrão

Itens Proibidos e de Alto risco:
Dinheiro em Espécie: Mesmo em pequenas quantias, não é recomendado. Lockers não são cofres bancários. 
Animais Vivos: Totalmente proibido por questões éticas e sanitárias. 
Documentos Roubados ou Falsificados: Proibidos por lei.

PHARMACY, dividida em novas categorias (ANVISA e INFARMED):
PHARMACY_PRESCRIPTION_MEDS (Medicamentos com Prescrição): Deve ser proibido em lockers padrão.  Esses itens são de alto risco, muitas vezes controlados, e podem exigir temperaturas específicas. A entrega deve ser feita com assinatura e verificação de identidade, geralmente em mãos.
PHARMACY_OTC_MEDS (Medicamentos sem Prescrição - Over-the-Counter): Pode ser permitido em lockers padrão, como analgésicos comuns, vitaminas e medicamentos para resfriado.  A exigência de ID pode ser opcional, dependendo do valor e do fornecedor. 
Anterior para Farmácia - {"category": "PHARMACY", "allowed": True, "requires_id": False},

"""

from sqlalchemy.orm import Session
from app.models.locker import Locker, LockerSlotConfig, LockerOperator
from app.models.product_locker_config import ProductLockerConfig, ProductCategory
from datetime import datetime, timezone


def seed_product_categories(db: Session):
    """Popula categorias mestre de produtos."""
    categories = [
        ProductCategory(
            id="ELECTRONICS",
            name="Eletrônicos",
            description="Smartphones, tablets, acessórios",
            default_temperature_zone="AMBIENT",
            default_security_level="ENHANCED",
            is_hazardous=False,
        ),
        ProductCategory(
            id="FOOD_PERISHABLE",
            name="Alimentos Perecíveis",
            description="Comida que requer refrigeração",
            default_temperature_zone="REFRIGERATED",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="FOOD_FROZEN",
            name="Alimentos Congelados",
            description="Comida que requer congelamento",
            default_temperature_zone="FROZEN",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="DOCUMENTS",
            name="Documentos",
            description="Papeladas, contratos, certificados",
            default_temperature_zone="AMBIENT",
            default_security_level="HIGH",
            is_hazardous=False,
        ),
        ProductCategory(
            id="FASHION",
            name="Moda e Vestuário",
            description="Roupas, calçados, acessórios",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
        ),
        ProductCategory(
            id="PHARMACY_OTC_MEDS",
            name="Farmácia sem prescrição médica",
            description="Medicamentos e produtos de saúde sem prescrição",
            default_temperature_zone="AMBIENT",
            default_security_level="STANDARD",
            is_hazardous=False,
            requires_age_verification=True,
        ),
        ProductCategory(
            id="PHARMACY_PRESCRIPTION_MEDS",
            name="Farmácia com prescrição médica",
            description="Medicamentos e produtos de saúde sem prescrição",
            default_temperature_zone="REFRIGERATED",
            default_security_level="HIGH",
            is_hazardous=False,
            requires_age_verification=True,
        ),
        ProductCategory(
            id="HAZARDOUS",
            name="Materiais Perigosos",
            description="Produtos químicos, inflamáveis",
            default_temperature_zone="AMBIENT",
            default_security_level="HIGH",
            is_hazardous=True,
        ),
        ProductCategory(
            id="HIGH_VALUE",
            name="Alto Valor",
            description="Joias, relógios, itens de luxo",
            default_temperature_zone="AMBIENT",
            default_security_level="HIGH",
            is_hazardous=False,
        ),
    ]
    
    for cat in categories:
        if not db.query(ProductCategory).filter(ProductCategory.id == cat.id).first():
            db.add(cat)
    
    db.commit()


def seed_operators(db: Session):
    """Popula operadores de lockers."""
    operators = [
        LockerOperator(
            id="OP-ELLAN-001",
            name="Ellan Lab Operações",
            document="00.000.000/0001-00",
            operator_type="LOGISTICS",
            active=True,
        ),
        LockerOperator(
            id="OP-LOGGI-001",
            name="Loggi Partner",
            document="11.111.111/0001-11",
            operator_type="LOGISTICS",
            active=True,
        ),
        LockerOperator(
            id="OP-SHOP-001",
            name="E-commerce Partner",
            document="22.222.222/0001-22",
            operator_type="ECOMMERCE",
            active=True,
        ),
        LockerOperator(
            id="OP-PHARMA-001",
            name="Drogaria Partner",
            document="33.333.333/0001-33",
            operator_type="ECOMMERCE",
            active=True,
        ),
        LockerOperator(
            id="OP-ATACADAO-001",
            name="Atacadão Partner",
            document="44.444.444/0001-44",
            operator_type="ECOMMERCE",
            active=True,
        ),
        LockerOperator(
            id="OP-WORTEN-001",
            name="Worten Partner",
            document="501.501.501",
            operator_type="ECOMMERCE",
            active=True,
        ),
        LockerOperator(
            id="OP-MOL-001",
            name="Marcos & Osineide Lda",
            document="518.474.828",
            operator_type="ECOMMERCE",
            active=True,
        ),
        LockerOperator(
            id="OP-LIDL-001",
            name="Lidl",
            document="502.502.502",
            operator_type="ECOMMERCE",
            active=True,
        ),
        LockerOperator(
            id="OP-SANTOBURACO-001",
            name="Comércio de Alimentos Lda",
            document="503.503.503",
            operator_type="ECOMMERCE",
            active=True,
        ),
        LockerOperator(
            id="OP-EGIRO-001",
            name="É Giro Pastelaria Artesanal Lda",
            document="504.504.504",
            operator_type="ECOMMERCE",
            active=True,
        ),
    ]
    
    for op in operators:
        if not db.query(LockerOperator).filter(LockerOperator.id == op.id).first():
            db.add(op)
    
    db.commit()


def seed_lockers(db: Session):
    """Popula lockers com configurações de produtos."""
    
    # Configurações padrão de produtos para lockers
    default_product_configs = [
        #ok Eletrônicos - permitido em lockers padrão
        {"category": "ELECTRONICS", "allowed": True, "max_value": 500000, "requires_id": True},
        
        #ok Documentos - permitido apenas em lockers de alta segurança
        {"category": "DOCUMENTS", "allowed": True, "requires_signature": True, "requires_id": True},
        
        #ok Moda - permitido universalmente
        {"category": "FASHION", "allowed": True},
        
        #ok Farmácia Nova Categoria - Medicamentos com Prescrição (PRESCRIPTION_MEDS)
        {"category": "PHARMACY_PRESCRIPTION_MEDS", "allowed": False, "requires_id": True, "requires_signature": True, "requires_temp_control": "refrigerated"},
        
        #ok Farmácia Nova Categoria - Medicamentos sem Prescrição (OTC_MEDS)
        {"category": "PHARMACY_OTC_MEDS", "allowed": True, "requires_id": False, "requires_temp_control": "none"},   

        #ok Alimentos perecíveis - apenas lockers refrigerados
        {"category": "FOOD_PERISHABLE", "allowed": False},  # Default: não permitido
        
        #ok Congelados - apenas lockers freezer
        {"category": "FOOD_FROZEN", "allowed": False},  # Default: não permitido
        
        #ok Alto valor - apenas lockers de alta segurança
        {"category": "HIGH_VALUE", "allowed": False},  # Default: não permitido
        
        #ok Perigosos - nunca permitido em lockers padrão
        {"category": "HAZARDOUS", "allowed": False},
        
        # Cookies, bolos secos - lockers padrão
        {"category": "BAKED_GOODS", "allowed": True, "max_value": 200, "requires_temp_control": "none"},  
        
        # Bolos/tortas doces cremosos - só refrigerados
        {"category": "CAKES_TARTS", "allowed": False, "requires_temp_control": "refrigerated"},  
        
        # Empadas salgadinhas - só refrigerados
        {"category": "EMPADAS_PIES", "allowed": False, "requires_temp_control": "refrigerated"},  
        
        # Biscoitos, pães, snacks secos - universal
        {"category": "FOOD_DRY", "allowed": True, "max_value": 150},  
        
        # Bebidas não alcoólicas
        {"category": "BEVERAGES", "allowed": True, "max_value": 100, "requires_temp_control": "none"},  
        
        # Petiscos prontos, como cookies embalados
        {"category": "SNACKS", "allowed": True},  
        
        # Medicamentos 
        {"category": "MEDICINES", "allowed": False},
        
        # Dinheiro em Espécie
        {"category": "MONEY", "allowed": False},
        
        # Animais Vivos
        {"category": "ANIMALS_ALIVE", "allowed": False},

    ]
    
    # ==================== LOCKERS - SÃO PAULO ====================
    lockers_sp = [
        {
            "id": "SP-OSASCO-CENTRO-LK-001",
            "display_name": "Osasco Centro - Locker 001",
            "region": "SP",
            "city": "Osasco",
            "state": "SP",
            "country": "BR",
            "timezone": "America/Sao_Paulo",
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "AMBIENT",
            "security_level": "STANDARD",
            "has_camera": True,
            "slots": [
                {"size": "P", "count": 8, "w": 10, "h": 10, "d": 40, "max_weight": 2},
                {"size": "M", "count": 8, "w": 20, "h": 20, "d": 40, "max_weight": 5},
                {"size": "G", "count": 6, "w": 30, "h": 40, "d": 40, "max_weight": 10},
                {"size": "XG", "count": 2, "w": 50, "h": 60, "d": 40, "max_weight": 20},
            ],
            "product_overrides": [
                {"category": "FOOD_PERISHABLE", "allowed": False},
            ]
        },
        {
            "id": "SP-CARAPICUIBA-JDMARILU-LK-001",
            "display_name": "Carapicuíba JD Marilu - Locker 001",
            "region": "SP",
            "city": "Carapicuíba",
            "state": "SP",
            "country": "BR",
            "timezone": "America/Sao_Paulo",
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "AMBIENT",
            "security_level": "STANDARD",
            "has_camera": False,
            "slots": [
                {"size": "P", "count": 10, "w": 10, "h": 10, "d": 40, "max_weight": 2},
                {"size": "M", "count": 10, "w": 20, "h": 20, "d": 40, "max_weight": 5},
                {"size": "G", "count": 4, "w": 30, "h": 40, "d": 40, "max_weight": 10},
            ],
            "product_overrides": [
                {"category": "BAKED_GOODS", "allowed": True, "max_value": 200, "requires_temp_control": "none"},  
                {"category": "FOOD_DRY", "allowed": True, "max_value": 150},  
                {"category": "SNACKS", "allowed": True},  
            ]
        },
        {
            "id": "SP-CARAPICUIBA-JDMARILU-LK-002",
            "display_name": "Carapicuíba JD Marilu - Locker 002",
            "region": "SP",
            "city": "Carapicuíba",
            "state": "SP",
            "country": "BR",
            "timezone": "America/Sao_Paulo",
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "AMBIENT",
            "security_level": "STANDARD",
            "has_camera": False,
            "slots": [
                {"size": "P", "count": 30, "w": 10, "h": 10, "d": 40, "max_weight": 2},
                {"size": "M", "count": 20, "w": 20, "h": 20, "d": 40, "max_weight": 5},
                {"size": "G", "count": 10, "w": 30, "h": 40, "d": 40, "max_weight": 10},
            ],
            "product_overrides": [ ]
        },
        {
            "id": "SP-ALPHAVILLE-SHOP-LK-001",
            "display_name": "Alphaville Shopping - Locker Premium",
            "region": "SP",
            "city": "Barueri",
            "state": "SP",
            "country": "BR",
            "timezone": "America/Sao_Paulo",
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "AMBIENT",
            "security_level": "HIGH",
            "has_camera": True,
            "has_alarm": True,
            "slots": [
                {"size": "P", "count": 10, "w": 10, "h": 10, "d": 40, "max_weight": 2},
                {"size": "M", "count": 10, "w": 20, "h": 20, "d": 40, "max_weight": 5},
                {"size": "G", "count": 8, "w": 30, "h": 40, "d": 40, "max_weight": 10},
                {"size": "XG", "count": 4, "w": 50, "h": 60, "d": 40, "max_weight": 20},
            ],
            "product_overrides": [
                {"category": "HIGH_VALUE", "allowed": True, "max_value": 2000000},
                {"category": "DOCUMENTS", "allowed": True, "requires_signature": True},
                {"category": "ELECTRONICS", "allowed": True, "max_value": 5000, "requires_id": True},
            ]
        },
        {
            "id": "SP-VILAOLIMPIA-FOOD-LK-001",
            "display_name": "Vila Olímpia - Locker Refrigerado",
            "region": "SP",
            "city": "São Paulo",
            "state": "SP",
            "country": "BR",
            "timezone": "America/Sao_Paulo",
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "REFRIGERATED",
            "security_level": "STANDARD",
            "has_camera": True,
            "slots": [
                {"size": "P", "count": 12, "w": 10, "h": 10, "d": 40, "max_weight": 3},
                {"size": "M", "count": 8, "w": 20, "h": 20, "d": 40, "max_weight": 5},
            ],
            "product_overrides": [
                {"category": "FOOD_PERISHABLE", "allowed": True, "temperature_zone": "REFRIGERATED"},
                {"category": "PHARMACY_OTC_MEDS", "allowed": True},
                {"category": "ELECTRONICS", "allowed": False},  # Não armazenar eletrônicos em refrigerado
                {"category": "CAKES_TARTS", "allowed": False, "requires_temp_control": "refrigerated"},  
                {"category": "BEVERAGES", "allowed": True, "max_value": 100, "requires_temp_control": "none"},  
            ]
        },
    ]

    # ==================== LOCKERS - PORTUGAL ====================
    lockers_pt = [
        {
            "id": "PT-MAIA-CENTRO-LK-001",
            "display_name": "Maia Centro - Locker 001",
            "region": "PT",
            "city": "Maia",
            "state": "Porto",
            "country": "PT",
            "timezone": "Europe/Lisbon",
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "AMBIENT",
            "security_level": "STANDARD",
            "has_camera": True,
            "slots": [
                {"size": "P", "count": 8, "w": 10, "h": 10, "d": 40, "max_weight": 2},
                {"size": "M", "count": 8, "w": 20, "h": 20, "d": 40, "max_weight": 5},
                {"size": "G", "count": 6, "w": 30, "h": 40, "d": 40, "max_weight": 10},
                {"size": "XG", "count": 2, "w": 50, "h": 60, "d": 40, "max_weight": 20},
            ],
            "product_overrides": []
        },
        {
            "id": "PT-GUIMARAES-AZUREM-LK-001",
            "display_name": "Guimarães Azurém - Locker 001",
            "region": "PT",
            "city": "Guimarães",
            "state": "Braga",
            "country": "PT",
            "timezone": "Europe/Lisbon",
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "REFRIGERATED",
            "security_level": "STANDARD",
            "has_camera": False,
            "slots": [
                {"size": "P", "count": 10, "w": 10, "h": 10, "d": 40, "max_weight": 2},
                {"size": "M", "count": 10, "w": 20, "h": 20, "d": 40, "max_weight": 5},
                {"size": "G", "count": 4, "w": 30, "h": 40, "d": 40, "max_weight": 10},
            ],
            "product_overrides": [
                {"category": "FOOD_PERISHABLE", "allowed": True, "temperature_zone": "REFRIGERATED"},
                {"category": "CAKES_TARTS", "allowed": False, "requires_temp_control": "refrigerated"},  
                {"category": "BEVERAGES", "allowed": True, "max_value": 100, "requires_temp_control": "none"},  
            ]
        },
        {
            "id": "PT-LISBOA-PHARMA-LK-001",
            "display_name": "Lisboa - Locker Farmácia",
            "region": "PT",
            "city": "Lisboa",
            "state": "Lisboa",
            "country": "PT",
            "timezone": "Europe/Lisbon",
            "operator_id": "OP-PHARMA-001",
            "temperature_zone": "AMBIENT",
            "security_level": "ENHANCED",
            "has_camera": True,
            "slots": [
                {"size": "P", "count": 15, "w": 10, "h": 10, "d": 40, "max_weight": 2},
                {"size": "M", "count": 5, "w": 20, "h": 20, "d": 40, "max_weight": 5},
            ],
            "product_overrides": [
                {"category": "PHARMACY_OTC_MEDS", "allowed": True, "requires_id": False},
                {"category": "ELECTRONICS", "allowed": False},
                {"category": "FASHION", "allowed": False},
            ]
        },
    ]

    # ==================== LOCKERS FUTUROS (ES / RJ) ====================
    lockers_future = [
        {
            "id": "ES-MADRID-CENTRO-LK-001",
            "display_name": "Madrid Centro - Locker 001",
            "region": "ES",
            "city": "Madrid",
            "country": "ES",
            "timezone": "Europe/Madrid",
            "active": False,
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "AMBIENT",
            "security_level": "STANDARD",
            "slots": [
                {"size": "P", "count": 8, "w": 10, "h": 10, "d": 40, "max_weight": 2},
                {"size": "M", "count": 8, "w": 20, "h": 20, "d": 40, "max_weight": 5},
                {"size": "G", "count": 6, "w": 30, "h": 40, "d": 40, "max_weight": 10},
            ],
            "product_overrides": []
        },
        {
            "id": "RJ-CAPITAL-CENTRO-LK-001",
            "display_name": "Rio Centro - Locker 001",
            "region": "RJ",
            "city": "Rio de Janeiro",
            "state": "RJ",
            "country": "BR",
            "timezone": "America/Sao_Paulo",
            "active": False,
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "AMBIENT",
            "security_level": "STANDARD",
            "slots": [
                {"size": "P", "count": 16, "w": 10, "h": 10, "d": 40, "max_weight": 2},
                {"size": "M", "count": 8, "w": 20, "h": 20, "d": 40, "max_weight": 5},
                {"size": "G", "count": 6, "w": 30, "h": 40, "d": 40, "max_weight": 10},
            ],
            "product_overrides": []
        },
        {
            "id": "PR-CAPITAL-SANTAFELICIDADE-LK-001",
            "display_name": "Curitiba Santa Felicidade - Locker 001",
            "region": "PR",
            "city": "Curitiba",
            "state": "PR",
            "country": "BR",
            "timezone": "America/Sao_Paulo",
            "active": False,
            "operator_id": "OP-ELLAN-001",
            "temperature_zone": "AMBIENT",
            "security_level": "STANDARD",
            "slots": [
                {"size": "P", "count": 10, "w": 10, "h": 10, "d": 40, "max_weight": 2},
                {"size": "M", "count": 10, "w": 20, "h": 20, "d": 40, "max_weight": 5},
                {"size": "G", "count": 10, "w": 30, "h": 40, "d": 40, "max_weight": 10},
            ],
            "product_overrides": []
        },
    ]

    all_lockers = lockers_sp + lockers_pt + lockers_future

    for locker_data in all_lockers:
        existing = db.query(Locker).filter(Locker.id == locker_data["id"]).first()
        if existing:
            continue

        slots_config = locker_data.pop("slots", [])
        product_overrides = locker_data.pop("product_overrides", [])
        
        locker = Locker(**locker_data, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        db.add(locker)
        db.flush()

        # Cria slot configs
        for slot in slots_config:
            slot_config = LockerSlotConfig(
                locker_id=locker.id,
                slot_size=slot["size"],
                slot_count=slot["count"],
                width_cm=slot.get("w"),
                height_cm=slot.get("h"),
                depth_cm=slot.get("d"),
                max_weight_kg=slot.get("max_weight"),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(slot_config)

        # Cria product configs (default + overrides)
        for default_config in default_product_configs:
            # Verifica se há override
            override = next((o for o in product_overrides if o["category"] == default_config["category"]), None)
            config = {**default_config, **(override or {})}
            
            product_config = ProductLockerConfig(
                locker_id=locker.id,
                category=config["category"],
                allowed=config["allowed"],
                temperature_zone=config.get("temperature_zone", "ANY"),
                max_value=config.get("max_value"),
                requires_signature=config.get("requires_signature", False),
                requires_id=config.get("requires_id", False),
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            db.add(product_config)

    db.commit()


def run_full_seed(db: Session):
    """Executa todo o seed na ordem correta."""
    seed_product_categories(db)
    seed_operators(db)
    seed_lockers(db)