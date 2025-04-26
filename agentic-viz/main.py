"""
Main script to run the entire multi-agent system.
"""
import os
import argparse
import subprocess
import time
import sys
from pathlib import Path

def setup_database():
    """Set up the database with sample data."""
    print("Setting up database...")
    try:
        from database.create_database import create_database
        create_database()
        print("Database setup complete.")
    except Exception as e:
        print(f"Error setting up database: {e}")
        sys.exit(1)

def start_api_server():
    """Start the FastAPI server in a subprocess."""
    print("Starting API server...")
    api_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "api.api_agent:app", "--host", "0.0.0.0", "--port", "8080"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    # Give the server a moment to start
    time.sleep(2)
    return api_process

def start_ui_server():
    """Start the Streamlit UI server in a subprocess."""
    print("Starting Streamlit UI server...")
    ui_process = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "ui/streamlit_app.py"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    return ui_process

def main():
    """Main function to run the system."""
    parser = argparse.ArgumentParser(description="Run the Visual Query System")
    parser.add_argument("--setup-db", action="store_true", help="Set up the database with sample data")
    parser.add_argument("--api-only", action="store_true", help="Run only the API server")
    parser.add_argument("--ui-only", action="store_true", help="Run only the UI server")
    
    args = parser.parse_args()
    
    # Check if database exists, create if it doesn't or if explicitly requested
    db_path = Path(__file__).parent / "database" / "sales_data.db"
    if not db_path.exists() or args.setup_db:
        setup_database()
    
    processes = []
    
    # Start API server if requested or if running both
    if not args.ui_only:
        api_process = start_api_server()
        processes.append(api_process)
        print("API server running at http://localhost:8080")
        print("API documentation available at http://localhost:8080/docs")
    
    # Start UI server if requested or if running both
    if not args.api_only:
        ui_process = start_ui_server()
        processes.append(ui_process)
        print("Streamlit UI running. Check the console output for the URL (typically http://localhost:8501)")
    
    print("\nPress Ctrl+C to stop the servers...")
    
    try:
        # Keep the main process running
        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        for process in processes:
            process.terminate()
        print("Servers stopped.")

if __name__ == "__main__":
    main()
