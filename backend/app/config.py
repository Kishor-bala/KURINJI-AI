import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"

# Audio and Database storage
AUDIO_DIR = DATA_DIR / "audio"
RAW_AUDIO_DIR = AUDIO_DIR / "raw"
CLIPS_AUDIO_DIR = AUDIO_DIR / "clips"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
DATABASE_PATH = DATA_DIR / "vocabulary.db"

# Original dataset location inside project
DATASET_DIR = PROJECT_ROOT / "dataset"
DATASET_LOG_FILE = DATASET_DIR / "Mother Tongue Recordings Log.xlsx"
DATASET_BADAGA_DIR = DATASET_DIR / "Badaga-20261030T094159Z-1-001" / "Badaga"
DATASET_MARWARI_DIR = DATASET_DIR / "Marwari-20261030T094201Z-1-001" / "Marwari"

# Audio specifications
TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1  # Mono
TARGET_SAMPLE_WIDTH = 2  # 16-bit PCM (bytes per sample)
MIN_AUDIO_DURATION = 0.3  # seconds
MAX_AUDIO_DURATION = 15.0  # seconds
SILENCE_TOP_DB = 30  # dB threshold for silence detection

# Encoder & Matching specifications
ENCODER_MODEL_NAME = "facebook/wav2vec2-xls-r-300m"
ENCODER_REPRESENTATION_DIM = 1024
DEFAULT_POOLING_METHOD = "mean"

# Acceptance & Rejection calibration
DEFAULT_SIMILARITY_THRESHOLD = 0.55  # Minimum cosine similarity for acceptance (cross-speaker calibrated)
DEFAULT_MARGIN_THRESHOLD = 0.005  # Minimum difference between top-1 and top-2 candidate (calibrated for 495 closed vocabulary)
RECOGNITION_AGGREGATION_METHOD = "max"  # Options: 'max', 'average', 'top3_average'
USE_EMBEDDING_CENTERING = True  # Eliminates Transformer anisotropy for calibrated discrimination

# Ensure required runtime directories exist
for directory in [DATA_DIR, AUDIO_DIR, RAW_AUDIO_DIR, CLIPS_AUDIO_DIR, EMBEDDINGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
