from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://admin:admin@localhost:5432/ellan"
    model_artifact_path: str = "./artifacts/rf_failure.joblib"
    enable_train_scheduler: bool = False  # ENABLE_TRAIN_SCHEDULER=true
    scheduler_hour: int = 2
    scheduler_timezone: str = "America/Sao_Paulo"
    enable_batch_predict_scheduler: bool = False  # ENABLE_BATCH_PREDICT_SCHEDULER=true
    batch_predict_hour: int = 2
    batch_predict_minute: int = 30
    predict_commit_batch_size: int = 100
    ml_model_dir: str | None = None  # ML_MODEL_DIR env overrides via model_dir param
    churn_model_path: str = "./artifacts/churn_model.pkl"
    pricing_bandit_state_path: str = "./artifacts/pricing_bandit_state.pkl"
    lstm_occupancy_model_path: str = "./artifacts/lstm_occupancy.keras"
    lstm_occupancy_scalers_path: str = "./artifacts/lstm_occupancy_scalers.joblib"
    lstm_occupancy_meta_path: str = "./artifacts/lstm_occupancy.meta.json"
    fraud_model_dir: str = "./artifacts/fraud"
    fraud_model_bundle_path: str = "./artifacts/fraud/fraud_bundle.joblib"
    fraud_model_meta_path: str = "./artifacts/fraud/fraud_bundle.meta.json"
    routing_travel_rf_path: str = "./artifacts/routing_travel_rf.joblib"
    ltv_model_dir: str | None = None  # LTV_MODEL_DIR; default artifacts via ml_model_dir
    # NLP feedback (SentenceTransformers multilingue; desligar com FEEDBACK_USE_TFIDF_ONLY=true)
    feedback_embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    feedback_use_tfidf_only: bool = False  # FEEDBACK_USE_TFIDF_ONLY


settings = Settings()
