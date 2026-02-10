import json
import logging
from groq import Groq
from typing import Dict, List
from .config import Config
from .rag_engine import RAGEngine

logging.basicConfig(
    filename=Config.LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TaskProcessor:
    def __init__(self, rag_engine):
        if rag_engine is None:
            raise ValueError("TaskProcessor requires a RAGEngine instance")
        self.rag_engine = rag_engine
        self.groq_client = Groq(api_key=Config.GROQ_API_KEY)
        
    def parse_request(self, message: str) -> Dict:
        """Extract structured task information from natural language"""
        try:
            logging.info(f"Parsing request: {message}")
            
            response = self.groq_client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """Extract task details from the user request and return ONLY valid JSON.
                        Required fields: title, priority (low/medium/high), category, deadline_hint.
                        Categories: equipment_purchase, software_subscription, travel_booking, meeting_scheduling, document_request, general.
                        Return format: {"title": "...", "priority": "...", "category": "...", "deadline_hint": "..."}"""
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            parsed = json.loads(response.choices[0].message.content)
            logging.info(f"Parsed task: {parsed}")
            
            return parsed
            
        except Exception as e:
            logging.error(f"Error parsing request: {str(e)}")
            return {
                "title": message[:100],
                "priority": "medium",
                "category": "general",
                "deadline_hint": "not specified"
            }
    
    def enrich_with_sop(self, parsed_task: Dict) -> str:
        """Generate enriched task description with SOP guidelines"""
        try:
            logging.info(f"Enriching task with SOP for category: {parsed_task['category']}")
            
            query = f"{parsed_task['category']} {parsed_task['title']}"
            sop_chunks = self.rag_engine.query(query, n_results=3)
            
            if not sop_chunks:
                logging.warning("No SOP chunks found, proceeding without enrichment")
                return parsed_task['title']
            
            sop_context = "\n\n".join(sop_chunks)
            
            response = self.groq_client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are an assistant that creates task descriptions with SOP reminders.
                        Given a task and relevant SOP context, create a clear description that includes:
                        1. The main task
                        2. Relevant SOP guidelines (bullet points)
                        Keep it concise and actionable."""
                    },
                    {
                        "role": "user",
                        "content": f"""Task: {parsed_task['title']}
                        
SOP Context:
{sop_context}

Create a task description with SOP reminders."""
                    }
                ],
                temperature=0.2
            )
            
            enriched_description = response.choices[0].message.content
            logging.info("Task enriched with SOP guidelines")
            
            return enriched_description
            
        except Exception as e:
            logging.error(f"Error enriching task: {str(e)}")
            return parsed_task['title']
    
    def answer_question(self, question: str) -> str:
        """Answer SOP-related questions using RAG"""
        try:
            logging.info(f"Answering question: {question}")
            
            sop_chunks = self.rag_engine.query(question, n_results=3)
            
            if not sop_chunks:
                return "I could not find relevant information in the SOP documents."
            
            sop_context = "\n\n".join(sop_chunks)
            
            response = self.groq_client.chat.completions.create(
                model=Config.GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a helpful assistant that answers questions based on SOP documentation.
                        Use only the provided context to answer. Be concise and cite the SOP section when possible.
                        If the answer is not in the context, say so."""
                    },
                    {
                        "role": "user",
                        "content": f"""Question: {question}
                        
SOP Context:
{sop_context}

Answer the question based on the SOP context."""
                    }
                ],
                temperature=0.1
            )
            
            answer = response.choices[0].message.content
            logging.info("Question answered successfully")
            
            return answer
            
        except Exception as e:
            logging.error(f"Error answering question: {str(e)}")
            return "An error occurred while processing your question."