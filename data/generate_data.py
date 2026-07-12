import os
import random
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from faker import Faker

# Set random seeds for reproducibility
random.seed(42)
np.random.seed(42)

# Initialize Faker with Indian locale
fake = Faker('en_IN')

# Configuration
NUM_BUSINESSES = 800
NUM_WEEKS = 52
START_DATE = datetime(2025, 7, 15)

CATEGORIES = ['Gym', 'Salon', 'Cafe', 'Retail']
CITIES = ['Delhi', 'Mumbai', 'Bengaluru', 'Chennai', 'Pune', 'Hyderabad']

# Directory setup
OS_WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(OS_WORKSPACE_DIR, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

print(f"Generating synthetic data in: {DATA_DIR}")

# Review templates to create rich textual data for NLP processing
REVIEW_TEMPLATES = {
    'Gym': {
        5: [
            "Great trainers, modern equipment, very clean gym. Best gym in the area!",
            "Excellent workout atmosphere, trainers are very helpful. Clean changing rooms.",
            "Fully equipped with the latest machines. The personal trainers really know their stuff.",
            "Love the vibes here. The group classes are highly energetic and fun!",
            "Top class facilities and very hygienic post-COVID setup. Strongly recommended."
        ],
        4: [
            "Good place to work out. Equipment is well-maintained, though it gets crowded in evenings.",
            "Decent gym with polite staff. Parking can sometimes be an issue.",
            "Nice trainers and good environment. The monthly subscription is worth the price.",
            "Spacious gym floor. Wish they had more benches, but overall a solid experience.",
            "Satisfied with the hygiene and trainer support. Good value for money."
        ],
        3: [
            "Average gym. Some machines are often out of order and repairs take weeks.",
            "It's fine for basic lifting, but the music is way too loud and annoying.",
            "Trainers are okay, but they focus more on personal training clients than regulars.",
            "Decent space but the ventilation could be improved. Smells sweaty during peak hours.",
            "A bit crowded. The staff is polite but the locker facility is average."
        ],
        2: [
            "Very crowded and half the treadmills don't work. Not worth the subscription fee.",
            "Trainers are unfriendly and keep pushing expensive supplement packages.",
            "The washrooms are rarely clean. Heavy smell of sweat and dampness.",
            "Poor management. They changed the timings without informing members in advance.",
            "A lot of broken equipment. The dumbbells are unorganized and hard to find."
        ],
        1: [
            "Extremely unhygienic. The air conditioning never works and trainers are unprofessional. Waste of money.",
            "Rude staff, rusty equipment, and terrible hygiene. Wish I could give zero stars.",
            "They charged me for a full year and closed down the evening slot. Fraud management!",
            "Terrible experience. The trainer gave me wrong instructions and I got a back injury.",
            "Completely waste of money. No water in washrooms and dirty floor. Avoid at all costs."
        ]
    },
    'Salon': {
        5: [
            "Awesome hair spa session by Rajesh. Very polite staff and neat services.",
            "Excellent bridal makeup and hair styling. The staff is highly professional.",
            "Clean salon, relaxing ambiance. Loved the facial and manicure. Will visit again!",
            "Great service at reasonable rates. They use premium products. Highly recommended.",
            "Perfect styling every single time. Rajesh is a master barber!"
        ],
        4: [
            "Very good salon. Polite staff and quick service. A bit pricey but good quality.",
            "Nice haircuts. The waiting area is comfortable, and they offer green tea.",
            "Satisfactory hygiene levels. Staff is helpful in suggesting the right treatment.",
            "Good salon experience. Make sure to book an appointment as weekends are packed.",
            "Modern setup and skilled staff. The hair color came out exactly as expected."
        ],
        3: [
            "Service is average. The stylist seemed in a hurry and didn't listen to instructions.",
            "Okay hair cut, but wait time was 30 minutes even with an appointment.",
            "The ambiance is nice, but prices have increased significantly. Not as good value now.",
            "Average styling. Hygiene in the washing area could be improved.",
            "It was okay. Nothing exceptional. Basic haircut was decent but styling was mediocre."
        ],
        2: [
            "Very disappointed. The stylist cut my hair way too short and unevenly.",
            "Dirty towels and uncleaned combs. The management doesn't care about basic hygiene.",
            "Overpriced for such basic services. They charge extra for small things without telling.",
            "Rude receptionist and very slow staff. Waited 45 minutes for a simple trim.",
            "Poor service quality. The hair treatment caused scalp irritation. Will not return."
        ],
        1: [
            "Ruined my haircut completely. Unprofessional staff, dirty scissors and overpriced.",
            "Worst salon experience ever. They burned my hair during straightening. Terrible!",
            "Extremely unhygienic. Used the same dirty towel on me. Disgusting service.",
            "Arrogant staff and terrible service. They cut my ear slightly with the scissors and didn't even apologize.",
            "Complete waste of money. Total fraud prices and unskilled workers. Highly unprofessional."
        ]
    },
    'Cafe': {
        5: [
            "Loved the cold brew and the paneer tikka sandwich. Ambient lighting makes it perfect for working.",
            "Excellent coffee, cozy seating, and polite staff. The blueberry cheesecake is a must-try!",
            "Best cafe in the city. Great music, wonderful staff, and the pasta was super delicious.",
            "A perfect workspace. WiFi is fast and the pour-over coffee is exceptional.",
            "Great vibes and amazing food. The outdoor seating is very beautiful."
        ],
        4: [
            "Good coffee and cozy ambience. Perfect for a casual meeting or reading.",
            "Tasty sandwiches and milkshakes. Service is a bit slow during weekends.",
            "Nice ambiance and friendly staff. Price is slightly on the higher side.",
            "Loved the pizza and hot chocolate. Good place to hang out with friends.",
            "Clean cafe with a nice selection of desserts. Coffee quality is consistent."
        ],
        3: [
            "Decent cafe but the seating is cramped. Coffee is average, nothing special.",
            "Food is okay but overpriced. The acoustics are bad, gets very noisy.",
            "Service is slow. We had to ask for water three times. Sandwich was dry.",
            "Ambiance is good for photos, but the main dishes are mediocre. Desserts are better.",
            "An average cafe. Good tea but the snacks were oily and lukewarm."
        ],
        2: [
            "Terrible service, waited 45 minutes for a cold coffee. The food was tasteless and expensive.",
            "Very noisy, bad seating, and average coffee. Staff looked confused and uncoordinated.",
            "Air conditioning was not working. The sandwich had stale bread. Very disappointed.",
            "Hygiene is questionable. Saw flies near the cake display. Avoid eating here.",
            "Overpriced and tasteless. The espresso shot was sour and burned. Poor barista skills."
        ],
        1: [
            "Found a hair in my food! Extremely unhygienic kitchen. Arrogant manager refused to refund.",
            "Terrible food, horrible service. The waiters are rude and ignore customers. Stay away!",
            "Stale food that gave my friend food poisoning. Disgusting and unsafe cafe.",
            "Worst place ever. Dirty tables, bad smell, and expensive, cold food. Avoid!",
            "Terrible customer service. They charged us service charge forcibly and misbehaved."
        ]
    },
    'Retail': {
        5: [
            "Very friendly owner and they always have fresh stock. Price is also reasonable.",
            "Excellent collection of apparel. The staff helps you find the right fit patiently.",
            "Great neighborhood store. Always well-stocked and they deliver home quickly.",
            "Super clean store layout. Got a great discount on groceries. Highly recommended!",
            "Outstanding service. The owner ordered a specific item just for me. Very customer-centric."
        ],
        4: [
            "Good range of items. The store is clean and billing is fast. Friendly staff.",
            "Nice shopping experience. Most items are available, parking is slightly tight.",
            "Satisfied with the collection. Prices are competitive compared to supermarket chains.",
            "Organized sections. Got what I needed quickly. Helpful floor staff.",
            "Decent discounts and polite billing clerks. Good neighborhood retail shop."
        ],
        3: [
            "Okay shop. Some items are close to expiry, so check labels carefully.",
            "Limited collection. They don't have many brand options for household goods.",
            "The store is a bit congested. Billing takes long during evening rush hours.",
            "Average service. The staff is indifferent and not very helpful.",
            "Prices are okay, but they don't accept cards for small amounts below 100 Rs."
        ],
        2: [
            "Rude staff. They don't accept cards/UPI easily and sell items past expiry date.",
            "Messy layout, difficult to find items. The staff is clueless about the stock.",
            "Prices are higher than MRP on some items. Shady billing practices.",
            "Poor customer support. Refused to exchange a defective item purchased just yesterday.",
            "Cramped aisles and dirty floors. The store needs better management."
        ],
        1: [
            "Complete fraud. Charged me double for items and refused a refund. Horrible experience.",
            "Worst retail shop. Arrogant owner, expired products, and bad attitude. Never visiting again.",
            "Selling duplicate items and charging above MRP. Report them to consumer forum!",
            "Extremely rude staff. They accused us of shoplifting just because we were looking around. Insulting!",
            "Dirty store, expired items on shelves, and bad customer service. Total waste of time."
        ]
    }
}

# 1. GENERATE BUSINESS METADATA
businesses = []
for i in range(1, NUM_BUSINESSES + 1):
    bus_id = f"BUS_{i:04d}"
    category = random.choice(CATEGORIES)
    city = random.choice(CITIES)
    
    # Generate business name
    suffix = {
        'Gym': ['Fitness', 'Iron Gym', 'Powerhouse', 'CrossFit', 'Arena', 'Studio', 'Pulse'],
        'Salon': ['Spa & Salon', 'Makeover Studio', 'Unisex Salon', 'Glow', 'Styles', 'Cuts & Curls'],
        'Cafe': ['Cafe', 'Bistro', 'Coffee House', 'Brew Room', 'Beans & Leaves', 'Corner'],
        'Retail': ['Mart', 'Supermarket', 'Provisions', 'Bazaar', 'Stores', 'Apparels']
    }
    bus_name = f"{fake.first_name()}'s {random.choice(suffix[category])}"
    owner_name = fake.name()
    
    # Latent variable H (Health) which dictates the ground truth survival/success
    # Normal distribution with mean 0, variance 1.
    latent_health = float(np.random.normal(0, 1.0))
    
    # Experience in years (Log-normal distribution to skew towards younger businesses, but correlate with health)
    years_base = np.random.lognormal(mean=0.8, sigma=0.6)
    years_in_operation = float(np.clip(years_base + 0.5 * latent_health, 0.5, 15.0))
    
    # Probabilistic survival label based on health and experience
    # Stronger health and more years -> higher probability of survival
    logit = 1.6 * latent_health + 0.4 * np.log(years_in_operation) - 0.2
    prob_survival = 1 / (1 + np.exp(-logit))
    business_health_12mo = 1 if random.random() < prob_survival else 0
    
    businesses.append({
        'business_id': bus_id,
        'business_name': bus_name,
        'owner_name': owner_name,
        'category': category,
        'city': city,
        'years_in_operation': round(years_in_operation, 2),
        'latent_health': latent_health,  # Hidden factor used to generate consistent features
        'business_health_12mo': business_health_12mo
    })

df_businesses = pd.DataFrame(businesses)

# Introduce some missing values in years_in_operation to test imputation (e.g. 5% missingness)
missing_mask = np.random.rand(len(df_businesses)) < 0.05
df_businesses.loc[missing_mask, 'years_in_operation'] = np.nan

# Save businesses to file (hide latent_health from training, but keep it in data/latent_factors.csv for verification if needed)
df_businesses.drop(columns=['latent_health']).to_csv(os.path.join(DATA_DIR, 'raw_businesses.csv'), index=False)
df_businesses[['business_id', 'latent_health']].to_csv(os.path.join(DATA_DIR, 'latent_factors.csv'), index=False)

print("Saved raw_businesses.csv and latent_factors.csv")

# 2. GENERATE WEEKLY TIMESERIES DATA (UPI, SOCIAL, FOOTFALL)
upi_records = []
social_records = []
footfall_records = []
review_records = []

# Date generator helper
weeks_dates = [START_DATE - timedelta(weeks=w) for w in range(NUM_WEEKS)]
weeks_dates.reverse() # Start from 52 weeks ago to today

# Footfall peak hours templates (hourly index summing to 1.0)
PEAK_HOURS_TEMPLATES = {
    'Gym': [0.03, 0.08, 0.12, 0.09, 0.04, 0.02, 0.01, 0.01, 0.02, 0.02, 0.02, 0.02, 0.02, 0.01, 0.02, 0.04, 0.10, 0.15, 0.12, 0.06, 0.03, 0.01, 0.01, 0.01],
    'Cafe': [0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.04, 0.06, 0.08, 0.07, 0.06, 0.09, 0.12, 0.08, 0.05, 0.06, 0.08, 0.10, 0.05, 0.03, 0.02, 0.01, 0.01, 0.01],
    'Salon': [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.01, 0.02, 0.04, 0.06, 0.08, 0.08, 0.08, 0.07, 0.08, 0.10, 0.12, 0.10, 0.08, 0.05, 0.02, 0.01, 0.00, 0.00],
    'Retail': [0.01, 0.01, 0.01, 0.01, 0.01, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.06, 0.08, 0.07, 0.06, 0.08, 0.10, 0.12, 0.11, 0.08, 0.05, 0.02, 0.01, 0.01]
}

for index, row in df_businesses.iterrows():
    bus_id = row['business_id']
    cat = row['category']
    h = row['latent_health']
    
    # --------------------
    # A. TRANSACTION PROXY DATA (UPI)
    # --------------------
    # Base transaction parameters based on category and latent health
    if cat == 'Gym':
        base_txn_count = 35 + 15 * h
        base_ticket_size = 1800 + 400 * h
    elif cat == 'Cafe':
        base_txn_count = 220 + 90 * h
        base_ticket_size = 220 + 30 * h
    elif cat == 'Salon':
        base_txn_count = 55 + 25 * h
        base_ticket_size = 750 + 150 * h
    else: # Retail
        base_txn_count = 140 + 60 * h
        base_ticket_size = 450 + 90 * h

    # Ensure boundaries are realistic and positive
    base_txn_count = max(5, base_txn_count)
    base_ticket_size = max(50, base_ticket_size)

    # Volatility factor - Unhealthy businesses have higher volatility (cash flow inconsistency)
    volatility = max(0.08, 0.15 - 0.06 * h)

    # Trend slope over time - Healthy businesses grow, Unhealthy ones shrink
    trend_slope = 0.005 * h  # growth percentage per week

    # --------------------
    # B. SOCIAL MEDIA DATA
    # --------------------
    # Follower count starting point (52 weeks ago)
    follower_start = 800 + 400 * h
    if cat in ['Gym', 'Salon']:
        follower_start += 300 # More visual businesses
    follower_start = max(40, follower_start)
    current_followers = follower_start

    # Posting rates
    avg_posts_week = max(0.2, 2.0 + 1.2 * h) # Unhealthy posting drops

    # Engagement rate (likes + comments / followers)
    engagement_base = max(0.005, 0.04 + 0.018 * h)

    # --------------------
    # C. FOOTFALL DATA
    # --------------------
    # Average weekly check-ins
    if cat == 'Gym':
        base_checkins = 120 + 40 * h
    elif cat == 'Cafe':
        base_checkins = 250 + 90 * h
    elif cat == 'Salon':
        base_checkins = 40 + 15 * h
    else: # Retail
        base_checkins = 90 + 35 * h
    base_checkins = max(3, base_checkins)

    # --------------------
    # SIMULATING THE 52 WEEKS
    # --------------------
    social_missing = random.random() < 0.08 # 8% businesses have missing/no social media profiles
    
    for w in range(NUM_WEEKS):
        date_str = weeks_dates[w].strftime('%Y-%m-%d')
        
        # Seasonality factor (Diwali peak at week 15-18 (autumn), summer dip, etc.)
        # Diwali boost for Retail/Salon/Cafe (weeks 15-18 or weeks 40-42)
        seasonality = 1.0
        if w in [15, 16, 17, 18, 40, 41, 42]:
            if cat in ['Retail', 'Salon', 'Cafe']:
                seasonality = 1.35 + 0.1 * np.random.normal(0, 0.1)
            else: # Gyms drop slightly during major festivals
                seasonality = 0.85
        elif w in [22, 23, 24, 25]: # Monsoon dip for footfalls
            seasonality = 0.90

        # Dynamic trend multiplier
        trend_mult = (1.0 + trend_slope) ** w
        
        # 1. Generate UPI transactions
        weekly_count_noise = np.random.normal(0, volatility)
        weekly_volume_noise = np.random.normal(0, volatility * 1.2)
        
        txn_count = int(np.round(base_txn_count * trend_mult * seasonality * (1.0 + weekly_count_noise)))
        txn_count = max(1, txn_count)
        
        ticket_size = base_ticket_size * (1.0 + np.random.normal(0, 0.05)) # steady ticket size
        ticket_size = max(20, ticket_size)
        
        txn_volume = txn_count * ticket_size * (1.0 + weekly_volume_noise)
        txn_volume = max(txn_count * 20, txn_volume)
        
        upi_records.append({
            'business_id': bus_id,
            'week_start_date': date_str,
            'transaction_count': txn_count,
            'transaction_volume': round(float(txn_volume), 2),
            'avg_ticket_size': round(float(txn_volume / txn_count), 2)
        })

        # 2. Generate Social Media Metrics
        if not social_missing:
            # Follower growth is stochastic but guided by trend and health
            growth_noise = np.random.normal(0, 0.005)
            growth_rate = (0.008 * h + 0.004) + growth_noise
            # If business is failing (h < 0), growth decays, sometimes losing followers
            if h < 0:
                growth_rate = max(-0.02, growth_rate)
            
            current_followers *= (1.0 + growth_rate)
            current_followers = max(10, current_followers)
            
            # Post frequency might drop for failing businesses in latter half of year
            posts_decay = 1.0
            if h < -0.2 and w > 26:
                posts_decay = max(0.1, 1.0 - 0.03 * (w - 26)) # Posting fades away
            
            posts = int(np.random.poisson(avg_posts_week * posts_decay))
            
            # Engagement rate has weekly fluctuation
            er = engagement_base * (1.0 + np.random.normal(0, 0.15))
            er = np.clip(er, 0.001, 0.20)
            
            social_records.append({
                'business_id': bus_id,
                'week_start_date': date_str,
                'follower_count': int(np.round(current_followers)),
                'engagement_rate': round(float(er), 4),
                'posts_count': posts
            })
        else:
            # Let's write NaN/None occasionally to represent empty records in tables
            # This simulates real missing records in the database.
            pass

        # 3. Generate Footfall Data
        checkins_noise = np.random.normal(0, 0.1)
        checkins = int(np.round(base_checkins * trend_mult * seasonality * (1.0 + checkins_noise)))
        checkins = max(0, checkins)
        
        # Hourly popular times (distribute actual check-ins across 24 hours based on template + noise)
        hourly_template = np.array(PEAK_HOURS_TEMPLATES[cat])
        hourly_noise = np.random.dirichlet(np.ones(24) * 10) # smooth Dirichlet noise
        hourly_dist = 0.85 * hourly_template + 0.15 * hourly_noise
        hourly_dist /= hourly_dist.sum()
        
        hourly_checkins = np.random.multinomial(checkins, hourly_dist)
        
        footfall_records.append({
            'business_id': bus_id,
            'week_start_date': date_str,
            'check_ins': checkins,
            'popular_hours_profile': json.dumps(hourly_checkins.tolist())
        })

    # --------------------
    # D. REVIEWS GENERATION
    # --------------------
    # Total reviews count depends on health (more active business = more reviews)
    total_reviews = int(np.random.poisson(max(2.0, 18.0 + 12.0 * h)))
    total_reviews = max(3, total_reviews)
    
    for r in range(total_reviews):
        # Review date random within 52 weeks
        rev_week = random.randint(0, NUM_WEEKS - 1)
        rev_date = weeks_dates[rev_week] + timedelta(days=random.randint(0, 6))
        rev_date_str = rev_date.strftime('%Y-%m-%d')
        
        # Rating probabilities vary by health and whether it's in the second half for failing businesses
        is_second_half = rev_week > 26
        
        if h > 0.3:
            # Highly healthy business: mostly 4-5 stars
            rating_probs = [0.01, 0.02, 0.05, 0.27, 0.65]
        elif h > -0.2:
            # Average business
            rating_probs = [0.05, 0.08, 0.15, 0.42, 0.30]
        else:
            # Failing business: gets worse over time
            if is_second_half:
                rating_probs = [0.45, 0.25, 0.15, 0.10, 0.05] # Mostly terrible reviews
            else:
                rating_probs = [0.20, 0.22, 0.25, 0.23, 0.10]
        
        rating = int(np.random.choice([1, 2, 3, 4, 5], p=rating_probs))
        
        # Select from template
        text = random.choice(REVIEW_TEMPLATES[cat][rating])
        # Randomize review text slightly with user name/details sometimes
        if random.random() < 0.25:
            text = f"{fake.first_name()}: {text}"
            
        review_records.append({
            'business_id': bus_id,
            'rating': rating,
            'review_text': text,
            'date': rev_date_str
        })

# Convert to dataframes and save
df_upi = pd.DataFrame(upi_records)
df_social = pd.DataFrame(social_records)
df_footfall = pd.DataFrame(footfall_records)
df_reviews = pd.DataFrame(review_records)

# Introduce some random missingness in the timeseries data to test imputation
# 2% random missing values in UPI transaction volumes (simulating connection drops)
upi_vol_missing_mask = np.random.rand(len(df_upi)) < 0.02
df_upi.loc[upi_vol_missing_mask, 'transaction_volume'] = np.nan
df_upi.loc[upi_vol_missing_mask, 'avg_ticket_size'] = np.nan

# 3% random missing values in social media engagement metrics
social_er_missing_mask = np.random.rand(len(df_social)) < 0.03
df_social.loc[social_er_missing_mask, 'engagement_rate'] = np.nan

# Save CSVs
df_upi.to_csv(os.path.join(DATA_DIR, 'upi_transactions.csv'), index=False)
df_social.to_csv(os.path.join(DATA_DIR, 'social_media.csv'), index=False)
df_footfall.to_csv(os.path.join(DATA_DIR, 'footfall.csv'), index=False)
df_reviews.to_csv(os.path.join(DATA_DIR, 'reviews.csv'), index=False)

print("Generated database tables successfully:")
print(f" - Businesses: {len(df_businesses)}")
print(f" - UPI Transactions: {len(df_upi)}")
print(f" - Social Media metrics: {len(df_social)}")
print(f" - Footfall check-ins: {len(df_footfall)}")
print(f" - Reviews: {len(df_reviews)}")
