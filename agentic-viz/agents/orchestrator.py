"""
CrewAI orchestrator for coordinating the multi-agent system.
"""
from typing import Dict, List, Any, Union, Optional
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from langchain_groq import ChatGroq
import json

from agents.text_to_sql_agent import TextToSQLAgent
from agents.data_query_agent import DataQueryAgent
from agents.visualization_agent import VisualizationAgent

# Load environment variables
load_dotenv()

class Orchestrator:
    """
    Orchestrator class to coordinate the multi-agent system using CrewAI.
    This class manages the workflow between different specialized agents.
    """
    
    def __init__(self):
        """Initialize the orchestrator with CrewAI agents."""
        # Initialize LangChain agents for specialized tasks
        self.text_to_sql_agent_impl = TextToSQLAgent()
        self.data_query_agent_impl = DataQueryAgent()
        self.visualization_agent_impl = VisualizationAgent()
        
        # Initialize conversation context
        self.conversation_history = []
        
        # Initialize LLM for CrewAI agents
        self.llm = None
        if os.getenv("GROQ_API_KEY"):
            self.llm = ChatGroq(
                api_key=os.getenv("GROQ_API_KEY"),
                model_name="Llama-3.3-70B-Versatile"
            )
        
        # Create CrewAI agents if LLM is available
        if self.llm:
            self._create_crewai_agents()
    
    def _create_crewai_agents(self):
        """Create CrewAI agents for the system."""
        self.sql_agent = Agent(
            role="SQL Expert",
            goal="Convert natural language queries into accurate SQL queries",
            backstory="You are an expert in SQL with years of experience translating natural language into database queries.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        self.data_agent = Agent(
            role="Data Analyst",
            goal="Execute SQL queries and analyze the results",
            backstory="You are a skilled data analyst who can execute SQL queries and understand the resulting data.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
        
        self.viz_agent = Agent(
            role="Visualization Specialist",
            goal="Create effective data visualizations from query results",
            backstory="You are a data visualization expert who knows how to represent data in the most insightful way.",
            verbose=True,
            allow_delegation=False,
            llm=self.llm
        )
    
    def process(self, query: str) -> Dict[str, Any]:
        """
        Process a natural language query through the CrewAI workflow.
        
        Args:
            query: Natural language query from the user
            
        Returns:
            Dict containing the results of the processing pipeline or error information
        """
        # Initialize the result dictionary
        result = {
            "query": query,
            "sql_query": None,
            "query_result": None,
            "visualization_spec": None,
            "visualization": None,
            "error": None,
            "success": True
        }
        
        try:
            # Step 1: Convert natural language to SQL using our specialized agent
            sql_result = self.text_to_sql_agent_impl.generate_sql(query)
            
            if not sql_result.get("success", False):
                result["error"] = sql_result.get("error", "Error generating SQL")
                result["success"] = False
                return result
                
            result["sql_query"] = sql_result["sql_query"]
            
            # Step 2: Execute SQL query using our specialized agent
            query_result = self.data_query_agent_impl.execute_query(result["sql_query"])
            
            if not query_result.get("success", False):
                result["error"] = query_result.get("error", "Error executing query")
                result["success"] = False
                return result
            
            result["query_result"] = query_result
            
            # Step 3: Determine visualization using our specialized agent
            viz_spec_result = self.visualization_agent_impl.determine_visualization(
                query, query_result
            )
            
            if not viz_spec_result.get("success", False):
                result["error"] = viz_spec_result.get("error", "Error determining visualization")
                result["success"] = False
                return result
            
            result["visualization_spec"] = viz_spec_result["visualization_spec"]
            
            # Step 4: Create visualization using our specialized agent
            viz_result = self.visualization_agent_impl.create_visualization(
                query_result, result["visualization_spec"]
            )
            
            if not viz_result.get("success", False):
                result["error"] = viz_result.get("error", "Error creating visualization")
                result["success"] = False
                return result
            
            result["visualization"] = viz_result
            
            # Use CrewAI for additional insights if available
            if self.llm and hasattr(self, 'sql_agent'):
                try:
                    # Define tasks for the crew
                    sql_task = Task(
                        description=f"Review this SQL query for the question: '{query}'. SQL: {result['sql_query']}",
                        agent=self.sql_agent,
                        expected_output="SQL review and suggestions",
                        async_execution=False
                    )
                    
                    viz_task = Task(
                        description=f"Review this visualization for the question: '{query}' with visualization type: {result['visualization_spec'].get('visualization_type')}",
                        agent=self.viz_agent,
                        expected_output="Visualization review",
                        async_execution=False
                    )
                    
                    # Create a CrewAI crew for insights
                    crew = Crew(
                        agents=[self.sql_agent, self.viz_agent],
                        tasks=[sql_task, viz_task],
                        verbose=False,
                        process=Process.sequential
                    )
                    
                    # Run the crew asynchronously for insights
                    # We don't wait for the result as it's just for additional insights
                except Exception as crew_error:
                    # Ignore CrewAI errors as they are not critical for the main workflow
                    print(f"CrewAI error (non-critical): {str(crew_error)}")
            
            # Update conversation history
            self.update_conversation_history(query, result)
            
            return result
            
        except Exception as e:
            result["error"] = f"Error in processing pipeline: {str(e)}"
            result["success"] = False
            return result
    
    def update_conversation_history(self, query: str, result: Dict[str, Any]) -> None:
        """
        Update the conversation history with the current query and results.
        
        Args:
            query: The natural language query
            result: The result dictionary from processing
        """
        # Add the current interaction to the conversation history
        interaction = {
            "query": query,
            "sql_query": result.get("sql_query"),
            "visualization_type": result.get("visualization_spec", {}).get("visualization_type")
        }
        
        self.conversation_history.append(interaction)
        
        # Limit history to last 5 interactions to prevent context overflow
        if len(self.conversation_history) > 5:
            self.conversation_history = self.conversation_history[-5:]
    
    def get_schema(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get the database schema from the text-to-SQL agent.
        
        Returns:
            Database schema as a dictionary
        """
        return self.text_to_sql_agent_impl.schema
    
    def reset_conversation(self) -> None:
        """Reset the conversation history and agent states."""
        self.conversation_history = []
        self.text_to_sql_agent_impl.reset_conversation()

if __name__ == "__main__":
    # Test the orchestrator
    orchestrator = Orchestrator()
    result = orchestrator.process("Show me total sales by product category")
    
    if result["success"]:
        print(f"Query: {result['query']}")
        print(f"SQL: {result['sql_query']}")
        print(f"Visualization Spec: {result['visualization_spec']}")
        print("Visualization created successfully" if result["visualization"].get("success") else "Visualization failed")
    else:
        print(f"Error: {result['error']}")
