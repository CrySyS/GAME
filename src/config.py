from pathlib import Path
from datetime import datetime
import os

# NOTE: Adjust these paths as needed for your environment

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ARCH = "arm"
MALWARE_DIR = Path(f"/Users/jozsefsandor/datasets/ml-sample-pack-subset-1K/malware/{ARCH}")
BENIGN_DIR = Path(f"/Users/jozsefsandor/datasets/ml-sample-pack-extra-1K/benign/{ARCH}")


BASE_CONFIG = {
    "POPULATION_SIZE": 256,
    "NUM_GENERATIONS": 32,
    "ELITISM_COUNT": 3,
    "TOURNAMENT_SIZE": 3,
    "tournament_selection_p": 0.85,
    "FRESH_COUNT": 16,
    "MUTATION_CHANCES": 
    {
        "ratio_sampler": 0.3,
        "data_generator": 0.3
    },
    "FITNESS_WEIGHTS":
    {
        "tlsh_diff": 0.3,
        "size_increase": 0.6,
        "entropy_diff": 0.1
    },
    "ANOMALY_WEIGHTS":
    {
        "Appender": 0.8,
        "PaddingOverwriter": 0.9,
        "SegmentInjector": 1.0
    },
    "DETECTED_PENALTY": 0.1,  # Multiplier applied to fitness if the modified file is still detected as malware
    "REPETITION": 12
}

OUTPUT_DIR = PROJECT_ROOT / f"output-{ARCH}"
OUTPUT_DIR.mkdir(exist_ok=True)


# for logging in the same file in case of multiprocessing, we use a unique log file name based on timestamp or environment variable
LOG_RUN_ID_ENV = "GA_LOG_RUN_ID"
LOG_RUN_ID = os.environ.get(LOG_RUN_ID_ENV)
if not LOG_RUN_ID:
    LOG_RUN_ID = datetime.now().strftime("%Y%m%d-%H%M%S")
    os.environ[LOG_RUN_ID_ENV] = LOG_RUN_ID
    
LOG_DIR = OUTPUT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE_PATH = LOG_DIR / f"ga-{LOG_RUN_ID}.log"


LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(name)s | %(levelname)s | %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        # 'detailed': {
        #     'format': '%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s',
        #     'datefmt': '%Y-%m-%d %H:%M:%S'
        # }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        # 'file': {
        #     'class': 'logging.FileHandler',
        #     'level': 'DEBUG',
        #     'formatter': 'detailed',
        #     'filename': str(LOG_FILE_PATH),
        #     'mode': 'a'
        # }
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['console'] # Change to ['console', 'file'] to log to both console and file
        },
        'matplotlib': {
            'level': 'WARNING',
            'propagate': True
        },
        'matplotlib.font_manager': {
            'level': 'WARNING',
            'propagate': True
        }
    }
}