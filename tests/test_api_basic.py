import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Set dummy env vars BEFORE importing anything to prevent startup crashes
os.environ['SUPABASE_URL'] = 'https://example.supabase.co'
os.environ['SUPABASE_SERVICE_KEY'] = 'dummy-key'
os.environ['FLASK_SECRET_KEY'] = 'test-secret'
os.environ['AZURE_STORAGE_CONNECTION_STRING'] = 'DefaultEndpointsProtocol=https;AccountName=test;AccountKey=test;EndpointSuffix=core.windows.net'
os.environ['RAZORPAY_KEY_ID'] = 'test_key'
os.environ['RAZORPAY_KEY_SECRET'] = 'test_secret'

# Add project root to sys.path to ensure imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from form_filler.api import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    """Test the /health endpoint with a successful DB connection."""
    with patch('form_filler.api.get_db_connection') as mock_db:
        # Mock connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = (1,)

        response = client.get('/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['database'] == 'connected'

def test_health_check_db_fail(client):
    """Test the /health endpoint when DB connection fails."""
    with patch('form_filler.api.get_db_connection') as mock_db:
        mock_db.side_effect = Exception("DB Error")

        response = client.get('/health')

        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'error' in data['database']
