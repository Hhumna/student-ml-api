import pytest
import os
import sys

# Add parent directory to path so we can import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'wrong'
    assert data['application'] == 'student-ml-api'
    assert data['version'] == '1.0.0'

def test_predict_endpoint_success(client):
    response = client.post('/predict', json={"value": 5})
    assert response.status_code == 200
    data = response.get_json()
    assert data['input'] == 5
    assert data['prediction'] == 10

def test_predict_endpoint_missing_value(client):
    response = client.post('/predict', json={"other": 123})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Missing 'value' in request JSON"
    
def test_predict_endpoint_empty_json(client):
    response = client.post('/predict', json={})
    assert response.status_code == 400
    
def test_predict_endpoint_invalid_type_string(client):
    response = client.post('/predict', json={"value": "5"})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "'value' must be a number"

def test_predict_endpoint_invalid_type_boolean(client):
    response = client.post('/predict', json={"value": True})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
