# Visual Query System

A multi-agent system using LangChain and LangGraph that transforms natural language queries into interactive visual data.

## Overview

This system uses a coordinated set of agents to process natural language queries, convert them to SQL, execute database queries, and generate interactive visualizations. The entire pipeline is exposed through a REST API and multiple user interfaces.

## Architecture

The system consists of the following components:

1. **Database Agent**: Connects to a SQLite database with random sales data.
2. **Text-to-SQL Agent**: Uses the Groq API with Gemini model to convert natural language queries into SQL commands.
3. **Data Query Agent**: Executes SQL commands on the database and retrieves results.
4. **Visualization Agent**: Transforms data into interactive charts using Plotly.
5. **API Agent**: Exposes functionality via a FastAPI REST API.
6. **User Interface Agent**: Provides multiple interfaces for testing and interacting with the system.

## Project Structure

```
visual/
├── agents/                 # Agent implementations
│   ├── __init__.py
│   ├── text_to_sql_agent.py
│   ├── data_query_agent.py
│   ├── visualization_agent.py
│   └── orchestrator.py
├── api/                    # API implementation
│   ├── __init__.py
│   └── api_agent.py
├── database/               # Database utilities
│   ├── __init__.py
│   ├── create_database.py
│   └── db_utils.py
├── frontend/               # React frontend with D3.js
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── App.js
│   │   └── index.js
│   └── package.json
├── ui/                     # Streamlit user interface
│   └── streamlit_app.py
├── .env                    # Environment variables
├── main.py                 # Main script to run the system
├── requirements.txt        # Backend dependencies
└── README.md               # Project documentation
```

## Setup and Installation

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install backend dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Install frontend dependencies:
   ```
   cd frontend
   npm install
   ```
5. Set up your environment variables in `.env`:
   ```
   GROQ_API_KEY=your_groq_api_key
   ```

## Running the System

### Option 1: Run the entire system

```
python main.py
```

This will:
1. Create the database with sample data (if it doesn't exist)
2. Start the FastAPI server
3. Start the Streamlit UI server

### Option 2: Run components separately

```
# Set up the database only
python main.py --setup-db

# Run only the API server
python main.py --api-only

# Run only the UI server
python main.py --ui-only
```

### Option 3: Run the React frontend

```
# Make sure the API server is running first
cd frontend
npm start
```

## Accessing the System

- **API**: http://localhost:8080
  - API documentation: http://localhost:8080/docs
  - Health check: http://localhost:8080/api/health
  - Schema: http://localhost:8080/api/schema
  - Query endpoint: http://localhost:8080/api/query (POST)

- **Streamlit UI**: http://localhost:8501 (Streamlit interface)

- **React Frontend**: http://localhost:3000 (React with D3.js visualizations)

## Example Queries

- "Show me total sales by product category"
- "What are the top 5 products by sales quantity?"
- "Show me sales trends over the past month"
- "Compare sales across different regions"
- "What's the average sale amount by customer region?"

## API Usage

```python
import requests

response = requests.post(
    "http://localhost:8080/api/query",
    json={"query": "Show me total sales by product category"}
)

result = response.json()
print(result["sql_query"])  # Generated SQL
print(result["data"])       # Query results
print(result["visualization_html"])  # HTML for visualization
```

## Features

- **Natural Language Processing**: Convert plain English to SQL queries
- **Context Awareness**: Handle follow-up questions by maintaining conversation context
- **Interactive Visualizations**: 
  - Generate appropriate charts based on query and data
  - Plotly visualizations in the Streamlit UI
  - D3.js visualizations in the React frontend
- **REST API**: Access all functionality programmatically
- **Multiple User Interfaces**: 
  - Streamlit UI for quick testing
  - React frontend with D3.js for production use

## React Frontend with D3.js

The React frontend provides a modern, interactive interface for the visualization system:

- **Natural Language Query Interface**: Simple text input for queries
- **Interactive D3.js Visualizations**: Dynamic, responsive visualizations
- **Data Table View**: Explore the raw data alongside visualizations
- **Database Schema Explorer**: View the database structure
- **Example Queries**: Quick-start with predefined example queries

The frontend communicates with the FastAPI backend and uses D3.js to create custom, interactive visualizations based on the query results.

### D3.js Visualization Types

The system automatically selects the most appropriate visualization type based on the data:

- **Bar Charts**: For categorical comparisons
- **Line Charts**: For time series and trends
- **Scatter Plots**: For correlation analysis
- **Pie Charts**: For part-to-whole relationships
- **Heatmaps**: For matrix data and correlations

All visualizations are interactive with hover effects, tooltips, and responsive design.

## Dependencies

- LangChain & LangGraph for agent orchestration
- Groq API with Gemini model for LLM capabilities
- FastAPI for REST API
- Streamlit for testing interface
- React and D3.js for frontend visualizations
- Plotly for Streamlit visualizations
- SQLite for database storage
- Pandas for data manipulation
