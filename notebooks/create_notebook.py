import os
import json

# Setup notebook directory
OS_WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTEBOOKS_DIR = os.path.join(OS_WORKSPACE_DIR, 'notebooks')
os.makedirs(NOTEBOOKS_DIR, exist_ok=True)

notebook_path = os.path.join(NOTEBOOKS_DIR, 'EDA_and_Modeling.ipynb')

# Construct the notebook cell-by-cell
cells = []

# Section 1: Markdown introduction
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# Alternative Credit Underwriting Engine - Exploratory Data Analysis & Modeling\n",
        "\n",
        "This notebook explores the simulated credit dataset for small Indian businesses (gyms, salons, cafes, and retail shops). It demonstrates:\n",
        "1. **Relational Data Loading & EDA** (class distributions, time-series, and review rating distributions).\n",
        "2. **Feature Engineering** (NLP sentiment/TF-IDF extraction from review text, time-series trend slopes, transaction volatility, and footfall ratios).\n",
        "3. **Leak-Proof Preprocessing** (`ColumnTransformer` combining `KNNImputer`, `StandardScaler`, and `OneHotEncoder`).\n",
        "4. **ML Modeling Suite** (XGBoost, LightGBM, Random Forest, Logistic Regression, and Stacking Ensemble).\n",
        "5. **SHAP Explainability** (Local and global feature attribution via SHAP TreeExplainer)."
    ]
})

# Cell 2: Code imports and setup
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "import os\n",
        "import json\n",
        "import numpy as np\n",
        "import pandas as pd\n",
        "import matplotlib.pyplot as plt\n",
        "import seaborn as sns\n",
        "import sys\n",
        "\n",
        "# Add models directory to path to import features\n",
        "sys.path.append(os.path.abspath('../models'))\n",
        "from features import extract_business_features, compute_slope\n",
        "\n",
        "sns.set_theme(style=\"whitegrid\", palette=\"muted\")\n",
        "plt.rcParams[\"figure.figsize\"] = (12, 6)\n",
        "print(\"Imports and environment set up successfully!\")"
    ]
})

# Section 3: Markdown for EDA Data Loading
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 1. Load Raw Datasets\n",
        "\n",
        "We load the multi-table synthetic relational database generated in the `/data` directory."
    ]
})

# Cell 4: Code for Loading Data
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "data_dir = '../data'\n",
        "df_biz = pd.read_csv(os.path.join(data_dir, 'raw_businesses.csv'))\n",
        "df_upi = pd.read_csv(os.path.join(data_dir, 'upi_transactions.csv'))\n",
        "df_social = pd.read_csv(os.path.join(data_dir, 'social_media.csv'))\n",
        "df_footfall = pd.read_csv(os.path.join(data_dir, 'footfall.csv'))\n",
        "df_reviews = pd.read_csv(os.path.join(data_dir, 'reviews.csv'))\n",
        "\n",
        "print(f\"Loaded {len(df_biz)} businesses.\")\n",
        "print(f\"Loaded {len(df_upi)} weekly UPI transaction records.\")\n",
        "print(f\"Loaded {len(df_social)} weekly social media records.\")\n",
        "print(f\"Loaded {len(df_footfall)} weekly footfall records.\")\n",
        "print(f\"Loaded {len(df_reviews)} customer review records.\")"
    ]
})

# Section 5: Markdown for Visualizations
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 2. Exploratory Data Analysis (EDA)\n",
        "\n",
        "We inspect the distributions and trends inside our datasets."
    ]
})

# Cell 6: Code for Class Distribution Plot
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# Class distribution of target business_health_12mo\n",
        "plt.figure(figsize=(10, 4))\n",
        "plt.subplot(1, 2, 1)\n",
        "sns.countplot(x='business_health_12mo', data=df_biz)\n",
        "plt.title('Business Health Target Distribution (1: Survived, 0: Failed/Closed)')\n",
        "plt.xlabel('Business Health (12mo)')\n",
        "\n",
        "# Business categories\n",
        "plt.subplot(1, 2, 2)\n",
        "sns.countplot(x='category', data=df_biz)\n",
        "plt.title('Business Count by Industry Category')\n",
        "plt.xlabel('Category')\n",
        "plt.tight_layout()\n",
        "plt.show()"
    ]
})

# Cell 7: Code for Years in Operation Boxplot
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# Years in operation vs business health\n",
        "plt.figure(figsize=(10, 4))\n",
        "plt.subplot(1, 2, 1)\n",
        "sns.boxplot(x='business_health_12mo', y='years_in_operation', data=df_biz)\n",
        "plt.title('Years in Operation vs Business Health')\n",
        "plt.xlabel('Business Health (12mo)')\n",
        "plt.ylabel('Years in Operation')\n",
        "\n",
        "# Missingness in years in operation\n",
        "print(f\"Missing years_in_operation values: {df_biz['years_in_operation'].isnull().sum()} ({df_biz['years_in_operation'].isnull().mean()*100:.1f}%)\")\n",
        "\n",
        "# Review rating distribution\n",
        "plt.subplot(1, 2, 2)\n",
        "sns.countplot(x='rating', data=df_reviews)\n",
        "plt.title('Review Star Rating Distribution (All Categories)')\n",
        "plt.xlabel('Rating (1-5)')\n",
        "plt.tight_layout()\n",
        "plt.show()"
    ]
})

# Cell 8: Code for Time-Series Aggregations & Plots
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# Group UPI transactions chronologically and plot average weekly volume per category\n",
        "df_upi_merged = df_upi.merge(df_biz[['business_id', 'category']], on='business_id')\n",
        "weekly_txn = df_upi_merged.groupby(['week_start_date', 'category'])['transaction_volume'].mean().reset_index()\n",
        "weekly_txn['week_start_date'] = pd.to_datetime(weekly_txn['week_start_date'])\n",
        "weekly_txn = weekly_txn.sort_values('week_start_date')\n",
        "\n",
        "plt.figure(figsize=(12, 5))\n",
        "sns.lineplot(x='week_start_date', y='transaction_volume', hue='category', data=weekly_txn)\n",
        "plt.title('Average Weekly UPI Transaction Volume (INR) by Category over 52 Weeks')\n",
        "plt.xlabel('Date')\n",
        "plt.ylabel('Average Weekly Transaction Volume (INR)')\n",
        "plt.xticks(rotation=45)\n",
        "plt.show()"
    ]
})

# Section 9: Markdown for Feature Engineering
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 3. Feature Engineering\n",
        "\n",
        "We extract high-dimensional credit risk indicators including time-series trends (volume slopes, posting frequency slopes, footfall peak ratios) and review text analysis (NLP sentiment, TF-IDF n-grams)."
    ]
})

# Cell 10: Code for running feature extraction
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "print(\"Engineering tabular features from relational tables...\")\n",
        "df_features, tfidf_vec = extract_business_features(\n",
        "    df_biz, df_upi, df_social, df_footfall, df_reviews, \n",
        "    tfidf_vectorizer=None, fit_tfidf=True\n",
        ")\n",
        "\n",
        "print(f\"Engineered feature matrix shape: {df_features.shape}\")\n",
        "print(\"Sample engineered features:\")\n",
        "df_features[['business_id', 'years_in_operation', 'upi_vol_mean', 'upi_vol_cv', \n",
        "             'social_followers_latest', 'footfall_peak_ratio', 'review_sentiment_mean']].head(5)"
    ]
})

# Cell 11: Code for TF-IDF inspect
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# Display the extracted vocabulary for review TF-IDF\n",
        "vocab = tfidf_vec.get_feature_names_out()\n",
        "print(\"Review TF-IDF Vocabulary:\")\n",
        "print(vocab)"
    ]
})

# Section 12: Markdown for Model Training
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 4. Pipeline Setup & Model Training\n",
        "\n",
        "We divide the dataset into train (80%) and test (20%) sets. We configure a leak-proof training pipeline using scikit-learn's `ColumnTransformer` and build base models (Logistic Regression, Random Forest, XGBoost, LightGBM) and our Stacking Ensemble."
    ]
})

# Cell 13: Code for Model Training
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV\n",
        "from sklearn.compose import ColumnTransformer\n",
        "from sklearn.pipeline import Pipeline\n",
        "from sklearn.impute import KNNImputer\n",
        "from sklearn.preprocessing import StandardScaler, OneHotEncoder\n",
        "from sklearn.linear_model import LogisticRegression\n",
        "from sklearn.ensemble import RandomForestClassifier, StackingClassifier\n",
        "from sklearn.metrics import (\n",
        "    roc_auc_score, precision_recall_curve, auc, f1_score, \n",
        "    confusion_matrix, brier_score_loss, accuracy_score, classification_report\n",
        ")\n",
        "from sklearn.calibration import calibration_curve\n",
        "import xgboost as xgb\n",
        "import lightgbm as lgb\n",
        "\n",
        "# Split data\n",
        "df_train_biz, df_test_biz = train_test_split(\n",
        "    df_biz, test_size=0.20, random_state=42, stratify=df_biz['business_health_12mo']\n",
        ")\n",
        "\n",
        "X_train_full, tfidf_vec = extract_business_features(\n",
        "    df_train_biz, df_upi, df_social, df_footfall, df_reviews, \n",
        "    tfidf_vectorizer=None, fit_tfidf=True\n",
        ")\n",
        "y_train = X_train_full['business_health_12mo'].values\n",
        "X_train = X_train_full.drop(columns=['business_id', 'business_name', 'owner_name', 'business_health_12mo'])\n",
        "\n",
        "X_test_full, _ = extract_business_features(\n",
        "    df_test_biz, df_upi, df_social, df_footfall, df_reviews, \n",
        "    tfidf_vectorizer=tfidf_vec, fit_tfidf=False\n",
        ")\n",
        "y_test = X_test_full['business_health_12mo'].values\n",
        "X_test = X_test_full.drop(columns=['business_id', 'business_name', 'owner_name', 'business_health_12mo'])\n",
        "\n",
        "# Define preprocessing columns\n",
        "cat_cols = ['category', 'city']\n",
        "num_cols = [col for col in X_train.columns if col not in cat_cols]\n",
        "\n",
        "preprocessor = ColumnTransformer([\n",
        "    ('num', Pipeline([('imputer', KNNImputer(n_neighbors=5)), ('scaler', StandardScaler())]), num_cols),\n",
        "    ('cat', Pipeline([('onehot', OneHotEncoder(handle_unknown='ignore'))]), cat_cols)\n",
        "])\n",
        "\n",
        "print(\"Features split and preprocessing pipelines ready!\")"
    ]
})

# Cell 14: Code for fitting models
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)\n",
        "\n",
        "# 1. Logistic Regression\n",
        "lr_pipeline = Pipeline([('preprocessor', preprocessor), ('classifier', LogisticRegression(C=0.5, penalty='l2', max_iter=1000, random_state=42))])\n",
        "lr_pipeline.fit(X_train, y_train)\n",
        "\n",
        "# 2. Random Forest\n",
        "rf_pipeline = Pipeline([('preprocessor', preprocessor), ('classifier', RandomForestClassifier(n_estimators=150, max_depth=6, random_state=42))])\n",
        "rf_pipeline.fit(X_train, y_train)\n",
        "\n",
        "# 3. Tuned XGBoost\n",
        "xgb_pipeline = Pipeline([('preprocessor', preprocessor), ('classifier', xgb.XGBClassifier(max_depth=3, learning_rate=0.05, n_estimators=100, use_label_encoder=False, eval_metric='logloss', random_state=42))])\n",
        "xgb_pipeline.fit(X_train, y_train)\n",
        "\n",
        "# 4. Tuned LightGBM\n",
        "lgb_pipeline = Pipeline([('preprocessor', preprocessor), ('classifier', lgb.LGBMClassifier(max_depth=3, learning_rate=0.05, n_estimators=100, random_state=42, verbose=-1))])\n",
        "lgb_pipeline.fit(X_train, y_train)\n",
        "\n",
        "# 5. Stacking StackingClassifier\n",
        "stacking_estimators = [\n",
        "    ('xgb', xgb_pipeline.named_steps['classifier']),\n",
        "    ('lgb', lgb_pipeline.named_steps['classifier']),\n",
        "    ('rf', rf_pipeline.named_steps['classifier']),\n",
        "    ('lr', lr_pipeline.named_steps['classifier'])\n",
        "]\n",
        "stacking_classifier = StackingClassifier(estimators=stacking_estimators, final_estimator=LogisticRegression(C=1.0, penalty='l2', random_state=42), cv=cv)\n",
        "champion_pipeline = Pipeline([('preprocessor', preprocessor), ('classifier', stacking_classifier)])\n",
        "champion_pipeline.fit(X_train, y_train)\n",
        "\n",
        "print(\"All classifiers trained successfully!\")"
    ]
})

# Section 15: Markdown for Evaluation
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 5. Model Comparison & Metrics Evaluation\n",
        "\n",
        "We evaluate the models on the unseen test set using ROC-AUC, PR-AUC, F1-Score, Brier Calibration score, and plot the evaluation curves."
    ]
})

# Cell 16: Code for computing metrics and plotting curves
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "from sklearn.metrics import roc_curve\n",
        "\n",
        "models_dict = {\n",
        "    'Logistic Regression': lr_pipeline,\n",
        "    'Random Forest': rf_pipeline,\n",
        "    'XGBoost': xgb_pipeline,\n",
        "    'LightGBM': lgb_pipeline,\n",
        "    'Stacking Ensemble (Champion)': champion_pipeline\n",
        "}\n",
        "\n",
        "metrics_summary = []\n",
        "\n",
        "fig, axes = plt.subplots(1, 3, figsize=(20, 6))\n",
        "ax_roc, ax_pr, ax_cal = axes[0], axes[1], axes[2]\n",
        "\n",
        "for name, model in models_dict.items():\n",
        "    y_probs = model.predict_proba(X_test)[:, 1]\n",
        "    roc_auc = roc_auc_score(y_test, y_probs)\n",
        "    \n",
        "    precision, recall, _ = precision_recall_curve(y_test, y_probs)\n",
        "    pr_auc = auc(recall, precision)\n",
        "    \n",
        "    thresholds = np.linspace(0.01, 0.99, 100)\n",
        "    f1_scores = [f1_score(y_test, (y_probs >= t).astype(int)) for t in thresholds]\n",
        "    best_idx = np.argmax(f1_scores)\n",
        "    best_f1 = f1_scores[best_idx]\n",
        "    best_thresh = thresholds[best_idx]\n",
        "    \n",
        "    brier = brier_score_loss(y_test, y_probs)\n",
        "    accuracy = accuracy_score(y_test, (y_probs >= 0.5).astype(int))\n",
        "    \n",
        "    metrics_summary.append({\n",
        "        'Model': name,\n",
        "        'ROC-AUC': roc_auc,\n",
        "        'PR-AUC': pr_auc,\n",
        "        'F1-Score': best_f1,\n",
        "        'Brier Score': brier,\n",
        "        'Accuracy (0.5)': accuracy\n",
        "    })\n",
        "    \n",
        "    # Plot ROC\n",
        "    fpr, tpr, _ = roc_curve(y_test, y_probs)\n",
        "    ax_roc.plot(fpr, tpr, label=f'{name} (AUC = {roc_auc:.3f})')\n",
        "    \n",
        "    # Plot PR\n",
        "    ax_pr.plot(recall, precision, label=f'{name} (AUC = {pr_auc:.3f})')\n",
        "    \n",
        "    # Plot Calibration\n",
        "    prob_true, prob_pred = calibration_curve(y_test, y_probs, n_bins=10)\n",
        "    ax_cal.plot(prob_pred, prob_true, marker='o', label=f'{name} (Brier = {brier:.3f})')\n",
        "\n",
        "# Format ROC\n",
        "ax_roc.plot([0, 1], [0, 1], 'k--')\n",
        "ax_roc.set_title('ROC Curves (Sensitivity vs specificity)')\n",
        "ax_roc.set_xlabel('False Positive Rate')\n",
        "ax_roc.set_ylabel('True Positive Rate')\n",
        "ax_roc.legend()\n",
        "ax_roc.grid(True, alpha=0.3)\n",
        "\n",
        "# Format PR\n",
        "ax_pr.set_title('Precision-Recall Curves')\n",
        "ax_pr.set_xlabel('Recall')\n",
        "ax_pr.set_ylabel('Precision')\n",
        "ax_pr.legend()\n",
        "ax_pr.grid(True, alpha=0.3)\n",
        "\n",
        "# Format Calibration\n",
        "ax_cal.plot([0, 1], [0, 1], 'k--', label='Perfectly Calibrated')\n",
        "ax_cal.set_title('Calibration Curves (Risk probability reliability)')\n",
        "ax_cal.set_xlabel('Mean Predicted Probability')\n",
        "ax_cal.set_ylabel('Fraction of Positives')\n",
        "ax_cal.legend()\n",
        "ax_cal.grid(True, alpha=0.3)\n",
        "\n",
        "plt.tight_layout()\n",
        "plt.show()\n",
        "\n",
        "df_m = pd.DataFrame(metrics_summary)\n",
        "display(df_m)"
    ]
})

# Section 17: Markdown for SHAP
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "## 6. Model Explainability via SHAP (TreeExplainer)\n",
        "\n",
        "SHAP values measure the marginal contribution of each feature to a credit score prediction. We load our pre-trained SHAP TreeExplainer (fit on the Random Forest pipeline) and visualize the global feature importances."
    ]
})

# Cell 18: Code for running SHAP
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "import shap\n",
        "import joblib\n",
        "\n",
        "print(\"Loading pre-fit SHAP Explainer...\")\n",
        "explainer = joblib.load('../models/shap_explainer.joblib')\n",
        "\n",
        "# Compute SHAP values for a sample of the test set\n",
        "X_test_preprocessed = rf_pipeline.named_steps['preprocessor'].transform(X_test)\n",
        "\n",
        "# Get feature names\n",
        "num_feat_names = num_cols\n",
        "cat_encoder = rf_pipeline.named_steps['preprocessor'].named_transformers_['cat'].named_steps['onehot']\n",
        "cat_feat_names = list(cat_encoder.get_feature_names_out(cat_cols))\n",
        "preprocessed_feature_names = num_feat_names + cat_feat_names\n",
        "\n",
        "X_test_preprocessed_df = pd.DataFrame(X_test_preprocessed, columns=preprocessed_feature_names)\n",
        "shap_values = explainer.shap_values(X_test_preprocessed_df.iloc[:100])\n",
        "\n",
        "# Plot SHAP summary plot (for Class 1: Survival)\n",
        "# Note: Random Forest SHAP values shape: (n_samples, n_features, n_classes)\n",
        "if len(shap_values.shape) == 3:\n",
        "    class1_shap = shap_values[:, :, 1]\n",
        "else:\n",
        "    class1_shap = shap_values\n",
        "\n",
        "shap.summary_plot(class1_shap, X_test_preprocessed_df.iloc[:100], max_display=15)"
    ]
})

# Section 19: Markdown for local explainability demonstration
cells.append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "### Local SHAP Explanation Demonstration\n",
        "\n",
        "Let's write a python function to print the top positive and negative contributing factors for a single business prediction in plain English. This logic will be running live inside our FastAPI `/score` endpoint!"
    ]
})

# Cell 20: Code for local explainability prints
cells.append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "def explain_prediction(business_idx, df_raw_sample, X_preprocessed_df, shap_values_array):\n",
        "    # Get actual details\n",
        "    biz_name = df_raw_sample.iloc[business_idx]['business_name']\n",
        "    biz_cat = df_raw_sample.iloc[business_idx]['category']\n",
        "    credit_score = df_raw_sample.iloc[business_idx]['predicted_health_score']\n",
        "    \n",
        "    # Get SHAP values for class 1 (survive/creditworthy)\n",
        "    # Extract values for the specific business\n",
        "    row_shaps = shap_values_array[business_idx, :, 1] if len(shap_values_array.shape) == 3 else shap_values_array[business_idx]\n",
        "    \n",
        "    # Sort features by absolute contribution\n",
        "    feat_names = X_preprocessed_df.columns\n",
        "    contributions = pd.DataFrame({\n",
        "        'feature': feat_names,\n",
        "        'shap_value': row_shaps\n",
        "    }).sort_values('shap_value', key=abs, ascending=False)\n",
        "    \n",
        "    print(f\"=== Credit Risk Report for: {biz_name} ({biz_cat}) ===\")\n",
        "    print(f\"Risk Health Score: {credit_score}/100 (Higher is healthier credit)\")\n",
        "    print(\"\\nTop Contributing Credit Factors (SHAP analysis):\")\n",
        "    \n",
        "    for idx, row in contributions.head(5).iterrows():\n",
        "        direction = \"Positive (Enhances Credit)\" if row['shap_value'] > 0 else \"Negative (Increases Risk)\"\n",
        "        print(f\" - {row['feature']}: {row['shap_value']:.4f} -> {direction}\")\n",
        "\n",
        "# Load the validation samples\n",
        "df_samples = pd.read_csv('../data/scored_test_samples.csv')\n",
        "df_samples_pre = rf_pipeline.named_steps['preprocessor'].transform(df_samples.drop(columns=['business_id', 'business_name', 'owner_name', 'business_health_12mo', 'predicted_health_score'], errors='ignore'))\n",
        "df_samples_pre_df = pd.DataFrame(df_samples_pre, columns=preprocessed_feature_names)\n",
        "sample_shaps = explainer.shap_values(df_samples_pre_df)\n",
        "\n",
        "# Explain the first 2 businesses in validation list\n",
        "explain_prediction(0, df_samples, df_samples_pre_df, sample_shaps)\n",
        "print(\"\\n\")\n",
        "explain_prediction(1, df_samples, df_samples_pre_df, sample_shaps)"
    ]
})

# Save notebook contents to JSON
notebook_json = {
    "cells": cells,
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3 (ipykernel)",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 2
}

with open(notebook_path, 'w') as f:
    json.dump(notebook_json, f, indent=2)

print(f"Jupyter Notebook generated successfully at: {notebook_path}")
