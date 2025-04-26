"""
Database utility functions for connecting to and querying the SQLite database.
"""
import os
import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional

class DatabaseManager:
    def __init__(self, db_path: Optional[str] = None):
        """Initialize database manager with path to SQLite database."""
        if db_path is None:
            self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sales_data.db")
        else:
            self.db_path = db_path
            
    def get_connection(self):
        """Get a connection to the SQLite database."""
        return sqlite3.connect(self.db_path)
    
    def execute_query(self, query: str, params: tuple = ()) -> Dict[str, Any]:
        """Execute SQL query and return results as a dictionary with data, columns, and row_count."""
        conn = self.get_connection()
        try:
            # Execute query and fetch results
            df = pd.read_sql_query(query, conn, params=params)
            
            # Convert DataFrame to list of dictionaries
            records = df.to_dict(orient="records")
            
            # Return a dictionary with data, columns, and row_count
            return {
                "data": records,
                "columns": list(df.columns),
                "row_count": len(records)
            }
        except Exception as e:
            print(f"Error executing query: {e}")
            raise
        finally:
            conn.close()
    
    def get_schema(self) -> Dict[str, List[Dict[str, str]]]:
        """Get database schema information."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        schema = {}
        for table in tables:
            table_name = table[0]
            # Get column information for each table
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Format column information
            schema[table_name] = [
                {
                    "name": col[1],
                    "type": col[2],
                    "primary_key": bool(col[5])
                }
                for col in columns
            ]
        
        conn.close()
        return schema
    
    def get_table_sample(self, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample data from a table."""
        query = f"SELECT * FROM {table_name} LIMIT {limit}"
        result = self.execute_query(query)
        return result["data"]

# Create a default instance
db_manager = DatabaseManager()

if __name__ == "__main__":
    # Test database connection and schema retrieval
    schema = db_manager.get_schema()
    print("Database Schema:")
    for table, columns in schema.items():
        print(f"\nTable: {table}")
        for col in columns:
            pk = " (PK)" if col["primary_key"] else ""
            print(f"  - {col['name']} ({col['type']}){pk}")
        
        # Print sample data
        print("\nSample data:")
        samples = db_manager.get_table_sample(table)
        for sample in samples:
            print(f"  {sample}")
