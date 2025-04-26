"""
Text-to-SQL agent for converting natural language queries to SQL.
"""
from typing import Dict, List, Any, Optional
import os
import json
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from database.db_utils import db_manager

# Load environment variables
load_dotenv()

class TextToSQLAgent:
    """
    Agent for converting natural language queries to SQL queries.
    """
    
    def __init__(self):
        """Initialize the text-to-SQL agent with LLM and database schema."""
        # Get database schema
        self.schema = db_manager.get_schema()
        
        # Format schema for prompt
        self.formatted_schema = self._format_schema()
        
        # Initialize conversation history
        self.conversation_history = []
        
        # Initialize LLM
        # api_key = os.getenv("GROQ_API_KEY")
        api_key = "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"
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
            
        self.llm = ChatGroq(
            api_key=api_key,
            model_name="Llama-3.3-70B-Versatile"
        )
        
        # Define SQL generation prompt
        self.sql_prompt = PromptTemplate(
            input_variables=["schema", "query", "conversation_history"],
            template="""
            You are an expert SQL developer. Your task is to convert natural language queries into valid SQLite SQL queries.
            
            DATABASE SCHEMA:
            {schema}
            
            CONVERSATION HISTORY:
            {conversation_history}
            
            USER QUERY:
            {query}
            
            Generate a valid SQL query that answers the user's question. The query should be executable in SQLite.
            Only return the SQL query, nothing else. Do not include markdown formatting, explanations, or any text other than the SQL query itself.
            """
        )
        
        # Create LLM chain for SQL generation
        self.sql_chain = LLMChain(llm=self.llm, prompt=self.sql_prompt)
    
    def _format_schema(self) -> str:
        """Format the database schema for the prompt."""
        formatted = []
        
        for table_name, columns in self.schema.items():
            table_info = f"Table: {table_name}\nColumns:"
            
            for col in columns:
                pk_info = " (PRIMARY KEY)" if col["primary_key"] else ""
                table_info += f"\n  - {col['name']} ({col['type']}){pk_info}"
            
            # Add sample data
            try:
                samples = db_manager.get_table_sample(table_name, 3)
                if samples:
                    table_info += "\nSample data:"
                    for sample in samples[:3]:
                        table_info += f"\n  {sample}"
            except Exception:
                # Ignore errors in getting sample data
                pass
                
            formatted.append(table_info)
        
        return "\n\n".join(formatted)
    
    def generate_sql(self, query: str) -> Dict[str, Any]:
        """
        Generate SQL from natural language query.
        
        Args:
            query: Natural language query
            
        Returns:
            Dict containing the generated SQL query or error
        """
        try:
            # Format conversation history for context
            conversation_context = ""
            if self.conversation_history:
                history_items = []
                for item in self.conversation_history[-3:]:  # Last 3 interactions
                    history_items.append(f"Query: {item['query']}\nSQL: {item['sql_query']}")
                conversation_context = "\n\n".join(history_items)
            
            # Generate SQL using LLM
            sql_query = self.sql_chain.run(
                schema=self.formatted_schema,
                query=query,
                conversation_history=conversation_context
            )
            
            # Clean up the SQL query (remove markdown formatting if present)
            sql_query = sql_query.strip()
            if sql_query.startswith("```sql"):
                sql_query = sql_query[6:].strip()
            if sql_query.endswith("```"):
                sql_query = sql_query[:-3].strip()
            
            # Update conversation history
            self.conversation_history.append({
                "query": query,
                "sql_query": sql_query
            })
            
            # Limit history to prevent context overflow
            if len(self.conversation_history) > 5:
                self.conversation_history = self.conversation_history[-5:]
            
            return {
                "success": True,
                "sql_query": sql_query
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating SQL: {str(e)}"
            }
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []

if __name__ == "__main__":
    # Test the agent
    agent = TextToSQLAgent()
    result = agent.generate_sql("Show me total sales by product category")
    
    if result["success"]:
        print(f"Generated SQL: {result['sql_query']}")
    else:
        print(f"Error: {result['error']}")
