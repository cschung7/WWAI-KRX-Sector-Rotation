#!/usr/bin/env python3
"""
Meta-Labeler Module

Implements de Prado's meta-labeling approach:
- Binary classifier that learns: "Given this signal, should I take the trade?"
- Uses purged K-fold cross-validation to avoid look-ahead bias
- Trains on historical backtest results
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pickle
import json
import warnings
warnings.filterwarnings('ignore')

try:
    import xgboost as xgb
    HAS_XGBOOST = True
except ImportError:
    HAS_XGBOOST = False
    print("Warning: XGBoost not available, will use Random Forest")

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("Warning: scikit-learn not available")

try:
    from .feature_engineering import FeatureEngineer
except ImportError:
    from feature_engineering import FeatureEngineer

class MetaLabeler:
    """Meta-labeler for filtering trading signals"""
    
    def __init__(self, model_type: str = 'xgboost', model_params: Optional[Dict] = None):
        """
        Args:
            model_type: 'xgboost' or 'random_forest'
            model_params: Model hyperparameters
        """
        self.model_type = model_type
        self.model = None
        self.feature_engineer = FeatureEngineer()
        self.feature_names = None
        self.model_params = model_params or {}
        
        # Default parameters
        if model_type == 'xgboost' and HAS_XGBOOST:
            self.default_params = {
                'objective': 'binary:logistic',
                'eval_metric': 'auc',
                'max_depth': 6,
                'learning_rate': 0.1,
                'n_estimators': 100,
                'subsample': 0.8,
                'colsample_bytree': 0.8,
                'random_state': 42,
                'scale_pos_weight': 1.0  # Will be adjusted based on class imbalance
            }
        elif model_type == 'random_forest' and HAS_SKLEARN:
            self.default_params = {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 20,
                'min_samples_leaf': 10,
                'random_state': 42,
                'class_weight': 'balanced'
            }
        else:
            raise ValueError(f"Model type '{model_type}' not available. Install xgboost or scikit-learn.")
        
        # Merge with user params
        self.default_params.update(self.model_params)
    
    def _purged_k_fold(self, dates: pd.Series, n_splits: int = 5, 
                       purge_days: int = 5, embargo_days: int = 5) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Purged K-fold cross-validation to avoid look-ahead bias
        
        Args:
            dates: Series of dates for each sample
            n_splits: Number of folds
            purge_days: Days to purge between train and test (avoid overlap)
            embargo_days: Days to embargo after test (avoid leakage)
            
        Returns:
            List of (train_indices, test_indices) tuples
        """
        if not HAS_SKLEARN:
            # Simple time-based split if sklearn not available
            dates_sorted = dates.sort_values()
            n = len(dates_sorted)
            splits = []
            for i in range(n_splits):
                test_start = int(n * i / n_splits)
                test_end = int(n * (i + 1) / n_splits)
                train_end = max(0, test_start - purge_days)
                train_start = 0
                test_indices = dates_sorted.iloc[test_start:test_end].index.values
                train_indices = dates_sorted.iloc[train_start:train_end].index.values
                splits.append((train_indices, test_indices))
            return splits
        
        # Use TimeSeriesSplit as base
        tscv = TimeSeriesSplit(n_splits=n_splits)
        dates_sorted = dates.sort_values()
        date_indices = dates_sorted.index.values
        
        splits = []
        for train_idx, test_idx in tscv.split(date_indices):
            # Get actual dates
            train_dates = dates_sorted.iloc[train_idx]
            test_dates = dates_sorted.iloc[test_idx]
            
            # Purge: remove train samples too close to test
            if len(test_dates) > 0:
                test_start = test_dates.min()
                purge_end = test_start - timedelta(days=purge_days)
                train_indices = train_dates[train_dates <= purge_end].index.values
            else:
                train_indices = train_dates.index.values
            
            # Embargo: remove test samples too close to next train
            if len(train_indices) > 0 and len(test_dates) > 0:
                test_end = test_dates.max()
                embargo_start = test_end + timedelta(days=embargo_days)
                # This would affect next fold, handled in next iteration
            
            splits.append((train_indices, test_dates.index.values))
        
        return splits
    
    def prepare_features(self, signals_df: pd.DataFrame, theme_mapping: Dict[str, List[str]],
                        db_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        Extract features for all signals
        
        Args:
            signals_df: DataFrame with columns [theme, date, signal_type, signal_strength, ...]
            theme_mapping: Dict mapping theme names to ticker lists
            db_df: Database DataFrame (optional)
            
        Returns:
            DataFrame with features
        """
        print("Extracting features for meta-labeling...")
        features_list = []
        
        for idx, row in signals_df.iterrows():
            theme = row['theme']
            signal_date = pd.to_datetime(row['date'])
            signal_dict = row.to_dict()
            
            # Get theme tickers
            theme_tickers = theme_mapping.get(theme, [])
            
            # Extract all features
            try:
                all_features = self.feature_engineer.extract_all_features(
                    signal_dict,
                    theme,
                    theme_tickers,
                    signal_date,
                    db_df=db_df
                )
                all_features['signal_idx'] = idx
                features_list.append(all_features)
            except Exception as e:
                print(f"  Warning: Failed to extract features for {theme} on {signal_date}: {e}")
                continue
        
        if len(features_list) == 0:
            raise ValueError("No features extracted!")
        
        features_df = pd.DataFrame(features_list)
        features_df = features_df.set_index('signal_idx')
        
        # Store feature names
        self.feature_names = [c for c in features_df.columns if c not in ['signal_idx']]
        
        print(f"  Extracted {len(features_df)} samples with {len(self.feature_names)} features")
        return features_df
    
    def train(self, features_df: pd.DataFrame, labels: pd.Series, 
              dates: Optional[pd.Series] = None, use_cv: bool = True) -> Dict:
        """
        Train the meta-labeler
        
        Args:
            features_df: DataFrame with features
            labels: Series with binary labels (1 = take trade, 0 = skip)
            dates: Series with dates for each sample (for purged K-fold)
            use_cv: Whether to use cross-validation
            
        Returns:
            dict: Training metrics
        """
        print(f"\nTraining meta-labeler ({self.model_type})...")
        print(f"  Samples: {len(features_df)}, Features: {len(features_df.columns)}")
        print(f"  Positive labels: {labels.sum()} ({labels.mean()*100:.1f}%)")
        
        # Handle missing values
        features_df = features_df.fillna(0)
        
        # Prepare data
        X = features_df.values
        y = labels.values
        
        metrics = {}
        
        if use_cv and dates is not None and HAS_SKLEARN:
            # Use purged K-fold cross-validation
            print("  Using purged K-fold cross-validation...")
            splits = self._purged_k_fold(dates, n_splits=5)
            
            cv_scores = []
            for fold, (train_idx, test_idx) in enumerate(splits):
                if len(train_idx) == 0 or len(test_idx) == 0:
                    continue
                
                X_train, X_test = X[train_idx], X[test_idx]
                y_train, y_test = y[train_idx], y[test_idx]
                
                # Train model
                model = self._create_model()
                model.fit(X_train, y_train)
                
                # Evaluate
                y_pred = model.predict(X_test)
                y_pred_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else y_pred
                
                # Calculate metrics
                accuracy = (y_pred == y_test).mean()
                precision = (y_pred[y_test == 1] == 1).mean() if (y_test == 1).sum() > 0 else 0
                recall = (y_pred[y_test == 1] == 1).mean() if (y_test == 1).sum() > 0 else 0
                auc = roc_auc_score(y_test, y_pred_proba) if len(np.unique(y_test)) > 1 else 0
                
                cv_scores.append({
                    'accuracy': accuracy,
                    'precision': precision,
                    'recall': recall,
                    'auc': auc
                })
                
                print(f"    Fold {fold+1}: Accuracy={accuracy:.3f}, Precision={precision:.3f}, "
                      f"Recall={recall:.3f}, AUC={auc:.3f}")
            
            # Average metrics
            metrics['cv_accuracy'] = np.mean([s['accuracy'] for s in cv_scores])
            metrics['cv_precision'] = np.mean([s['precision'] for s in cv_scores])
            metrics['cv_recall'] = np.mean([s['recall'] for s in cv_scores])
            metrics['cv_auc'] = np.mean([s['auc'] for s in cv_scores])
            
            print(f"\n  CV Average: Accuracy={metrics['cv_accuracy']:.3f}, "
                  f"Precision={metrics['cv_precision']:.3f}, "
                  f"Recall={metrics['cv_recall']:.3f}, AUC={metrics['cv_auc']:.3f}")
        
        # Train final model on all data
        print("\n  Training final model on all data...")
        self.model = self._create_model()
        
        # Adjust class weight if needed
        if self.model_type == 'xgboost' and HAS_XGBOOST:
            pos_weight = (y == 0).sum() / (y == 1).sum() if (y == 1).sum() > 0 else 1.0
            self.default_params['scale_pos_weight'] = pos_weight
        
        self.model.fit(X, y)
        
        # Final predictions
        y_pred = self.model.predict(X)
        y_pred_proba = self.model.predict_proba(X)[:, 1] if hasattr(self.model, 'predict_proba') else y_pred
        
        # Calculate final metrics
        metrics['train_accuracy'] = (y_pred == y).mean()
        metrics['train_precision'] = (y_pred[y == 1] == 1).mean() if (y == 1).sum() > 0 else 0
        metrics['train_recall'] = (y_pred[y == 1] == 1).mean() if (y == 1).sum() > 0 else 0
        metrics['train_auc'] = roc_auc_score(y, y_pred_proba) if len(np.unique(y)) > 1 else 0
        
        print(f"  Final Model: Accuracy={metrics['train_accuracy']:.3f}, "
              f"Precision={metrics['train_precision']:.3f}, "
              f"Recall={metrics['train_recall']:.3f}, AUC={metrics['train_auc']:.3f}")
        
        return metrics
    
    def _create_model(self):
        """Create model instance"""
        if self.model_type == 'xgboost' and HAS_XGBOOST:
            return xgb.XGBClassifier(**self.default_params)
        elif self.model_type == 'random_forest' and HAS_SKLEARN:
            return RandomForestClassifier(**self.default_params)
        else:
            raise ValueError(f"Model type '{self.model_type}' not available")
    
    def predict(self, features_df: pd.DataFrame) -> np.ndarray:
        """
        Predict whether to take trades
        
        Args:
            features_df: DataFrame with features
            
        Returns:
            Array of binary predictions (1 = take, 0 = skip)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Handle missing values
        features_df = features_df.fillna(0)
        
        # Ensure same feature order
        if self.feature_names:
            missing_features = set(self.feature_names) - set(features_df.columns)
            if missing_features:
                for feat in missing_features:
                    features_df[feat] = 0
            features_df = features_df[self.feature_names]
        
        X = features_df.values
        return self.model.predict(X)
    
    def predict_proba(self, features_df: pd.DataFrame) -> np.ndarray:
        """
        Predict probabilities
        
        Args:
            features_df: DataFrame with features
            
        Returns:
            Array of probabilities [P(skip), P(take)]
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        # Handle missing values
        features_df = features_df.fillna(0)
        
        # Ensure same feature order
        if self.feature_names:
            missing_features = set(self.feature_names) - set(features_df.columns)
            if missing_features:
                for feat in missing_features:
                    features_df[feat] = 0
            features_df = features_df[self.feature_names]
        
        X = features_df.values
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X)
        else:
            # Fallback: use decision function
            pred = self.model.predict(X)
            proba = np.zeros((len(pred), 2))
            proba[pred == 1, 1] = 1.0
            proba[pred == 0, 0] = 1.0
            return proba
    
    def save(self, filepath: Path):
        """Save trained model"""
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Save model
        model_file = filepath.with_suffix('.pkl')
        with open(model_file, 'wb') as f:
            pickle.dump(self.model, f)
        
        # Save metadata
        metadata = {
            'model_type': self.model_type,
            'model_params': self.default_params,
            'feature_names': self.feature_names,
            'n_features': len(self.feature_names) if self.feature_names else 0
        }
        metadata_file = filepath.with_suffix('.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Model saved to {model_file}")
        print(f"Metadata saved to {metadata_file}")
    
    def load(self, filepath: Path):
        """Load trained model"""
        filepath = Path(filepath)
        
        # Load model
        model_file = filepath.with_suffix('.pkl')
        with open(model_file, 'rb') as f:
            self.model = pickle.load(f)
        
        # Load metadata
        metadata_file = filepath.with_suffix('.json')
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        self.model_type = metadata['model_type']
        self.default_params = metadata['model_params']
        self.feature_names = metadata['feature_names']
        
        print(f"Model loaded from {model_file}")
        print(f"  Model type: {self.model_type}")
        if self.feature_names:
            print(f"  Features: {len(self.feature_names)}")
        else:
            print(f"  Features: Not specified")

