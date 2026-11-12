import sqlite3

def create_dummy_database():
    print("Initializing Enterprise Order Database (orders.db)...")
    
    conn = sqlite3.connect("orders.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            customer_name TEXT,
            item TEXT,
            status TEXT,
            price REAL
        )
    """)
    
    cursor.execute("DELETE FROM orders")
    
    test_orders = [
        ("ORD-101", "Alice Smith", "MacBook Pro", "Shipped", 1999.99),
        ("ORD-102", "Bob Jones", "iPhone 16", "Processing", 999.50),
        ("ORD-103", "Charlie Brown", "AirPods", "Delivered", 249.00)
    ]
    
    cursor.executemany("""
        INSERT INTO orders (order_id, customer_name, item, status, price)
        VALUES (?, ?, ?, ?, ?)
    """, test_orders)
    
    conn.commit()
    
    cursor.execute("SELECT * FROM orders")
    rows = cursor.fetchall()
    
    print("\n--- DATABASE RECORDS SUCCESSFULLY SEEDED ---")
    for row in rows:
        print(row)
        
    conn.close()

if __name__ == "__main__":
    create_dummy_database()