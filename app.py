from flask import Flask, jsonify, request
import requests
import json
import os

app = Flask(__name__)
DB_FILE = "db.json"


def load_db():
    if not os.path.exists(DB_FILE):
        initial_data = [
            {
                "id": 1,
                "product_name": "Organic Almond Milk",
                "brands": "Silk",
                "ingredients_text": "Filtered water, almonds, cane sugar, ...",
                "price": 3.99,
                "stock": 50
            }
        ]
        with open(DB_FILE, "w") as f:
            json.dump(initial_data, f, indent=4)
        return initial_data

    with open(DB_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


def find_item_in_list(inventory, item_id):
    return next((item for item in inventory if item["id"] == item_id), None)


@app.route('/inventory', methods=['GET'])
def get_inventory():
    inventory = load_db()
    return jsonify(inventory), 200


@app.route('/inventory/<int:item_id>', methods=['GET'])
def get_item(item_id):
    inventory = load_db()
    item = find_item_in_list(inventory, item_id)
    if item:
        return jsonify(item), 200
    return jsonify({"error": f"Item with ID {item_id} not found"}), 404


@app.route('/inventory', methods=['POST'])
def add_item():
    data = request.get_json() or {}

    if 'product_name' not in data:
        return jsonify({"error": "Missing required field: product_name"}), 400

    inventory = load_db()
    new_id = max([item['id'] for item in inventory], default=0) + 1

    new_item = {
        "id": new_id,
        "product_name": str(data.get("product_name")),
        "brands": str(data.get("brands", "Unknown")),
        "ingredients_text": str(data.get("ingredients_text", "N/A")),
        "price": float(data.get("price", 0.0)),
        "stock": int(data.get("stock", 0))
    }

    inventory.append(new_item)
    save_db(inventory)

    return jsonify(new_item), 201


@app.route('/inventory/<int:item_id>', methods=['PATCH'])
def update_item(item_id):
    inventory = load_db()
    item = find_item_in_list(inventory, item_id)

    if not item:
        return jsonify({"error": f"Item with ID {item_id} not found"}), 404

    data = request.get_json() or {}

    if 'price' in data:
        item['price'] = float(data['price'])
    if 'stock' in data:
        item['stock'] = int(data['stock'])
    if 'product_name' in data:
        item['product_name'] = str(data['product_name'])
    if 'brands' in data:
        item['brands'] = str(data['brands'])

    save_db(inventory)
    return jsonify(item), 200


@app.route('/inventory/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    inventory = load_db()
    item = find_item_in_list(inventory, item_id)

    if not item:
        return jsonify({"error": f"Item with ID {item_id} not found"}), 404

    updated_inventory = [i for i in inventory if i['id'] != item_id]
    save_db(updated_inventory)

    return jsonify({"message": f"Item {item_id} successfully deleted"}), 200


@app.route('/inventory/fetch-external/<barcode>', methods=['POST'])
def fetch_external_product(barcode):
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"

    try:
        headers = {'User-Agent': 'InventoryManagementSystemLab - Python - Version 1.0'}
        response = requests.get(url, headers=headers, timeout=5)

        if response.status_code != 200:
            return jsonify({"error": "Failed to reach OpenFoodFacts"}), 502

        api_data = response.json()

        if api_data.get("status") == 1:
            product_details = api_data.get("product", {})
            client_data = request.get_json() or {}

            inventory = load_db()
            new_id = max([item['id'] for item in inventory], default=0) + 1

            new_item = {
                "id": new_id,
                "product_name": product_details.get("product_name", "Unknown External Product"),
                "brands": product_details.get("brands", "Unknown Brand"),
                "ingredients_text": product_details.get("ingredients_text", "No ingredients documented"),
                "price": float(client_data.get("price", 0.0)),
                "stock": int(client_data.get("stock", 0))
            }

            inventory.append(new_item)
            save_db(inventory)

            return jsonify({"message": "Product found and imported into local database!", "item": new_item}), 201

        return jsonify({"error": "Barcode not found on OpenFoodFacts"}), 404

    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request to OpenFoodFacts failed: {str(e)}"}), 500


if __name__ == '__main__':
    load_db()
    app.run(debug=True, port=5000)