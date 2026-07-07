import pytest
import json
import os
from unittest.mock import patch
from app import app, DB_FILE


@pytest.fixture
def client():
    app.config['TESTING'] = True

    # Back up any existing db.json so the test run doesn't clobber real data
    original_data = None
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            try:
                original_data = json.load(f)
            except json.JSONDecodeError:
                pass

    mock_test_db = [
        {
            "id": 1,
            "product_name": "Test Mock Almond Milk",
            "brands": "Mock-Silk",
            "ingredients_text": "Water, sugar, organic compound elements",
            "price": 2.50,
            "stock": 10
        }
    ]
    with open(DB_FILE, 'w') as f:
        json.dump(mock_test_db, f, indent=4)

    with app.test_client() as client:
        yield client

    # Restore the original db.json (or remove the test file if there wasn't one)
    if original_data is not None:
        with open(DB_FILE, 'w') as f:
            json.dump(original_data, f, indent=4)
    elif os.path.exists(DB_FILE):
        os.remove(DB_FILE)


def test_get_all_items(client):
    res = client.get('/inventory')
    assert res.status_code == 200
    assert len(res.json) == 1
    assert res.json[0]['product_name'] == "Test Mock Almond Milk"


def test_post_valid_item(client):
    payload = {"product_name": "Test Sparking Soda", "brands": "FizzCorp", "price": 1.25, "stock": 40}
    res = client.post('/inventory', json=payload)
    assert res.status_code == 201
    assert res.json['id'] == 2
    assert res.json['product_name'] == "Test Sparking Soda"


def test_post_missing_required_field(client):
    payload = {"brands": "No Name Co", "price": 1.00}
    res = client.post('/inventory', json=payload)
    assert res.status_code == 400
    assert "error" in res.json


def test_patch_updates_item(client):
    payload = {"price": 3.15, "stock": 5}
    res = client.patch('/inventory/1', json=payload)
    assert res.status_code == 200
    assert res.json['price'] == 3.15
    assert res.json['stock'] == 5


def test_delete_item(client):
    res = client.delete('/inventory/1')
    assert res.status_code == 200

    # Item should no longer be retrievable after deletion
    check_res = client.get('/inventory/1')
    assert check_res.status_code == 404


@patch('app.requests.get')
def test_fetch_external_product(mock_get, client):
    # Mock the OpenFoodFacts call so the test doesn't depend on the network
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "status": 1,
        "product": {
            "product_name": "Mock API Juice Box",
            "brands": "Global Drinks Inc",
            "ingredients_text": "Apples, vitamin c concentration extracts"
        }
    }

    payload = {"price": 0.89, "stock": 100}
    res = client.post('/inventory/fetch-external/99999999', json=payload)
    assert res.status_code == 201
    assert res.json['item']['product_name'] == "Mock API Juice Box"
    assert res.json['item']['price'] == 0.89

    