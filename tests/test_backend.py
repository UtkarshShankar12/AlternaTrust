import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add project directories to path
OS_WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(OS_WORKSPACE_DIR, 'backend')
MODELS_DIR = os.path.join(OS_WORKSPACE_DIR, 'models')

if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)
if MODELS_DIR not in sys.path:
    sys.path.append(MODELS_DIR)

# Import app AFTER paths are patched
from main import app, get_feature_description

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c

def test_get_businesses(client):
    """Verify get businesses endpoint returns valid scored portfolio items."""
    response = client.get("/businesses")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert "business_id" in data[0]
    assert "credit_score" in data[0]
    assert "risk_tier" in data[0]

def test_get_business_history(client):
    """Verify retrieving detailed history logs for a single business works."""
    # Test valid business
    response = client.get("/business/BUS_0001/history")
    assert response.status_code == 200
    data = response.json()
    assert "metadata" in data
    assert "upi_history" in data
    assert "reviews" in data
    assert data["metadata"]["business_id"] == "BUS_0001"
    
    # Test invalid business returns 404
    response = client.get("/business/BUS_9999/history")
    assert response.status_code == 404

def test_score_endpoint(client):
    """Verify that posting real-time raw streams correctly runs ML scoring pipeline."""
    payload = {
        "business": {
            "business_id": "BUS_TEST",
            "business_name": "Test Underwrite Gym",
            "owner_name": "Rahul Dev",
            "category": "Gym",
            "city": "Delhi",
            "years_in_operation": 2.5
        },
        "upi_transactions": [
            {
                "business_id": "BUS_TEST",
                "week_start_date": "2026-07-05",
                "transaction_count": 35,
                "transaction_volume": 55000.0,
                "avg_ticket_size": 1570.0
            },
            {
                "business_id": "BUS_TEST",
                "week_start_date": "2026-07-12",
                "transaction_count": 38,
                "transaction_volume": 59700.0,
                "avg_ticket_size": 1570.0
            }
        ],
        "social_media": [
            {
                "business_id": "BUS_TEST",
                "week_start_date": "2026-07-12",
                "follower_count": 950,
                "engagement_rate": 0.045,
                "posts_count": 3
            }
        ],
        "footfall": [
            {
                "business_id": "BUS_TEST",
                "week_start_date": "2026-07-12",
                "check_ins": 95,
                "popular_hours_profile": "[0.03,0.08,0.12,0.09,0.04,0.02,0.01,0.01,0.02,0.02,0.02,0.02,0.02,0.01,0.02,0.04,0.1,0.15,0.12,0.06,0.03,0.01,0.01,0.01]"
            }
        ],
        "reviews": [
            {
                "business_id": "BUS_TEST",
                "rating": 5,
                "review_text": "Excellent equipment, trainers are highly professional and the gym floor is clean.",
                "date": "2026-07-10"
            }
        ]
    }
    
    response = client.post("/score", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "credit_score" in data
    assert "risk_tier" in data
    assert "top_factors" in data
    assert len(data["top_factors"]) == 5
    assert data["business_id"] == "BUS_TEST"

def test_feature_descriptions():
    """Verify that feature names map cleanly to descriptive plain-English labels."""
    desc = get_feature_description("upi_vol_cv")
    assert "Cash Flow Volatility" in desc
    
    desc_tfidf = get_feature_description("tfidf_clean")
    assert "Keyword: 'Clean'" in desc_tfidf
