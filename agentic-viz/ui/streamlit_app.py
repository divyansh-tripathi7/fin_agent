"""
Streamlit User Interface Agent for the multi-agent system.
"""
import streamlit as st
import requests
import pandas as pd
import json
import plotly.io as pio
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set page config
st.set_page_config(
    page_title="Visual Query System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define API URL
API_URL = "http://localhost:8080/api"

def query_api(query, reset_context=False):
    """Query the API with a natural language query."""
    try:
        response = requests.post(
            f"{API_URL}/query",
            json={"query": query, "reset_context": reset_context},
            timeout=60
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None

def get_schema():
    """Get the database schema from the API."""
    try:
        response = requests.get(f"{API_URL}/schema", timeout=10)
        response.raise_for_status()
        return response.json().get("schema", {})
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching schema: {str(e)}")
        return {}

def display_schema(schema):
    """Display the database schema in the sidebar."""
    st.sidebar.header("Database Schema")
    
    for table, columns in schema.items():
        with st.sidebar.expander(f"Table: {table}"):
            cols = []
            types = []
            keys = []
            
            for col in columns:
                cols.append(col["name"])
                types.append(col["type"])
                keys.append("🔑" if col["primary_key"] else "")
            
            df = pd.DataFrame({
                "Column": cols,
                "Type": types,
                "PK": keys
            })
            
            st.dataframe(df, hide_index=True)

def main():
    """Main Streamlit application."""
    st.title("🔍 Visual Query System")
    st.subheader("Transform natural language queries into interactive visual data")
    
    # Get schema for the sidebar
    schema = get_schema()
    if schema:
        display_schema(schema)
    
    # Example queries
    st.sidebar.header("Example Queries")
    example_queries = [
        "Show me total sales by product category",
        "What are the top 5 products by sales quantity?",
        "Show me sales trends over the past month",
        "Compare sales across different regions",
        "What's the average sale amount by customer region?"
    ]
    
    for query in example_queries:
        if st.sidebar.button(query):
            st.session_state.query = query
            process_query(query)
    
    # Reset context button
    if st.sidebar.button("Reset Conversation Context"):
        st.session_state.conversation_history = []
        st.success("Conversation context has been reset!")
    
    # Initialize session state for conversation history
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    # Query input
    query = st.text_input("Enter your query:", key="query", help="Ask a question about the sales data")
    col1, col2 = st.columns([1, 5])
    with col1:
        submit = st.button("Submit")
    with col2:
        reset_context = st.checkbox("Reset context for this query", value=False)
    
    if submit and query:
        process_query(query, reset_context)

def process_query(query, reset_context=False):
    """Process a query and display results."""
    with st.spinner("Processing your query..."):
        # Call the API
        result = query_api(query, reset_context)
        
        if not result:
            return
        
        # Add to conversation history
        st.session_state.conversation_history.append({"query": query, "result": result})
        
        # Display results
        display_results(result)

def display_results(result):
    """Display the results of a query."""
    # Check for errors
    if result.get("error"):
        st.error(f"Error: {result['error']}")
        return
    
    # Display tabs for different views
    tab1, tab2, tab3 = st.tabs(["Visualization", "Data", "SQL Query"])
    
    with tab1:
        # Display visualization
        st.subheader("Visualization")
        if result.get("visualization_html"):
            # Use the HTML representation
            st.components.v1.html(result["visualization_html"], height=500)
        elif result.get("visualization_json"):
            # Use the JSON representation
            fig = go.Figure(result["visualization_json"])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No visualization available for this query.")
    
    with tab2:
        # Display data
        st.subheader("Query Results")
        if result.get("data"):
            df = pd.DataFrame(result["data"])
            st.dataframe(df, use_container_width=True)
            st.caption(f"Showing {result.get('row_count', len(result['data']))} records")
        else:
            st.info("No data available for this query.")
    
    with tab3:
        # Display SQL query
        st.subheader("Generated SQL Query")
        if result.get("sql_query"):
            st.code(result["sql_query"], language="sql")
        else:
            st.info("No SQL query was generated.")

if __name__ == "__main__":
    main()
