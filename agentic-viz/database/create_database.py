"""
Script to create and populate a SQLite database with random sales data.
"""
import sqlite3
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from faker import Faker
import random

# Initialize Faker
fake = Faker()

def create_database():
    """Create and populate the sales database with random data for one month."""
    # Ensure database directory exists
    os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)
    
    # Connect to SQLite database (will be created if it doesn't exist)
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sales_data.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Drop tables if they exist
    cursor.execute("DROP TABLE IF EXISTS sales")
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS customers")
    cursor.execute("DROP TABLE IF EXISTS regions")
    
    # Create tables
    cursor.execute("""
    CREATE TABLE regions (
        region_id INTEGER PRIMARY KEY,
        region_name TEXT NOT NULL,
        country TEXT NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        customer_name TEXT NOT NULL,
        email TEXT NOT NULL,
        region_id INTEGER,
        FOREIGN KEY (region_id) REFERENCES regions (region_id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE products (
        product_id INTEGER PRIMARY KEY,
        product_name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL
    )
    """)
    
    cursor.execute("""
    CREATE TABLE sales (
        sale_id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        product_id INTEGER,
        sale_date TEXT NOT NULL,
        quantity INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id),
        FOREIGN KEY (product_id) REFERENCES products (product_id)
    )
    """)
    
    # Generate regions data
    regions = [
        (1, "North America", "USA"),
        (2, "North America", "Canada"),
        (3, "Europe", "UK"),
        (4, "Europe", "Germany"),
        (5, "Asia", "Japan"),
        (6, "Asia", "India"),
        (7, "Oceania", "Australia"),
        (8, "South America", "Brazil")
    ]
    
    cursor.executemany("INSERT INTO regions VALUES (?, ?, ?)", regions)
    
    # Generate products data
    categories = ["Electronics", "Clothing", "Home Goods", "Books", "Food", "Toys"]
    products = []
    
    for i in range(1, 51):  # 50 products
        category = random.choice(categories)
        price = round(random.uniform(10.0, 1000.0), 2)
        product_name = f"{category} Item {i}"
        products.append((i, product_name, category, price))
    
    cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?)", products)
    
    # Generate customers data
    customers = []
    
    for i in range(1, 101):  # 100 customers
        region_id = random.randint(1, 8)
        customer_name = fake.name()
        email = fake.email()
        customers.append((i, customer_name, email, region_id))
    
    cursor.executemany("INSERT INTO customers VALUES (?, ?, ?, ?)", customers)
    
    # Generate sales data for one month
    sales = []
    sale_id = 1
    
    # Generate data for the last month
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    current_date = start_date
    while current_date <= end_date:
        # Generate between 5 and 20 sales per day
        num_sales = random.randint(5, 20)
        
        for _ in range(num_sales):
            customer_id = random.randint(1, 100)
            product_id = random.randint(1, 50)
            
            # Get the product price
            cursor.execute("SELECT price FROM products WHERE product_id = ?", (product_id,))
            price = cursor.fetchone()[0]
            
            quantity = random.randint(1, 10)
            total_amount = round(price * quantity, 2)
            
            # Format date as ISO format for SQLite
            sale_date = current_date.strftime("%Y-%m-%d")
            
            sales.append((sale_id, customer_id, product_id, sale_date, quantity, total_amount))
            sale_id += 1
        
        current_date += timedelta(days=1)
    
    cursor.executemany("INSERT INTO sales VALUES (?, ?, ?, ?, ?, ?)", sales)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Database created successfully at {db_path}")
    print(f"Generated {len(sales)} sales records from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

if __name__ == "__main__":
    create_database()
