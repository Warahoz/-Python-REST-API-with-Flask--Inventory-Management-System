import requests
import sys

BASE_URL = "http://127.0.0.1:5000/inventory"

def print_menu():
    print("\n" + "="*40)
    print("      INVENTORY MANAGEMENT SYSTEM")
    print("="*40)
    print("1. View All Inventory")
    print("2. Search Item by ID")
    print("3. Add New Item")
    print("4. Import via Barcode (OpenFoodFacts)")
    print("5. Update Price/Stock")
    print("6. Delete Item")
    print("7. Exit")
    print("="*40)

def view_all():
    try:
        res = requests.get(BASE_URL)
        if res.status_code == 200:
            items = res.json()
            if not items:
                print("\n[!] Inventory is empty.")
                return
            print(f"\n{'ID':<5} | {'Product Name':<30} | {'Brand':<15} | {'Price':<8} | {'Stock':<6}")
            print("-" * 75)
            for i in items:
                print(f"{i['id']:<5} | {i['product_name'][:30]:<30} | {i['brands'][:15]:<15} | ${i['price']:<7.2f} | {i['stock']:<6}")
        else:
            print("[!] Error loading inventory data.")
    except requests.exceptions.ConnectionError:
        print("[!] Connection error: is the Flask app running?")

def view_single():
    item_id = input("\nEnter Item ID: ").strip()
    if not item_id.isdigit():
        print("[!] ID must be a number.")
        return
    try:
        res = requests.get(f"{BASE_URL}/{item_id}")
        if res.status_code == 200:
            item = res.json()
            print("\n--- Item Details ---")
            print(f"ID: {item['id']}")
            print(f"Name: {item['product_name']}")
            print(f"Brand: {item['brands']}")
            print(f"Price: ${item['price']:.2f}")
            print(f"Stock: {item['stock']} units")
            print(f"Ingredients: {item['ingredients_text']}")
        else:
            print(f"[!] {res.json().get('error')}")
    except requests.exceptions.ConnectionError:
        print("[!] Connection error: is the Flask app running?")

def add_custom():
    print("\n--- Add New Item ---")
    name = input("Product Name: ").strip()
    if not name:
        print("[!] Product name cannot be empty.")
        return
    brand = input("Brand: ").strip() or "Unknown"

    try:
        price = float(input("Price ($): ") or 0.0)
        stock = int(input("Stock Count: ") or 0)
    except ValueError:
        print("[!] Price must be a number and stock must be an integer.")
        return

    payload = {"product_name": name, "brands": brand, "price": price, "stock": stock}
    try:
        res = requests.post(BASE_URL, json=payload)
        if res.status_code == 201:
            print(f"\n[+] Item created with ID: {res.json()['id']}")
        else:
            print("[!] Failed to create item.")
    except requests.exceptions.ConnectionError:
        print("[!] Connection error: is the Flask app running?")

def import_barcode():
    print("\n--- Import from OpenFoodFacts ---")
    barcode = input("Barcode: ").strip()
    if not barcode:
        print("[!] Barcode is required.")
        return

    try:
        price = float(input("Price ($): ") or 0.0)
        stock = int(input("Stock Count: ") or 0)
    except ValueError:
        print("[!] Price must be a number and stock must be an integer.")
        return

    payload = {"price": price, "stock": stock}
    print("[*] Looking up barcode on OpenFoodFacts...")

    try:
        res = requests.post(f"{BASE_URL}/fetch-external/{barcode}", json=payload)
        if res.status_code == 201:
            data = res.json()
            print(f"\n[+] Imported: {data['item']['product_name']} (ID: {data['item']['id']})")
        else:
            print(f"[!] {res.json().get('error', 'Import failed')}")
    except requests.exceptions.ConnectionError:
        print("[!] Connection error: is the Flask app running?")

def update_item():
    item_id = input("\nEnter Item ID to update: ").strip()
    if not item_id.isdigit():
        print("[!] ID must be a number.")
        return

    print("Leave a field blank to keep its current value.")
    price_input = input("New Price ($): ").strip()
    stock_input = input("New Stock Count: ").strip()

    payload = {}
    try:
        if price_input: payload['price'] = float(price_input)
        if stock_input: payload['stock'] = int(stock_input)
    except ValueError:
        print("[!] Price must be a number and stock must be an integer.")
        return

    if not payload:
        print("[*] Nothing to update.")
        return

    try:
        res = requests.patch(f"{BASE_URL}/{item_id}", json=payload)
        if res.status_code == 200:
            print("[+] Item updated.")
        else:
            print(f"[!] {res.json().get('error')}")
    except requests.exceptions.ConnectionError:
        print("[!] Connection error: is the Flask app running?")

def delete_item():
    item_id = input("\nEnter Item ID to delete: ").strip()
    if not item_id.isdigit():
        print("[!] ID must be a number.")
        return
    try:
        res = requests.delete(f"{BASE_URL}/{item_id}")
        if res.status_code == 200:
            print(f"[+] Item {item_id} deleted.")
        else:
            print(f"[!] {res.json().get('error')}")
    except requests.exceptions.ConnectionError:
        print("[!] Connection error: is the Flask app running?")

def main():
    while True:
        print_menu()
        choice = input("Enter Command (1-7): ").strip()
        if choice == '1': view_all()
        elif choice == '2': view_single()
        elif choice == '3': add_custom()
        elif choice == '4': import_barcode()
        elif choice == '5': update_item()
        elif choice == '6': delete_item()
        elif choice == '7':
            print("\nGoodbye.")
            sys.exit()
        else:
            print("[!] Invalid choice.")

if __name__ == '__main__':
    main()