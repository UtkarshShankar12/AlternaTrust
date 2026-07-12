import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import shap

# Add the models folder to system path to import features.py
OS_WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(OS_WORKSPACE_DIR, 'models')
DATA_DIR = os.path.join(OS_WORKSPACE_DIR, 'data')

if MODELS_DIR not in sys.path:
    sys.path.append(MODELS_DIR)

from features import extract_business_features

app = FastAPI(
    title="AI-Powered Credit Underwriting Engine API",
    description="Backend API scoring small business creditworthiness in India using alternative data feeds.",
    version="1.0.0"
)

# Enable CORS for the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify frontend port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for strict validation
class BusinessMeta(BaseModel):
    business_id: str
    business_name: str
    owner_name: str
    category: str
    city: str
    years_in_operation: Optional[float] = None

class UPITransaction(BaseModel):
    business_id: str
    week_start_date: str
    transaction_count: int
    transaction_volume: float
    avg_ticket_size: float

class SocialLog(BaseModel):
    business_id: str
    week_start_date: str
    follower_count: int
    engagement_rate: Optional[float] = None
    posts_count: int

class FootfallLog(BaseModel):
    business_id: str
    week_start_date: str
    check_ins: int
    popular_hours_profile: str

class ReviewLog(BaseModel):
    business_id: str
    rating: int
    review_text: str
    date: str

class CreditScoreRequest(BaseModel):
    business: BusinessMeta
    upi_transactions: List[UPITransaction]
    social_media: List[SocialLog]
    footfall: List[FootfallLog]
    reviews: List[ReviewLog]

class SHAPFactor(BaseModel):
    feature: str
    contribution: float
    impact: str  # "positive" or "negative"
    description: str

class CreditScoreResponse(BaseModel):
    business_id: str
    business_name: str
    credit_score: float
    risk_tier: str  # "Low Risk", "Medium Risk", "High Risk"
    survival_probability: float
    top_factors: List[SHAPFactor]

# Feature explanation descriptions
FEATURE_DESCRIPTIONS = {
    'years_in_operation': 'Years in Business Operation (longer business history signals stability)',
    'upi_vol_total': 'Total UPI Transaction Volume (total cash throughput)',
    'upi_vol_mean': 'Average Weekly UPI Revenue (average weekly transaction volume)',
    'upi_vol_std': 'Revenue Volatility (weekly fluctuations in transaction volume)',
    'upi_vol_cv': 'Cash Flow Volatility Ratio (standardized variation of cash inflows; lower is more consistent)',
    'upi_count_total': 'Total UPI Payments Count (total customer transaction frequency)',
    'upi_count_mean': 'Average Weekly UPI Payments (weekly transaction frequency)',
    'avg_ticket_size_mean': 'Average Order Value (typical ticket size per UPI transaction)',
    'upi_vol_slope': 'Revenue Growth Trend (slope of weekly transaction volume growth)',
    'upi_momentum': 'Revenue Momentum (ratio of recent 12 weeks of volume vs previous 40 weeks)',
    'social_media_active': 'Social Media Presence (active digital footprint)',
    'social_followers_latest': 'Instagram/Social Follower Count (latest follower volume)',
    'social_followers_growth_pct': 'Social Media Follower Growth Rate (percentage growth over 1 year)',
    'social_followers_slope': 'Social Media Follower Trend (weekly growth slope)',
    'social_engagement_mean': 'Social Engagement Rate (average follower likes + comments percentage)',
    'social_posts_total': 'Total Social Posts (volume of promotional activity)',
    'social_posts_mean': 'Weekly Post Consistency (average weekly post frequency)',
    'footfall_total': 'Total Customer Check-ins (aggregate customer footfall)',
    'footfall_mean': 'Average Weekly Check-ins (weekly footfall density)',
    'footfall_std': 'Footfall Volatility (fluctuations in customer visits)',
    'footfall_slope': 'Footfall Growth Trend (slope of weekly check-ins)',
    'footfall_peak_ratio': 'Peak Hours Footfall Ratio (ratio of check-ins during evening peak hours)',
    'review_count_total': 'Total Customer Reviews (volume of digital feedback)',
    'review_rating_mean': 'Average Customer Review Rating (average star rating)',
    'review_rating_std': 'Review Rating Volatility (consistency of customer satisfaction)',
    'review_rating_trend': 'Customer Rating Trend (slope of star ratings over time)',
    'review_sentiment_mean': 'Average Review Sentiment Score (NLP-calculated customer sentiment; higher is more positive)',
    'review_sentiment_std': 'Review Sentiment Volatility (consistency of customer feedback sentiment)'
}

# Global containers loaded on startup
champion_pipeline = None
rf_pipeline = None
tfidf_vectorizer = None
shap_explainer = None
feature_metadata = None

# Database lookup tables for historical trend endpoints
db_biz = None
db_upi = None
db_social = None
db_foot = None
db_rev = None

# In-memory scored businesses cache
businesses_portfolio = []

@app.on_event("startup")
def startup_event():
    global champion_pipeline, rf_pipeline, tfidf_vectorizer, shap_explainer, feature_metadata
    global db_biz, db_upi, db_social, db_foot, db_rev, businesses_portfolio
    
    print("Loading models and pipeline state...")
    try:
        champion_pipeline = joblib.load(os.path.join(MODELS_DIR, 'champion_pipeline.joblib'))
        rf_pipeline = joblib.load(os.path.join(MODELS_DIR, 'rf_pipeline.joblib'))
        tfidf_vectorizer = joblib.load(os.path.join(MODELS_DIR, 'tfidf_vectorizer.joblib'))
        shap_explainer = joblib.load(os.path.join(MODELS_DIR, 'shap_explainer.joblib'))
        
        with open(os.path.join(MODELS_DIR, 'feature_metadata.json'), 'r') as f:
            feature_metadata = json.load(f)
            
        print("Models loaded successfully.")
    except Exception as e:
        print(f"ERROR: Failed to load models. Have you run the training script? Detail: {e}")
        raise e

    print("Loading database tables...")
    try:
        db_biz = pd.read_csv(os.path.join(DATA_DIR, 'raw_businesses.csv'))
        db_upi = pd.read_csv(os.path.join(DATA_DIR, 'upi_transactions.csv'))
        db_social = pd.read_csv(os.path.join(DATA_DIR, 'social_media.csv'))
        db_foot = pd.read_csv(os.path.join(DATA_DIR, 'footfall.csv'))
        db_rev = pd.read_csv(os.path.join(DATA_DIR, 'reviews.csv'))
        print("Database loaded successfully.")
    except Exception as e:
        print(f"ERROR: Failed to load CSV data. Detail: {e}")
        raise e

    # Compute portfolio scores cache at startup (for fast home page response)
    print("Pre-computing portfolio credit risk scores...")
    try:
        # Extract features for all businesses
        df_feats, _ = extract_business_features(
            db_biz, db_upi, db_social, db_foot, db_rev, 
            tfidf_vectorizer=tfidf_vectorizer, fit_tfidf=False
        )
        
        # Keep business_id and remove identifiers for pipeline inference
        biz_ids = df_feats['business_id'].values
        X = df_feats.drop(columns=['business_id', 'business_name', 'owner_name', 'business_health_12mo'], errors='ignore')
        
        probs = champion_pipeline.predict_proba(X)[:, 1]
        
        portfolio = []
        for idx, bid in enumerate(biz_ids):
            biz_row = db_biz[db_biz['business_id'] == bid].iloc[0]
            prob = float(probs[idx])
            score = round(prob * 100, 1)
            
            # Risk tier categorisation
            if score >= 80:
                tier = "Low Risk"
            elif score >= 50:
                tier = "Medium Risk"
            else:
                tier = "High Risk"
                
            portfolio.append({
                'business_id': bid,
                'business_name': biz_row['business_name'],
                'owner_name': biz_row['owner_name'],
                'category': biz_row['category'],
                'city': biz_row['city'],
                'years_in_operation': None if pd.isna(biz_row['years_in_operation']) else float(biz_row['years_in_operation']),
                'credit_score': score,
                'survival_probability': prob,
                'risk_tier': tier
            })
            
        businesses_portfolio = portfolio
        print(f"Scored {len(businesses_portfolio)} portfolio businesses successfully.")
    except Exception as e:
        print(f"ERROR: Failed to pre-compute portfolio scores. Detail: {e}")


def get_feature_description(feat_name: str) -> str:
    """Helper to convert feature name to human readable string."""
    if feat_name in FEATURE_DESCRIPTIONS:
        return FEATURE_DESCRIPTIONS[feat_name]
    
    # Handle TF-IDF terms dynamically
    if feat_name.startswith('tfidf_'):
        word = feat_name.replace('tfidf_', '')
        return f"Customer Review Keyword: '{word.capitalize()}' (mention frequency of this topic in reviews)"
        
    # Handle categories/cities dynamically
    if feat_name.startswith('cat__'):
        details = feat_name.replace('cat__', '').replace('category_', 'Industry Category: ').replace('city_', 'City Location: ')
        return f"Operational Context: {details}"
        
    # Fallback to name format
    return feat_name.replace('_', ' ').capitalize()


def compute_shap_explanations(df_features_row: pd.DataFrame) -> List[SHAPFactor]:
    """
    Computes local SHAP explanations for a single business's engineered features.
    Uses the Random Forest TreeExplainer.
    """
    # 1. Transform raw row to preprocessed representation
    # This must match the ColumnsTransformer order
    preprocessor = rf_pipeline.named_steps['preprocessor']
    X_preprocessed = preprocessor.transform(df_features_row)
    
    # 2. Get feature names to align column dimensions
    num_cols = feature_metadata['numerical_features']
    cat_cols = feature_metadata['categorical_features']
    
    cat_encoder = preprocessor.named_transformers_['cat'].named_steps['onehot']
    cat_feat_names = list(cat_encoder.get_feature_names_out(cat_cols))
    preprocessed_feature_names = num_cols + cat_feat_names
    
    # DataFrame reconstruction
    X_preprocessed_df = pd.DataFrame(X_preprocessed, columns=preprocessed_feature_names)
    
    # 3. Predict SHAP values
    shap_vals = shap_explainer.shap_values(X_preprocessed_df)
    
    # Extract values for Class 1 (survival)
    # RF SHAP output is typically (n_samples, n_features, 2)
    if len(shap_vals.shape) == 3:
        row_shaps = shap_vals[0, :, 1]
    elif len(shap_vals.shape) == 2:
        row_shaps = shap_vals[:, 1] if shap_vals.shape[1] == 2 else shap_vals[0]
    else:
        row_shaps = shap_vals[0]
        
    # 4. Sort and filter top factors
    contributions = []
    for idx, name in enumerate(preprocessed_feature_names):
        shap_val = float(row_shaps[idx])
        contributions.append({
            'feature': name,
            'shap_value': shap_val
        })
        
    # Sort by absolute SHAP value
    contributions_sorted = sorted(contributions, key=lambda x: abs(x['shap_value']), reverse=True)
    
    # Map top 5 to Pydantic objects
    top_factors = []
    for c in contributions_sorted[:5]:
        impact = "positive" if c['shap_value'] > 0 else "negative"
        top_factors.append(SHAPFactor(
            feature=c['feature'],
            contribution=round(c['shap_value'], 4),
            impact=impact,
            description=get_feature_description(c['feature'])
        ))
        
    return top_factors


# =====================================================================
# ENDPOINTS
# =====================================================================

@app.get("/businesses", response_model=List[Dict[str, Any]])
def get_businesses():
    """Returns the cached credit portfolio list of scored businesses."""
    return businesses_portfolio


@app.get("/business/{business_id}/history", response_model=Dict[str, Any])
def get_business_history(business_id: str):
    """
    Returns time-series history (weekly logs) and review texts for a single business.
    Used to render charts and review boards in React.
    """
    biz_mask = db_biz['business_id'] == business_id
    if not biz_mask.any():
        raise HTTPException(status_code=404, detail="Business not found")
        
    biz_row = db_biz[biz_mask].iloc[0]
    
    # Get score details from portfolio cache
    score_details = next((item for item in businesses_portfolio if item['business_id'] == business_id), None)
    score_val = score_details['credit_score'] if score_details else 50.0
    tier_val = score_details['risk_tier'] if score_details else "Medium Risk"
    prob_val = score_details['survival_probability'] if score_details else 0.5

    # Retrieve matching records
    upi_records = db_upi[db_upi['business_id'] == business_id].sort_values('week_start_date').to_dict('records')
    social_records = db_social[db_social['business_id'] == business_id].sort_values('week_start_date').to_dict('records')
    footfall_records = db_foot[db_foot['business_id'] == business_id].sort_values('week_start_date').to_dict('records')
    review_records = db_rev[db_rev['business_id'] == business_id].sort_values('date', ascending=False).to_dict('records')

    # Convert popular times profiles from string back to list for footfall charts
    for record in footfall_records:
        try:
            record['popular_hours_profile'] = json.loads(record['popular_hours_profile'])
        except Exception:
            record['popular_hours_profile'] = []

    # Inject SHAP factors for the business (computed dynamically)
    # Extract features for this single business
    single_biz_df = db_biz[db_biz['business_id'] == business_id]
    df_feat_row, _ = extract_business_features(
        single_biz_df, db_upi, db_social, db_foot, db_rev,
        tfidf_vectorizer=tfidf_vectorizer, fit_tfidf=False
    )
    
    # Drop identifiers
    X_row = df_feat_row.drop(columns=['business_id', 'business_name', 'owner_name', 'business_health_12mo'], errors='ignore')
    top_factors = compute_shap_explanations(X_row)

    # Compile result response
    result = {
        'metadata': {
            'business_id': business_id,
            'business_name': biz_row['business_name'],
            'owner_name': biz_row['owner_name'],
            'category': biz_row['category'],
            'city': biz_row['city'],
            'years_in_operation': None if pd.isna(biz_row['years_in_operation']) else float(biz_row['years_in_operation']),
            'credit_score': score_val,
            'risk_tier': tier_val,
            'survival_probability': prob_val,
            'top_factors': [tf.dict() for tf in top_factors]
        },
        'upi_history': upi_records,
        'social_history': social_records,
        'footfall_history': footfall_records,
        'reviews': review_records
    }
    
    return result


@app.post("/score", response_model=CreditScoreResponse)
def score_business(request: CreditScoreRequest):
    """
    Accepts full alternative data feeds for a single business.
    Performs real-time feature engineering, imputes, scales, runs stacking classifier,
    computes SHAP values, and returns credit score with explanations.
    """
    try:
        # 1. Parse inputs into DataFrames
        biz_data = [{
            'business_id': request.business.business_id,
            'business_name': request.business.business_name,
            'owner_name': request.business.owner_name,
            'category': request.business.category,
            'city': request.business.city,
            'years_in_operation': request.business.years_in_operation
        }]
        df_biz_in = pd.DataFrame(biz_data)

        upi_data = [item.dict() for item in request.upi_transactions]
        df_upi_in = pd.DataFrame(upi_data) if upi_data else pd.DataFrame(columns=['business_id', 'week_start_date', 'transaction_count', 'transaction_volume', 'avg_ticket_size'])

        social_data = [item.dict() for item in request.social_media]
        df_social_in = pd.DataFrame(social_data) if social_data else pd.DataFrame(columns=['business_id', 'week_start_date', 'follower_count', 'engagement_rate', 'posts_count'])

        foot_data = [item.dict() for item in request.footfall]
        df_foot_in = pd.DataFrame(foot_data) if foot_data else pd.DataFrame(columns=['business_id', 'week_start_date', 'check_ins', 'popular_hours_profile'])

        rev_data = [item.dict() for item in request.reviews]
        df_rev_in = pd.DataFrame(rev_data) if rev_data else pd.DataFrame(columns=['business_id', 'rating', 'review_text', 'date'])

        # 2. Run feature extractor (transform mode, using global tfidf_vectorizer)
        df_feat_row, _ = extract_business_features(
            df_biz_in, df_upi_in, df_social_in, df_foot_in, df_rev_in,
            tfidf_vectorizer=tfidf_vectorizer, fit_tfidf=False
        )

        # Remove identifiers to keep layout identical to model columns
        X_row = df_feat_row.drop(columns=['business_id', 'business_name', 'owner_name', 'business_health_12mo'], errors='ignore')

        # 3. Model score prediction
        prob = float(champion_pipeline.predict_proba(X_row)[0, 1])
        score = round(prob * 100, 1)

        # Compute risk tier
        if score >= 80:
            tier = "Low Risk"
        elif score >= 50:
            tier = "Medium Risk"
        else:
            tier = "High Risk"

        # 4. Compute SHAP explanations
        top_factors = compute_shap_explanations(X_row)

        return CreditScoreResponse(
            business_id=request.business.business_id,
            business_name=request.business.business_name,
            credit_score=score,
            risk_tier=tier,
            survival_probability=prob,
            top_factors=top_factors
        )
        
    except Exception as e:
        print(f"ERROR: Inference pipeline failed. Details: {e}")
        raise HTTPException(status_code=500, detail=f"Credit scoring pipeline failed: {str(e)}")


@app.post("/batch-score")
async def batch_score_csv(file: UploadFile = File(...)):
    """
    Ingests a CSV containing business_ids (one per line) or business metadata,
    matches them against relational DB tables, scores them, and returns results.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV uploads are supported")

    try:
        # Read uploaded CSV
        content = await file.read()
        # Decode and load into DataFrame
        import io
        df_uploaded = pd.read_csv(io.StringIO(content.decode('utf-8')))
        
        if 'business_id' not in df_uploaded.columns:
            raise HTTPException(status_code=400, detail="CSV must contain a 'business_id' column")

        # Perform scoring for each business_id
        scored_results = []
        for _, upload_row in df_uploaded.iterrows():
            bid = str(upload_row['business_id']).strip()
            
            # Look up in portfolio cache if available
            cached_score = next((item for item in businesses_portfolio if item['business_id'] == bid), None)
            
            if cached_score:
                scored_results.append(cached_score)
            else:
                # If not cached, try to load dynamically from db
                biz_mask = db_biz['business_id'] == bid
                if biz_mask.any():
                    single_biz_df = db_biz[biz_mask]
                    df_feat_row, _ = extract_business_features(
                        single_biz_df, db_upi, db_social, db_foot, db_rev,
                        tfidf_vectorizer=tfidf_vectorizer, fit_tfidf=False
                    )
                    X_row = df_feat_row.drop(columns=['business_id', 'business_name', 'owner_name', 'business_health_12mo'], errors='ignore')
                    prob = float(champion_pipeline.predict_proba(X_row)[0, 1])
                    score = round(prob * 100, 1)
                    
                    if score >= 80:
                        tier = "Low Risk"
                    elif score >= 50:
                        tier = "Medium Risk"
                    else:
                        tier = "High Risk"
                        
                    biz_data = db_biz[biz_mask].iloc[0]
                    scored_results.append({
                        'business_id': bid,
                        'business_name': biz_data['business_name'],
                        'owner_name': biz_data['owner_name'],
                        'category': biz_data['category'],
                        'city': biz_data['city'],
                        'years_in_operation': None if pd.isna(biz_data['years_in_operation']) else float(biz_data['years_in_operation']),
                        'credit_score': score,
                        'survival_probability': prob,
                        'risk_tier': tier
                    })
                else:
                    # Business not in database at all
                    scored_results.append({
                        'business_id': bid,
                        'business_name': str(upload_row.get('business_name', 'Unknown Business')),
                        'owner_name': str(upload_row.get('owner_name', 'N/A')),
                        'category': str(upload_row.get('category', 'Retail')),
                        'city': str(upload_row.get('city', 'Mumbai')),
                        'years_in_operation': float(upload_row.get('years_in_operation', 2.0)),
                        'credit_score': 50.0,
                        'survival_probability': 0.5,
                        'risk_tier': "Medium Risk (Untracked ID)"
                    })

        return {
            'total_scored': len(scored_results),
            'results': scored_results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV batch processing failed: {str(e)}")


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
