"""
Visualization agent for creating interactive visualizations from query results.
"""
from typing import Dict, List, Any, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json

class VisualizationAgent:
    """
    Agent for creating interactive visualizations from query results.
    """
    
    def __init__(self):
        """Initialize the visualization agent."""
        self.visualization_types = [
            "bar", "line", "scatter", "pie", "histogram", 
            "box", "violin", "heatmap", "table"
        ]
    
    def determine_visualization(self, query: str, query_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine the appropriate visualization type based on the query and data.
        
        Args:
            query: The natural language query
            query_result: The result of the SQL query execution
            
        Returns:
            Dict containing visualization specification
        """
        try:
            if not query_result.get("success", False):
                return {
                    "success": False,
                    "error": "Cannot determine visualization for failed query"
                }
            
            # Extract data from query result
            data = query_result.get("data", [])
            columns = query_result.get("columns", [])
            data_types = query_result.get("data_types", {})
            
            if not data or not columns:
                return {
                    "success": False,
                    "error": "No data available for visualization"
                }
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(data)
            
            # Default visualization type and parameters
            viz_type = "bar"
            x_column = columns[0] if columns else None
            y_columns = []
            color_column = None
            title = f"Visualization for: {query}"
            
            # Determine numeric columns for potential y-axis
            numeric_columns = [col for col in columns if col in data_types and data_types[col] in ["integer", "float"]]
            categorical_columns = [col for col in columns if col in data_types and data_types[col] == "string"]
            datetime_columns = [col for col in columns if col in data_types and data_types[col] == "datetime"]
            
            # Determine visualization type based on data and query
            if len(columns) == 1:
                # Single column visualization
                if columns[0] in numeric_columns:
                    viz_type = "histogram"
                    x_column = columns[0]
                else:
                    viz_type = "pie"
                    x_column = columns[0]
                    y_columns = ["count"]
            
            elif len(columns) >= 2:
                # Multi-column visualization
                
                # Check for time series data
                if datetime_columns and numeric_columns:
                    viz_type = "line"
                    x_column = datetime_columns[0]
                    y_columns = numeric_columns[:3]  # Limit to 3 numeric columns for clarity
                
                # Check for categorical vs numeric data
                elif categorical_columns and numeric_columns:
                    # If we have one categorical and multiple numeric columns
                    if len(categorical_columns) == 1 and len(numeric_columns) >= 1:
                        viz_type = "bar"
                        x_column = categorical_columns[0]
                        y_columns = numeric_columns[:3]  # Limit to 3 numeric columns for clarity
                    
                    # If we have multiple categorical columns and one numeric column
                    elif len(categorical_columns) >= 2 and len(numeric_columns) == 1:
                        viz_type = "heatmap"
                        x_column = categorical_columns[0]
                        y_columns = [numeric_columns[0]]
                        color_column = numeric_columns[0]
                
                # Check for multiple numeric columns
                elif len(numeric_columns) >= 2:
                    # Scatter plot for 2 numeric columns
                    viz_type = "scatter"
                    x_column = numeric_columns[0]
                    y_columns = [numeric_columns[1]]
                    if len(numeric_columns) > 2:
                        color_column = numeric_columns[2]
                
                # Default to table for complex data
                else:
                    viz_type = "table"
            
            # Check query keywords to override visualization type
            query_lower = query.lower()
            if "distribution" in query_lower or "histogram" in query_lower:
                viz_type = "histogram"
            elif "scatter" in query_lower or "correlation" in query_lower or "relationship" in query_lower:
                viz_type = "scatter"
            elif "line" in query_lower or "trend" in query_lower or "over time" in query_lower:
                viz_type = "line"
            elif "pie" in query_lower or "proportion" in query_lower or "percentage" in query_lower:
                viz_type = "pie"
            elif "box" in query_lower or "boxplot" in query_lower or "distribution" in query_lower:
                viz_type = "box"
            elif "heatmap" in query_lower or "matrix" in query_lower:
                viz_type = "heatmap"
            elif "table" in query_lower:
                viz_type = "table"
            
            # Create visualization specification
            visualization_spec = {
                "visualization_type": viz_type,
                "x_column": x_column,
                "y_columns": y_columns if y_columns else [y for y in numeric_columns[:3]] if numeric_columns else [],
                "color_column": color_column,
                "title": title,
                "data_columns": columns,
                "data_types": data_types
            }
            
            return {
                "success": True,
                "visualization_spec": visualization_spec
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error determining visualization: {str(e)}"
            }
    
    def create_visualization(self, query_result: Dict[str, Any], visualization_spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an interactive visualization based on the query result and visualization specification.
        
        Args:
            query_result: The result of the SQL query execution
            visualization_spec: The visualization specification
            
        Returns:
            Dict containing the visualization figure and metadata
        """
        try:
            # Extract data from query result
            data = query_result.get("data", [])
            
            if not data:
                return {
                    "success": False,
                    "error": "No data available for visualization"
                }
            
            # Convert to DataFrame
            df = pd.DataFrame(data)
            
            # Extract visualization parameters
            viz_type = visualization_spec.get("visualization_type", "bar")
            x_column = visualization_spec.get("x_column")
            y_columns = visualization_spec.get("y_columns", [])
            color_column = visualization_spec.get("color_column")
            title = visualization_spec.get("title", "Visualization")
            
            # Ensure we have valid columns
            if x_column and x_column not in df.columns:
                x_column = df.columns[0] if df.columns else None
            
            y_columns = [y for y in y_columns if y in df.columns]
            if not y_columns and len(df.columns) > 1:
                for col in df.columns:
                    if col != x_column and pd.api.types.is_numeric_dtype(df[col]):
                        y_columns.append(col)
                        if len(y_columns) >= 3:  # Limit to 3 numeric columns
                            break
            
            if color_column and color_column not in df.columns:
                color_column = None
            
            # Create figure based on visualization type
            fig = None
            
            if viz_type == "bar":
                if y_columns:
                    # Multi-column bar chart
                    if len(y_columns) > 1:
                        df_melted = df.melt(id_vars=[x_column], value_vars=y_columns, var_name='Category', value_name='Value')
                        fig = px.bar(df_melted, x=x_column, y='Value', color='Category', title=title,
                                    labels={x_column: x_column, 'Value': 'Value'})
                    else:
                        # Single y-column bar chart
                        fig = px.bar(df, x=x_column, y=y_columns[0], title=title,
                                    color=color_column if color_column else None)
                else:
                    # Count-based bar chart
                    fig = px.bar(df, x=x_column, title=title)
            
            elif viz_type == "line":
                if y_columns:
                    if len(y_columns) > 1:
                        df_melted = df.melt(id_vars=[x_column], value_vars=y_columns, var_name='Category', value_name='Value')
                        fig = px.line(df_melted, x=x_column, y='Value', color='Category', title=title,
                                    labels={x_column: x_column, 'Value': 'Value'})
                    else:
                        fig = px.line(df, x=x_column, y=y_columns[0], title=title,
                                    color=color_column if color_column else None)
                else:
                    fig = px.line(df, x=x_column, title=title)
            
            elif viz_type == "scatter":
                if len(y_columns) >= 1:
                    fig = px.scatter(df, x=x_column, y=y_columns[0], title=title,
                                   color=color_column if color_column else None)
                else:
                    fig = px.scatter(df, x=df.columns[0], y=df.columns[1] if len(df.columns) > 1 else df.columns[0], title=title)
            
            elif viz_type == "pie":
                if len(df) > 10:  # Limit pie chart segments
                    # Too many values, aggregate the smallest ones
                    df = df.sort_values(y_columns[0] if y_columns else df.columns[1], ascending=False)
                    top_df = df.head(9)
                    other_sum = df.iloc[9:][y_columns[0] if y_columns else df.columns[1]].sum()
                    other_row = pd.DataFrame({x_column: ["Other"], y_columns[0] if y_columns else df.columns[1]: [other_sum]})
                    df = pd.concat([top_df, other_row])
                
                fig = px.pie(df, names=x_column, values=y_columns[0] if y_columns else None, title=title)
            
            elif viz_type == "histogram":
                fig = px.histogram(df, x=x_column, title=title,
                                 color=color_column if color_column else None)
            
            elif viz_type == "box":
                if y_columns:
                    fig = px.box(df, x=x_column, y=y_columns[0], title=title,
                                color=color_column if color_column else None)
                else:
                    fig = px.box(df, x=x_column, title=title)
            
            elif viz_type == "violin":
                if y_columns:
                    fig = px.violin(df, x=x_column, y=y_columns[0], title=title,
                                   color=color_column if color_column else None)
                else:
                    fig = px.violin(df, x=x_column, title=title)
            
            elif viz_type == "heatmap":
                # For heatmap, we need to pivot the data
                if x_column and y_columns and len(y_columns) >= 1:
                    if len(df[x_column].unique()) <= 20 and len(df) > 0:  # Limit heatmap size
                        pivot_df = df.pivot_table(index=y_columns[0], columns=x_column, values=color_column if color_column else y_columns[0])
                        fig = px.imshow(pivot_df, title=title)
                    else:
                        # Fallback to table for large datasets
                        fig = go.Figure(data=[go.Table(
                            header=dict(values=list(df.columns)),
                            cells=dict(values=[df[col] for col in df.columns])
                        )])
                        fig.update_layout(title=title)
                else:
                    # Fallback to table
                    fig = go.Figure(data=[go.Table(
                        header=dict(values=list(df.columns)),
                        cells=dict(values=[df[col] for col in df.columns])
                    )])
                    fig.update_layout(title=title)
            
            elif viz_type == "table":
                fig = go.Figure(data=[go.Table(
                    header=dict(values=list(df.columns)),
                    cells=dict(values=[df[col] for col in df.columns])
                )])
                fig.update_layout(title=title)
            
            # Default to table if no visualization was created
            if fig is None:
                fig = go.Figure(data=[go.Table(
                    header=dict(values=list(df.columns)),
                    cells=dict(values=[df[col] for col in df.columns])
                )])
                fig.update_layout(title=title)
            
            # Improve layout and styling
            fig.update_layout(
                template="plotly_white",
                title={
                    'text': title,
                    'y': 0.95,
                    'x': 0.5,
                    'xanchor': 'center',
                    'yanchor': 'top'
                },
                margin=dict(l=50, r=50, t=80, b=50)
            )
            
            # Convert figure to JSON for serialization
            figure_json = json.loads(fig.to_json())
            
            return {
                "success": True,
                "figure": fig,
                "figure_json": figure_json,
                "visualization_type": viz_type,
                "title": title
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error creating visualization: {str(e)}"
            }
