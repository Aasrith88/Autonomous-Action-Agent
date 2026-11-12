import sqlite3
from langchain_core.tools import tool

@tool
def get_order_status(order_id: str) -> str:
    """
    Looks up the current status, item name, and price of an order in the SQLite database.
    Always call this tool FIRST when a user asks about an order or requests a refund.
    Requires the exact order_id (e.g., 'ORD-101').
    """
    print(f"\n[TOOL EXECUTION] Querying database for order: {order_id}...")
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    
    # Parameterized query implemented to prevent SQL injection vulnerabilities
    cursor.execute(
        "SELECT customer_name, item, status, price FROM orders WHERE order_id = ?", 
        (order_id,)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        customer, item, status, price = row
        return f"Order {order_id} for {customer}: Item='{item}', Status='{status}', Price=${price}"
    else:
        return f"Error: Order ID '{order_id}' was not found in the database."

@tool
def process_refund(order_id: str) -> str:
    """
    Processes a refund for an order by updating its status to 'Refunded' in the database.
    BUSINESS POLICY: Refunds are ONLY allowed if the order status is 'Processing' or 'Delivered'.
    Orders with status 'Shipped' (in transit) CANNOT be refunded.
    """
    print(f"\n[TOOL EXECUTION] Attempting to process refund for: {order_id}...")
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT status, price FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    
    if not row:
        conn.close()
        return f"Refund Failed: Order ID '{order_id}' does not exist."
        
    current_status, price = row
    
    # Hard-coded deterministic business logic prevents LLM prompt injection overrides
    if current_status == "Shipped":
        conn.close()
        return (
            f"Refund Denied: Order {order_id} is currently 'Shipped' (in transit). "
            "Per company policy, refunds cannot be issued until the package is delivered."
        )
    
    if current_status == "Refunded":
        conn.close()
        return f"Refund Denied: Order {order_id} has already been refunded."
        
    # Execute state mutation upon policy validation
    cursor.execute("UPDATE orders SET status = 'Refunded' WHERE order_id = ?", (order_id,))
    conn.commit()
    conn.close()
    
    return f"Success! Order {order_id} has been officially marked as 'Refunded' in the database. Amount refunded: ${price}."

if __name__ == "__main__":
    print("--- INITIATING DIRECT TOOL EXECUTION TESTS ---")
    print(get_order_status.invoke({"order_id": "ORD-101"}))
    print(process_refund.invoke({"order_id": "ORD-101"}))
    print(get_order_status.invoke({"order_id": "ORD-102"}))