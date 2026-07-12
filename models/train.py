import os
import json
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, auc, f1_score, 
    confusion_matrix, brier_score_loss, accuracy_score, classification_report
)
from sklearn.calibration import calibration_curve

import xgboost as xgb
import lightgbm as lgb
import shap

import sys
OS_WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(OS_WORKSPACE_DIR, 'models')
if MODELS_DIR not in sys.path:
    sys.path.append(MODELS_DIR)

# Import the shared feature extractor
from features import extract_business_features

# Set directories
OS_WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(OS_WORKSPACE_DIR, 'data')
MODELS_DIR = os.path.join(OS_WORKSPACE_DIR, 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

def train_and_evaluate():
    print("Loading data...")
    df_biz = pd.read_csv(os.path.join(DATA_DIR, 'raw_businesses.csv'))
    df_upi = pd.read_csv(os.path.join(DATA_DIR, 'upi_transactions.csv'))
    df_social = pd.read_csv(os.path.join(DATA_DIR, 'social_media.csv'))
    df_footfall = pd.read_csv(os.path.join(DATA_DIR, 'footfall.csv'))
    df_reviews = pd.read_csv(os.path.join(DATA_DIR, 'reviews.csv'))

    # Stratified Train/Test split on the businesses first (80-20 split)
    print("Splitting train and test sets...")
    df_train_biz, df_test_biz = train_test_split(
        df_biz, 
        test_size=0.20, 
        random_state=42, 
        stratify=df_biz['business_health_12mo']
    )

    # Extract features for train split (fit TF-IDF)
    print("Engineering training features...")
    X_train_full, tfidf_vec = extract_business_features(
        df_train_biz, df_upi, df_social, df_footfall, df_reviews, 
        tfidf_vectorizer=None, fit_tfidf=True
    )
    y_train = X_train_full['business_health_12mo'].values
    # Save train business ids and remove target and identifiers from feature matrix
    train_ids = X_train_full['business_id'].values
    X_train = X_train_full.drop(columns=['business_id', 'business_name', 'owner_name', 'business_health_12mo'])

    # Extract features for test split (transform TF-IDF)
    print("Engineering test features...")
    X_test_full, _ = extract_business_features(
        df_test_biz, df_upi, df_social, df_footfall, df_reviews, 
        tfidf_vectorizer=tfidf_vec, fit_tfidf=False
    )
    y_test = X_test_full['business_health_12mo'].values
    test_ids = X_test_full['business_id'].values
    X_test = X_test_full.drop(columns=['business_id', 'business_name', 'owner_name', 'business_health_12mo'])

    print(f"Features dimension: {X_train.shape}")

    # Identify categorical and numerical columns
    cat_cols = ['category', 'city']
    num_cols = [col for col in X_train.columns if col not in cat_cols]

    # Preprocessing pipelines
    num_transformer = Pipeline([
        ('imputer', KNNImputer(n_neighbors=5)),
        ('scaler', StandardScaler())
    ])

    cat_transformer = Pipeline([
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])

    preprocessor = ColumnTransformer([
        ('num', num_transformer, num_cols),
        ('cat', cat_transformer, cat_cols)
    ])

    # Save features description to metadata file for the UI
    feature_meta = {
        'numerical_features': num_cols,
        'categorical_features': cat_cols,
        'all_features': list(X_train.columns)
    }
    with open(os.path.join(MODELS_DIR, 'feature_metadata.json'), 'w') as f:
        json.dump(feature_meta, f, indent=4)

    # 1. DEFINE BASE MODELS
    print("Tuning base models...")
    
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    # A. XGBoost Classifier Tuning
    xgb_base = xgb.XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)
    xgb_pipeline_base = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', xgb_base)
    ])
    
    xgb_param_grid = {
        'classifier__max_depth': [3, 5],
        'classifier__learning_rate': [0.05, 0.1],
        'classifier__n_estimators': [100, 150]
    }
    
    print(" - Tuning XGBoost...")
    grid_xgb = GridSearchCV(xgb_pipeline_base, xgb_param_grid, cv=cv, scoring='roc_auc', n_jobs=-1)
    grid_xgb.fit(X_train, y_train)
    best_xgb = grid_xgb.best_estimator_
    print(f"   Best XGB ROC-AUC: {grid_xgb.best_score_:.4f}")

    # B. LightGBM Classifier Tuning
    lgb_base = lgb.LGBMClassifier(random_state=42, verbose=-1)
    lgb_pipeline_base = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', lgb_base)
    ])
    
    lgb_param_grid = {
        'classifier__max_depth': [3, 5],
        'classifier__learning_rate': [0.05, 0.1],
        'classifier__n_estimators': [100, 150]
    }
    
    print(" - Tuning LightGBM...")
    grid_lgb = GridSearchCV(lgb_pipeline_base, lgb_param_grid, cv=cv, scoring='roc_auc', n_jobs=-1)
    grid_lgb.fit(X_train, y_train)
    best_lgb = grid_lgb.best_estimator_
    print(f"   Best LightGBM ROC-AUC: {grid_lgb.best_score_:.4f}")

    # C. Random Forest Baseline
    rf_base = RandomForestClassifier(n_estimators=150, max_depth=6, random_state=42)
    rf_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', rf_base)
    ])
    print(" - Training Random Forest Baseline...")
    rf_pipeline.fit(X_train, y_train)

    # D. Logistic Regression (L2 Regularized Baseline)
    lr_base = LogisticRegression(C=0.5, penalty='l2', max_iter=1000, random_state=42)
    lr_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', lr_base)
    ])
    print(" - Training Logistic Regression Baseline...")
    lr_pipeline.fit(X_train, y_train)

    # E. Stacking Ensemble Classifier
    # We combine XGBoost, LightGBM, Random Forest, and Logistic Regression
    # We extract the classifiers directly from their pipelines so we stack the models
    # but the StackingClassifier itself takes the preprocessor pipeline as part of the overall pipeline!
    print("Building Stacking Classifier...")
    stacking_estimators = [
        ('xgb', best_xgb.named_steps['classifier']),
        ('lgb', best_lgb.named_steps['classifier']),
        ('rf', rf_pipeline.named_steps['classifier']),
        ('lr', lr_pipeline.named_steps['classifier'])
    ]
    
    stacking_classifier = StackingClassifier(
        estimators=stacking_estimators,
        final_estimator=LogisticRegression(C=1.0, penalty='l2', random_state=42),
        cv=cv,
        n_jobs=-1
    )
    
    champion_pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('classifier', stacking_classifier)
    ])
    
    print("Training Stacking Classifier...")
    champion_pipeline.fit(X_train, y_train)

    # 2. EVALUATION ON TEST SET
    models_dict = {
        'Logistic Regression': lr_pipeline,
        'Random Forest': rf_pipeline,
        'XGBoost': best_xgb,
        'LightGBM': best_lgb,
        'Stacking Ensemble (Champion)': champion_pipeline
    }
    
    metrics_summary = []
    
    # Setup plots
    plt.figure(figsize=(18, 5))
    
    # ROC Curve Plot
    ax_roc = plt.subplot(1, 3, 1)
    # PR Curve Plot
    ax_pr = plt.subplot(1, 3, 2)
    # Calibration Curve Plot
    ax_cal = plt.subplot(1, 3, 3)

    for name, model in models_dict.items():
        # Predict probabilities
        y_probs = model.predict_proba(X_test)[:, 1]
        y_pred = model.predict(X_test)
        
        # Metrics
        roc_auc = roc_auc_score(y_test, y_probs)
        
        precision, recall, _ = precision_recall_curve(y_test, y_probs)
        pr_auc = auc(recall, precision)
        
        # Calculate best threshold for F1
        thresholds = np.linspace(0.01, 0.99, 100)
        f1_scores = [f1_score(y_test, (y_probs >= t).astype(int)) for t in thresholds]
        best_idx = np.argmax(f1_scores)
        best_thresh = thresholds[best_idx]
        best_f1 = f1_scores[best_idx]
        
        brier = brier_score_loss(y_test, y_probs)
        accuracy = accuracy_score(y_test, (y_probs >= 0.5).astype(int))
        
        metrics_summary.append({
            'Model': name,
            'ROC-AUC': round(roc_auc, 4),
            'PR-AUC': round(pr_auc, 4),
            'F1-Score (optimal)': round(best_f1, 4),
            'Optimal Threshold': round(best_thresh, 2),
            'Brier Score': round(brier, 4),
            'Accuracy (0.5)': round(accuracy, 4)
        })
        
        # Plot ROC
        from sklearn.metrics import roc_curve
        fpr, tpr, _ = roc_curve(y_test, y_probs)
        ax_roc.plot(fpr, tpr, label=f"{name} (AUC = {roc_auc:.3f})")
        
        # Plot PR
        ax_pr.plot(recall, precision, label=f"{name} (AUC = {pr_auc:.3f})")
        
        # Plot Calibration
        prob_true, prob_pred = calibration_curve(y_test, y_probs, n_bins=10)
        ax_cal.plot(prob_pred, prob_true, marker='o', label=f"{name} (Brier = {brier:.3f})")
        
    # Format ROC
    ax_roc.plot([0, 1], [0, 1], 'k--')
    ax_roc.set_title('ROC Curves')
    ax_roc.set_xlabel('False Positive Rate')
    ax_roc.set_ylabel('True Positive Rate')
    ax_roc.legend()
    ax_roc.grid(True, alpha=0.3)
    
    # Format PR
    ax_pr.set_title('Precision-Recall Curves')
    ax_pr.set_xlabel('Recall')
    ax_pr.set_ylabel('Precision')
    ax_pr.legend()
    ax_pr.grid(True, alpha=0.3)
    
    # Format Calibration
    ax_cal.plot([0, 1], [0, 1], 'k--', label='Perfectly Calibrated')
    ax_cal.set_title('Calibration Curves')
    ax_cal.set_xlabel('Mean Predicted Probability')
    ax_cal.set_ylabel('Fraction of Positives')
    ax_cal.legend()
    ax_cal.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_path = os.path.join(MODELS_DIR, 'model_comparison_plots.png')
    plt.savefig(plot_path)
    plt.close()
    
    df_metrics = pd.DataFrame(metrics_summary)
    df_metrics.to_csv(os.path.join(MODELS_DIR, 'model_metrics.csv'), index=False)
    print("\nModel evaluation summary saved to model_metrics.csv:")
    print(df_metrics.to_string())

    # 3. EXPLAINABILITY VIA SHAP
    # We will build and save a SHAP Explainer using the Random Forest pipeline (to avoid XGBoost 3.0+ compat issues with SHAP)
    # To run TreeExplainer, we pass the trained RF model and the preprocessed background data
    print("Preparing SHAP TreeExplainer using Random Forest pipeline...")
    
    # Fit the preprocessor on training data to generate background data for SHAP
    # Note: SHAP needs the preprocessed numpy array or DataFrame.
    # The preprocessor output has numerical features first, then categorical encoded features.
    X_train_preprocessed = rf_pipeline.named_steps['preprocessor'].transform(X_train)
    
    # Get feature names from preprocessor
    num_feat_names = num_cols
    cat_encoder = rf_pipeline.named_steps['preprocessor'].named_transformers_['cat'].named_steps['onehot']
    cat_feat_names = list(cat_encoder.get_feature_names_out(cat_cols))
    preprocessed_feature_names = num_feat_names + cat_feat_names

    # Convert preprocessed background data back to DataFrame with clean column names for SHAP
    X_train_preprocessed_df = pd.DataFrame(X_train_preprocessed, columns=preprocessed_feature_names)

    # Train TreeExplainer on Random Forest
    rf_classifier = rf_pipeline.named_steps['classifier']
    explainer = shap.TreeExplainer(rf_classifier, data=X_train_preprocessed_df)

    # 4. SAVE MODEL ARTIFACTS
    print("Saving trained pipeline artifacts...")
    joblib.dump(champion_pipeline, os.path.join(MODELS_DIR, 'champion_pipeline.joblib'))
    joblib.dump(rf_pipeline, os.path.join(MODELS_DIR, 'rf_pipeline.joblib'))
    joblib.dump(tfidf_vec, os.path.join(MODELS_DIR, 'tfidf_vectorizer.joblib'))
    joblib.dump(explainer, os.path.join(MODELS_DIR, 'shap_explainer.joblib'))
    
    # Save some samples of raw test set and their scores to a JSON for verification/quick lookup
    print("Generating validation samples for verification...")
    # Get test predictions for a few businesses
    test_probs = champion_pipeline.predict_proba(X_test)[:, 1]
    df_samples = df_test_biz.copy()
    df_samples['predicted_health_score'] = np.round(test_probs * 100, 2)
    df_samples.head(30).to_csv(os.path.join(DATA_DIR, 'scored_test_samples.csv'), index=False)

    print("Pipeline training completed successfully!")

if __name__ == '__main__':
    train_and_evaluate()
