import os
import json
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Initialize VADER sentiment analyzer
sia = SentimentIntensityAnalyzer()

def compute_slope(y):
    """
    Computes the linear trend slope of a time-series y.
    If the series has less than 2 points, returns 0.
    """
    n = len(y)
    if n < 2:
        return 0.0
    x = np.arange(n)
    # Simple linear regression slope formula
    cov = np.cov(x, y)[0, 1]
    var = np.var(x, ddof=1)
    if var == 0:
        return 0.0
    return float(cov / var)

def extract_business_features(df_biz, df_upi, df_social, df_footfall, df_reviews, tfidf_vectorizer=None, fit_tfidf=True):
    """
    Extracts tabular features from multi-table relational credit data.
    
    Parameters:
    - df_biz: DataFrame of businesses (metadata)
    - df_upi: DataFrame of UPI transactions
    - df_social: DataFrame of social media logs
    - df_footfall: DataFrame of footfall logs
    - df_reviews: DataFrame of reviews
    - tfidf_vectorizer: Existing TfidfVectorizer (optional, for inference)
    - fit_tfidf: Whether to fit a new TfidfVectorizer or use the existing one
    
    Returns:
    - df_features: DataFrame of engineered features ready for modeling/inference
    - tfidf_vectorizer: The fitted or used TfidfVectorizer
    """
    # 1. PROCESS REVIEWS AND SENTIMENT
    # Compute sentiment for all reviews
    if len(df_reviews) > 0:
        # Avoid modifying original dataframe
        df_revs = df_reviews.copy()
        # VADER compound score
        df_revs['sentiment'] = df_revs['review_text'].fillna('').apply(lambda x: sia.polarity_scores(x)['compound'])
        
        # Group reviews by business
        rev_grouped = df_revs.groupby('business_id')
        
        rev_features = rev_grouped.agg(
            review_count_total=('rating', 'count'),
            review_rating_mean=('rating', 'mean'),
            review_rating_std=('rating', 'std'),
            review_sentiment_mean=('sentiment', 'mean'),
            review_sentiment_std=('sentiment', 'std')
        ).reset_index()
        
        # Rating trend slope
        rating_slopes = {}
        for bid, group in rev_grouped:
            # Sort reviews by date to compute slope
            group_sorted = group.sort_values('date')
            rating_slopes[bid] = compute_slope(group_sorted['rating'].values)
        rev_features['review_rating_trend'] = rev_features['business_id'].map(rating_slopes)
    else:
        rev_features = pd.DataFrame(columns=[
            'business_id', 'review_count_total', 'review_rating_mean', 
            'review_rating_std', 'review_sentiment_mean', 'review_sentiment_std', 
            'review_rating_trend'
        ])

    # Concatenate review texts per business for TF-IDF
    biz_texts = []
    biz_ids_text = []
    
    for bid in df_biz['business_id']:
        if len(df_reviews) > 0:
            biz_revs = df_reviews[df_reviews['business_id'] == bid]['review_text'].fillna('').tolist()
            text_combined = " ".join(biz_revs)
        else:
            text_combined = ""
        biz_texts.append(text_combined)
        biz_ids_text.append(bid)
        
    # Fit/Transform TF-IDF
    tfidf_max_features = 20
    if tfidf_vectorizer is None and fit_tfidf:
        tfidf_vectorizer = TfidfVectorizer(max_features=tfidf_max_features, stop_words='english')
        tfidf_matrix = tfidf_vectorizer.fit_transform(biz_texts).toarray()
    elif tfidf_vectorizer is not None:
        tfidf_matrix = tfidf_vectorizer.transform(biz_texts).toarray()
    else:
        # Fallback if no vectorizer and fit_tfidf is False
        tfidf_matrix = np.zeros((len(df_biz), tfidf_max_features))
        
    tfidf_cols = [f"tfidf_{w}" for w in (tfidf_vectorizer.get_feature_names_out() if tfidf_vectorizer else range(tfidf_max_features))]
    df_tfidf = pd.DataFrame(tfidf_matrix, columns=tfidf_cols)
    df_tfidf['business_id'] = biz_ids_text

    # 2. PROCESS UPI TRANSACTIONS
    upi_features = []
    for bid in df_biz['business_id']:
        biz_upi = df_upi[df_upi['business_id'] == bid]
        if len(biz_upi) > 0:
            # Sort chronologically
            biz_upi = biz_upi.sort_values('week_start_date')
            
            vol = biz_upi['transaction_volume'].values
            count = biz_upi['transaction_count'].values
            ticket = biz_upi['avg_ticket_size'].values
            
            # Remove NaNs for calculations (but handle them safely)
            vol_clean = vol[~np.isnan(vol)]
            count_clean = count[~np.isnan(count)]
            ticket_clean = ticket[~np.isnan(ticket)]
            
            vol_sum = np.sum(vol_clean) if len(vol_clean) > 0 else 0.0
            vol_mean = np.mean(vol_clean) if len(vol_clean) > 0 else 0.0
            vol_std = np.std(vol_clean) if len(vol_clean) > 1 else 0.0
            vol_cv = vol_std / (vol_mean + 1e-5)
            
            count_sum = np.sum(count_clean) if len(count_clean) > 0 else 0.0
            count_mean = np.mean(count_clean) if len(count_clean) > 0 else 0.0
            ticket_mean = np.mean(ticket_clean) if len(ticket_clean) > 0 else 0.0
            
            # Trend slope (weekly volume)
            # Use backfilled volume for slope to preserve week alignment
            vol_backfill = pd.Series(vol).bfill().ffill().values
            vol_slope = compute_slope(vol_backfill) if len(vol_backfill) > 0 else 0.0
            
            # Momentum: last 12 weeks vs first 40 weeks
            if len(vol_backfill) >= 12:
                recent_avg = np.mean(vol_backfill[-12:])
                older_avg = np.mean(vol_backfill[:-12]) if len(vol_backfill) > 12 else recent_avg
                momentum = recent_avg / (older_avg + 1e-5)
            else:
                momentum = 1.0
                
            upi_features.append({
                'business_id': bid,
                'upi_vol_total': vol_sum,
                'upi_vol_mean': vol_mean,
                'upi_vol_std': vol_std,
                'upi_vol_cv': vol_cv,
                'upi_count_total': count_sum,
                'upi_count_mean': count_mean,
                'avg_ticket_size_mean': ticket_mean,
                'upi_vol_slope': vol_slope,
                'upi_momentum': momentum
            })
        else:
            upi_features.append({
                'business_id': bid,
                'upi_vol_total': 0.0,
                'upi_vol_mean': 0.0,
                'upi_vol_std': 0.0,
                'upi_vol_cv': 0.0,
                'upi_count_total': 0.0,
                'upi_count_mean': 0.0,
                'avg_ticket_size_mean': 0.0,
                'upi_vol_slope': 0.0,
                'upi_momentum': 1.0
            })
    df_upi_feat = pd.DataFrame(upi_features)

    # 3. PROCESS SOCIAL MEDIA
    social_features = []
    for bid in df_biz['business_id']:
        biz_social = df_social[df_social['business_id'] == bid]
        if len(biz_social) > 0:
            # Sort chronologically
            biz_social = biz_social.sort_values('week_start_date')
            
            followers = biz_social['follower_count'].values
            er = biz_social['engagement_rate'].values
            posts = biz_social['posts_count'].values
            
            # Clean values
            f_clean = followers[~np.isnan(followers)]
            er_clean = er[~np.isnan(er)]
            p_clean = posts[~np.isnan(posts)]
            
            latest_followers = followers[-1] if len(followers) > 0 else np.nan
            first_followers = followers[0] if len(followers) > 0 else np.nan
            
            growth_pct = (latest_followers - first_followers) / (first_followers + 1.0) if not np.isnan(latest_followers) and not np.isnan(first_followers) else 0.0
            
            followers_backfill = pd.Series(followers).bfill().ffill().values
            followers_slope = compute_slope(followers_backfill) if len(followers_backfill) > 0 else 0.0
            
            er_mean = np.mean(er_clean) if len(er_clean) > 0 else np.nan
            posts_total = np.sum(p_clean) if len(p_clean) > 0 else 0.0
            posts_mean = np.mean(p_clean) if len(p_clean) > 0 else 0.0
            
            social_features.append({
                'business_id': bid,
                'social_media_active': 1,
                'social_followers_latest': latest_followers,
                'social_followers_growth_pct': growth_pct,
                'social_followers_slope': followers_slope,
                'social_engagement_mean': er_mean,
                'social_posts_total': posts_total,
                'social_posts_mean': posts_mean
            })
        else:
            # Not active on social media
            social_features.append({
                'business_id': bid,
                'social_media_active': 0,
                'social_followers_latest': np.nan,
                'social_followers_growth_pct': np.nan,
                'social_followers_slope': np.nan,
                'social_engagement_mean': np.nan,
                'social_posts_total': 0.0,
                'social_posts_mean': 0.0
            })
    df_social_feat = pd.DataFrame(social_features)

    # 4. PROCESS FOOTFALL
    footfall_features = []
    for bid in df_biz['business_id']:
        biz_foot = df_footfall[df_footfall['business_id'] == bid]
        if len(biz_foot) > 0:
            biz_foot = biz_foot.sort_values('week_start_date')
            checkins = biz_foot['check_ins'].values
            
            checkins_sum = np.sum(checkins)
            checkins_mean = np.mean(checkins)
            checkins_std = np.std(checkins)
            checkins_slope = compute_slope(checkins)
            
            # Compute peak hour checkins ratio (hours 17, 18, 19, 20 are evening peak)
            peak_ratios = []
            for profile_str in biz_foot['popular_hours_profile']:
                try:
                    profile = json.loads(profile_str)
                    total_hr = sum(profile)
                    peak_hr = sum(profile[17:21]) # 17, 18, 19, 20
                    ratio = peak_hr / (total_hr + 1e-5)
                    peak_ratios.append(ratio)
                except Exception:
                    peak_ratios.append(0.0)
            
            peak_ratio_mean = np.mean(peak_ratios) if len(peak_ratios) > 0 else 0.0
            
            footfall_features.append({
                'business_id': bid,
                'footfall_total': checkins_sum,
                'footfall_mean': checkins_mean,
                'footfall_std': checkins_std,
                'footfall_slope': checkins_slope,
                'footfall_peak_ratio': peak_ratio_mean
            })
        else:
            footfall_features.append({
                'business_id': bid,
                'footfall_total': 0.0,
                'footfall_mean': 0.0,
                'footfall_std': 0.0,
                'footfall_slope': 0.0,
                'footfall_peak_ratio': 0.0
            })
    df_foot_feat = pd.DataFrame(footfall_features)

    # 5. MERGE ALL TABLES
    df_merged = df_biz.copy()
    
    # Merge aggregations
    df_merged = df_merged.merge(df_upi_feat, on='business_id', how='left')
    df_merged = df_merged.merge(df_social_feat, on='business_id', how='left')
    df_merged = df_merged.merge(df_foot_feat, on='business_id', how='left')
    
    if len(rev_features) > 0:
        df_merged = df_merged.merge(rev_features, on='business_id', how='left')
    else:
        # Fill review count and rating features with defaults if no reviews at all
        for col in ['review_count_total', 'review_rating_mean', 'review_rating_std', 
                    'review_sentiment_mean', 'review_sentiment_std', 'review_rating_trend']:
            df_merged[col] = np.nan
        df_merged['review_count_total'] = 0.0
        
    df_merged = df_merged.merge(df_tfidf, on='business_id', how='left')
    
    # Fill review count with 0 for businesses that had no reviews
    df_merged['review_count_total'] = df_merged['review_count_total'].fillna(0.0)
    
    return df_merged, tfidf_vectorizer
