"""
Data query agent for executing SQL queries on the database.
"""
from typing import Dict, Any, List, Optional
import pandas as pd
from database.db_utils import db_manager

class DataQueryAgent:
    """
    Agent for executing SQL queries on the database and processing the results.
    """
    
    def __init__(self):
        """Initialize the data query agent with database manager."""
        # Database manager is already initialized in db_utils
        pass
    
    def execute_query(self, sql_query: str) -> Dict[str, Any]:
        """
        Execute a SQL query on the database.
        
        Args:
            sql_query: The SQL query to execute
            
        Returns:
            Dict containing the query results, row count, and column information
        """
        try:
            # Execute the query
            result = db_manager.execute_query(sql_query)
            
            # Extract data, columns, and row count
            data = result.get("data", [])
            columns = result.get("columns", [])
            row_count = result.get("row_count", 0)
            
            if row_count == 0:
                return {
                    "success": True,
                    "data": [],
                    "columns": columns,
                    "row_count": 0,
                    "message": "Query executed successfully but returned no results"
                }
            
            # Convert to DataFrame for easier data manipulation
            if data:
                df = pd.DataFrame(data)
                
                # Get data types for each column
                data_types = {}
                for col in df.columns:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        if all(isinstance(x, int) or x is None for x in df[col]):
                            data_types[col] = "integer"
                        else:
                            data_types[col] = "float"
                    elif pd.api.types.is_datetime64_dtype(df[col]):
                        data_types[col] = "datetime"
                    else:
                        data_types[col] = "string"
                
                # Get summary statistics for numeric columns
                summary_stats = {}
                for col in df.columns:
                    if pd.api.types.is_numeric_dtype(df[col]):
                        summary_stats[col] = {
                            "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                            "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                            "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                            "median": float(df[col].median()) if not pd.isna(df[col].median()) else None
                        }
            else:
                data_types = {}
                summary_stats = {}
            
            return {
                "success": True,
                "data": data,
                "columns": columns,
                "row_count": row_count,
                "data_types": data_types,
                "summary_stats": summary_stats
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error executing query: {str(e)}"
            }

if __name__ == "__main__":
    # Test the Data Query Agent
    agent = DataQueryAgent()
    
    # Test a simple query
    test_query = "SELECT * FROM products LIMIT 5"
    result = agent.execute_query(test_query)
    
    if result["success"]:
        print(f"Query executed successfully. Found {result['row_count']} rows.")
        print("Data sample:")
        print(result["data"][0] if result["data"] else 'No records')
    else:
        print(f"Query execution failed: {result['error']}")
