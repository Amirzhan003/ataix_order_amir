import json
import requests
 
 API_BASE_URL = "https://api.ataix.kz"
 API_KEY = "YOUR_KEY"
 ORDERS_FILE = "orders.json" 
 
 def load_orders():
     try:
         with open(ORDERS_FILE, "r") as f:
             return json.load(f)
     except FileNotFoundError:
         print(f"Error: The file {ORDERS_FILE} does not exist.")
         return []
 
 def save_orders(data):
     try:
         with open(ORDERS_FILE, "r", encoding="utf-8") as f:
             existing_orders = json.load(f)
     except (FileNotFoundError, json.JSONDecodeError):
         existing_orders = []
 
     orders_by_id = {}
 
     for order in existing_orders:
         order_id = order.get("orderID")
         if order_id:
             orders_by_id[order_id] = order
 
     for order in data:
         order_id = order.get("orderID")
         if order_id:
             orders_by_id[order_id] = order
 
     with open(ORDERS_FILE, "w", encoding="utf-8") as f:
         json.dump(list(orders_by_id.values()), f, indent=4, ensure_ascii=False)
 
     print("Orders updated in file.")
 
 def send_request(endpoint, method="GET", data=None):
     url = f"{API_BASE_URL}{endpoint}"
     headers = {
         "accept": "application/json",
         "X-API-Key": API_KEY
     }
     print(f"Sending {method} request to {url} with data: {data}")
     response = requests.request(method, url, json=data, headers=headers)
     
     if response.ok:
         print(f"Response received: {response.json()}")
         print(f" ")
         return response.json()
     else:
         print(f"Request failed with status code {response.status_code}: {response.text}")
         return None
 
 def update_orders():
     orders = load_orders()
     if not orders:
         print("No orders found.")
         return
 
     not_filled = []
     updated_orders = {}
 
     for order in orders:
         order_id = order.get("orderID")
         if not order_id:
             continue
 
         if order.get("status") in ("cancelled", "filled"):
             updated_orders[order_id] = order
             continue
 
         print(f"Checking order {order_id}...")
         order_status = send_request(f"/api/orders/{order_id}")
 
         if order_status and isinstance(order_status, dict):
             status = "true" if order_status.get("status") else "false"
 
             if "filled" in status:
                 print(f"Order {order_id} is filled.")
                 order["status"] = "filled"
                 updated_orders[order_id] = order
 
             else:
                 print(f"Order {order_id} is not filled. Cancelling...")
                 cancel_response = send_request(f"/api/orders/{order_id}", method="DELETE")
 
                 if cancel_response:
                     print(f"Order {order_id} cancelled.")
                     order["status"] = "cancelled"
                     updated_orders[order_id] = order
                     not_filled.append(order)
                 else:
                     print(f"Failed to cancel order {order_id}.")
                     updated_orders[order_id] = order
         else:
             print(f"Invalid response for order {order_id}")
             updated_orders[order_id] = order
 
     new_orders = []
     for order in not_filled:
         new_price = round(float(order["price"]) * 1.01, 2)
         print(f"Creating new order at {new_price} for {order['symbol']}...")
         new_order = send_request("/api/orders", method="POST", data={
             "symbol": order["symbol"],
             "price": new_price,
             "side": order.get("side", "buy"),
             "type": "limit",
             "quantity": order.get("quantity", 1)
         })
 
         if new_order and new_order.get("status") and "result" in new_order:
             result = new_order["result"]
             new_orders.append(result)
             updated_orders[result["orderID"]] = result
         else:
             print("Error creating new order:", new_order)
 
     save_orders(list(updated_orders.values()))
 
     
 if __name__ == "__main__":
     update_orders()
