from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
GENERATED_DIR = DATA_DIR / "generated"

CHECKPOINTS_DIR = PROJECT_ROOT / "checkpoints"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIGS_DIR = PROJECT_ROOT / "configs"

# Default configs (using new modular structure)
DEFAULT_MODEL_CONFIG = CONFIGS_DIR / "model.yaml"
DEFAULT_DATAGEN_FIM_CONFIG = CONFIGS_DIR / "datagen" / "fim.yaml"
DEFAULT_DATAGEN_L2R_CONFIG = CONFIGS_DIR / "datagen" / "l2r.yaml"

