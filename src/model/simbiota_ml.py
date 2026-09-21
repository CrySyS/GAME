import numpy as np
import tlsh
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, RobustScaler, MinMaxScaler, MaxAbsScaler
from sklearn.base import BaseEstimator,TransformerMixin
from sklearn.pipeline import Pipeline
from config import ARCH

import logging
logger = logging.getLogger(__name__)


BEST_SCALERS = {
    'arm': {
        'LR': RobustScaler(),
        'SVM': StandardScaler(),
        'RF': MinMaxScaler(),
        'AB': RobustScaler(),
        'GB': MaxAbsScaler()
    },
    'mips': {
        'LR': RobustScaler(),
        'SVM': StandardScaler(),
        'RF': StandardScaler(),
        'AB': MaxAbsScaler(),
        'GB': MaxAbsScaler()
    }
}

MODEL_TYPES = {
    'LR': LogisticRegression,
    'SVM': SVC,
    'RF': RandomForestClassifier,
    'AB': AdaBoostClassifier,
    'GB': GradientBoostingClassifier
}


BEST_HYPERPARAMETERS = {
    'arm': {
        'LR': {
            'C': 10,
            'penalty': "elasticnet",
            'solver': "saga",
            'l1_ratio': 0.5
        },
        'SVM': {
            'C': 1.0,
            'kernel': 'poly',
            'degree': 3,
            'gamma': 100
        },
        'RF': {
            'n_estimators': 60,
            'criterion': 'gini',
            'max_depth': 25
        },
        'AB': {
            'n_estimators': 90,
            'learning_rate': 1.0
        },
        'GB': {
            'n_estimators': 100,
            'learning_rate': 1.0,
            'subsample': 0.9
        }
    },
    'mips': {
        'LR': {
            'C': 10,
            'penalty': "elasticnet",
            'solver': "saga",
            'l1_ratio': 0.5
        },
        'SVM': {
            'C': 0.001,
            'kernel': 'poly',
            'degree': 5,
            'gamma': 1
        },
        'RF': {
            'n_estimators': 50,
            'criterion': 'entropy',
            'max_depth': 25
        },
        'AB': {
            'n_estimators': 100,
            'learning_rate': 1.0
        },
        'GB': {
            'n_estimators': 100,
            'learning_rate': 1.0,
            'subsample': 0.9
        }
    }
}

class TLSHFeatureTransformer(BaseEstimator,TransformerMixin):
    def __init__(self):
        pass

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        feature_vectors = []
        for tlsh_hash in X:
            h1 = tlsh.Tlsh()
            h1.fromTlshStr(tlsh_hash)
            features = [h1.lvalue, h1.q1ratio, h1.q2ratio]
            for bi in range(0,128):
                features.append(h1.bucket_value(bi))
            feature_vectors.append(features)
        return np.array(feature_vectors)
    

class SimbiotaML():
    
    def __init__(self, model_type='LR'):
        """model_type:  'LR' for Logistic Regression,
                        'SVM' for Support Vector Machine,
                        'RF' for Random Forest,
                        'AB' for AdaBoost,
                        'GB' for Gradient Boosting
        """
        
        self.model = Pipeline([
            ('feature_transformer', TLSHFeatureTransformer()),
            ('scaler', BEST_SCALERS[ARCH][model_type]),
            ('classifier', MODEL_TYPES[model_type](**BEST_HYPERPARAMETERS[ARCH][model_type]))
        ])
        self.model_type = model_type

        
    def fit(self, X, y):
        self.model.fit(X, y)
        logger.debug("Fitted SimbiotaML model on provided data.")
        
        
    def predict(self, X):
        predictions = self.model.predict(X)
        logger.debug("Predicted using SimbiotaML model.")
        return predictions
    
    
    def to_dict(self) -> dict:
        return {
            "detector_type": "SimbiotaML",
            "model_type": self.model.named_steps['classifier'].__class__.__name__,
            "scaler": self.model.named_steps['scaler'].__class__.__name__,
            "feature_transformer": self.model.named_steps['feature_transformer'].__class__.__name__
        }
        
        
    def __str__(self):
        return f"Simbiota_ML_{self.model_type}"
    

if __name__ == "__main__":
    from config import DATA_DIR, ARCH, MALWARE_DIR, BENIGN_DIR
    import pandas as pd
    from sklearn.metrics import confusion_matrix
    
    for model_type in ["LR", "RF"]:
        detector = SimbiotaML(model_type)
        data_file = pd.read_csv(DATA_DIR / f"{ARCH}_medium_tlsh.csv")
        X = data_file["tlsh"].values.tolist()
        y = data_file["label"]
        detector.fit(X, y)
        
        mw_hashes = [tlsh.hash(open(file_path, 'rb').read()) for file_path in MALWARE_DIR.iterdir()]
        bn_hashes = [tlsh.hash(open(file_path, 'rb').read()) for file_path in BENIGN_DIR.iterdir()]
        predictions = detector.predict(mw_hashes + bn_hashes)
        true_labels = [1] * len(mw_hashes) + [0] * len(bn_hashes)
        cm = confusion_matrix(true_labels, predictions)
        tn, fp, fn, tp = cm.ravel().tolist()
        print(f"{model_type}: True Negatives: {tn}, False Positives: {fp}, False Negatives: {fn}, True Positives: {tp}")
        