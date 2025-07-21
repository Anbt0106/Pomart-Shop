"""
Script to create an admin user for testing the admin login
"""

from app import create_app, db
from app.models import User
import pytest

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # Tạo user admin test nếu cần
        yield client

def test_add_item(client):
    # Đăng nhập admin nếu có xác thực
    # client.post('/login', data={...})
    data = {
        'name': 'Test Product',
        'description': 'Test Description',
        'price': 100,
        'stock': 10,
        'is_active': True,
        'is_featured': False,
        'date_released': '2024-06-01',
        'collection': 'popmart'
    }
    response = client.post('/admin/product/add-item', data=data, follow_redirects=True)
    assert b'Item added successfully!' in response.data 