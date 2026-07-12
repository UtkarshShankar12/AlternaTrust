# Model Card: Alternative Credit Underwriting Stacking Ensemble

This model card documents the performance, inputs, design decisions, and limitations of the machine learning model built to predict small business creditworthiness in India using alternative metrics.

---

## Model Details

- **Model Type**: Stacking Classifier
- **Base Estimators**:
  - XGBoost Classifier (Tuned: ROC-AUC: 0.8194 validation)
  - LightGBM Classifier (Tuned: ROC-AUC: 0.8189 validation)
  - Random Forest Classifier (Depth 6, 150 estimators)
  - Logistic Regression (L2 regularization, `C=0.5`)
- **Meta-Classifier**: Logistic Regression (`C=1.0`)
- **SHAP Explanation Model**: Random Forest Classifier (TreeExplainer compatible)
- **Version**: 1.0.0
- **Release Date**: July 12, 2026

---

## Intended Use

- **Primary Goal**: Predict the probability of a small merchant business surviving and growing (`business_health_12mo = 1`) vs declining or closing (`business_health_12mo = 0`) over a 12-month horizon.
- **Target Audience**: Indian micro-merchants (Gyms, Salons, Cafes, Retail Shops) who are cash-heavy and lack traditional corporate credit ratings (CIBIL or formal balance sheets).
- **Credit Risk Translation**: The predicted probability is scaled to a **Risk Score (0-100)**, where:
  - **80-100**: Low Risk (High creditworthiness)
  - **50-79**: Medium Risk (Moderate creditworthiness)
  - **0-49**: High Risk (High probability of default/decline)

---

## Features Ingested & Engineered

The training pipeline ingests four alternative telemetry streams and extracts 50 indicators:

1. **Transactional proxy (UPI Log)**: Total volume, volume consistency (Weekly CV), weekly ticket sizes, transaction frequency, volume growth trend (regression slope), and volume momentum (recent 12 weeks vs previous 40 weeks).
2. **Social Media**: Follower count trends, follower growth percentage, engagement rate averages, post consistency, and posting frequency.
3. **Footfall (Check-ins)**: Total check-ins, weekly check-in growth slope, and peak business hours footfall ratio (evening peak hours check-in density).
4. **Reviews & Sentiment**: Count of reviews, average review rating, ratings volatility, rating trend slope, NLP VADER compound sentiment averages, and top 20 TF-IDF review text keywords.

---

## Training Performance (Out-of-Sample Test Set)

Evaluated on an unseen test set ($N = 160$ businesses, stratified by target):

| Model | ROC-AUC | PR-AUC | F1-Score (Optimal) | Optimal Threshold | Brier Calibration Score | Accuracy (0.5 threshold) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Stacking Ensemble (Champion)** | **0.7964** | **0.8111** | **0.7841** | **0.55** | **0.1874** | **0.7500** |
| Random Forest | 0.7950 | 0.8083 | 0.7865 | 0.50 | 0.1905 | 0.7562 |
| XGBoost Classifier | 0.7906 | 0.8019 | 0.7594 | 0.46 | 0.1942 | 0.7063 |
| LightGBM Classifier | 0.7890 | 0.7983 | 0.7709 | 0.51 | 0.1946 | 0.7312 |
| Logistic Regression | 0.7876 | 0.7986 | 0.7831 | 0.48 | 0.1928 | 0.7375 |

---

## Model Limitations & Operational Warnings

> [!WARNING]
> **Proxy Target Variable Caveat**: This model is trained on a proxy target of business health (`business_health_12mo`) rather than actual loan repayment logs (delinquencies, defaults, write-offs). In a real production deployment, this model must be recalibrated with actual repayment outcomes once credit is extended.
>
> **Fraud and Manipulation Risks**: Alternative signals (like social media followers/engagement and online business reviews) are vulnerable to manipulation. Credit risk analysts must use fraud detection guardrails (e.g. flagging sudden follower spikes or repetitive review text patterns) alongside this model.
>
> **Data Decay / Freshness**: If a merchant stops syncing their UPI logs or social media streams, the model relies on imputation (`KNNImputer`), which degrades prediction accuracy. Real-time API monitoring must ensure data freshness.
>
> **Imbalanced Calibration**: While the Brier Score (0.1874) indicates reasonable calibration, the decision threshold should be set conservatively (e.g., threshold of 0.55) to minimize defaults.
