"""
FastAPI agent for exposing the multi-agent system as a REST API.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import json

from agents.orchestrator import Orchestrator

# Initialize the FastAPI app
app = FastAPI(title="Visual Data API", description="API for transforming natural language queries into visual data")

# Add CORS middleware to allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the orchestrator
orchestrator = Orchestrator()

# Define request and response models
class QueryRequest(BaseModel):
    query: str
    reset_context: bool = False
    visualization_format: str = "d3"  # Options: "d3", "plotly", "raw"

class QueryResponse(BaseModel):
    query: str
    sql_query: str
    data: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    row_count: Optional[int] = None
    visualization_type: Optional[str] = None
    visualization_spec: Optional[Dict[str, Any]] = None
    d3_spec: Optional[Dict[str, Any]] = None
    success: bool
    error: Optional[str] = None

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Visual Data API is running",
        "docs": "/docs",
        "endpoints": [
            "/api/query",
            "/api/schema",
            "/api/health"
        ]
    }

@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a natural language query and return visualization data.
    
    Args:
        request: QueryRequest object containing the query and reset_context flag
        
    Returns:
        QueryResponse object with the results
    """
    try:
        # Reset conversation context if requested
        if request.reset_context:
            orchestrator.reset_conversation()
        
        # Process the query
        result = orchestrator.process(request.query)
        
        if not result["success"]:
            return QueryResponse(
                query=request.query,
                sql_query=result.get("sql_query", ""),
                success=False,
                error=result.get("error", "Unknown error occurred")
            )
        
        # Extract query results
        query_result = result.get("query_result", {})
        data = query_result.get("data", [])
        columns = query_result.get("columns", [])
        row_count = query_result.get("row_count", 0)
        
        # Extract visualization
        visualization = result.get("visualization", {})
        visualization_spec = result.get("visualization_spec", {})
        visualization_type = visualization_spec.get("visualization_type", "")
        
        # Create D3-compatible data format
        d3_spec = create_d3_spec(data, columns, visualization_type, visualization_spec)
        
        # Return the response
        return QueryResponse(
            query=request.query,
            sql_query=result["sql_query"],
            data=data,
            columns=columns,
            row_count=row_count,
            visualization_type=visualization_type,
            visualization_spec=visualization_spec,
            d3_spec=d3_spec,
            success=True,
            error=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def create_d3_spec(data, columns, viz_type, viz_spec):
    """
    Create a D3-compatible specification for the visualization.
    
    Args:
        data: The query result data
        columns: The column names
        viz_type: The type of visualization
        viz_spec: The visualization specification
        
    Returns:
        A D3-compatible specification
    """
    if not data or not columns:
        return None
        
    # Get visualization parameters
    x_column = viz_spec.get("x_column")
    y_columns = viz_spec.get("y_columns", [])
    color_column = viz_spec.get("color_column")
    
    # Create a base D3 spec
    d3_spec = {
        "type": viz_type,
        "data": data,
        "encoding": {
            "x": {"field": x_column, "type": "nominal" if viz_type in ["bar", "pie"] else "quantitative"},
        }
    }
    
    # Add y-axis encoding if applicable
    if y_columns and len(y_columns) > 0:
        d3_spec["encoding"]["y"] = {"field": y_columns[0], "type": "quantitative"}
    
    # Add color encoding if applicable
    if color_column:
        d3_spec["encoding"]["color"] = {"field": color_column}
    
    # Add specific configurations based on visualization type
    if viz_type == "bar":
        d3_spec["mark"] = "bar"
    elif viz_type == "line":
        d3_spec["mark"] = "line"
    elif viz_type == "scatter":
        d3_spec["mark"] = "circle"
    elif viz_type == "pie":
        d3_spec["mark"] = "arc"
    elif viz_type == "heatmap":
        d3_spec["mark"] = "rect"
    
    return d3_spec

@app.get("/api/schema")
async def get_schema():
    """Get database schema."""
    try:
        schema = orchestrator.get_schema()
        return {"schema": schema}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
