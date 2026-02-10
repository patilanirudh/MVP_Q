import logging
from todoist_api_python.api import TodoistAPI
from typing import Dict
from .config import Config

logging.basicConfig(
    filename=Config.LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class TodoistClient:
    def __init__(self):
        self.api = TodoistAPI(Config.TODOIST_API_KEY)
        self.priority_map = {
            "low": 1,
            "medium": 2,
            "high": 3,
            "urgent": 4
        }
    
    def create_task(self, parsed_task: Dict, description: str) -> Dict:
        """Create task in Todoist with enriched description"""
        try:
            logging.info(f"Creating Todoist task: {parsed_task['title']}")
            
            priority = self.priority_map.get(parsed_task.get('priority', 'medium'), 2)
            
            task = self.api.add_task(
                content=parsed_task['title'],
                description=description,
                priority=priority
            )
            
            logging.info(f"Task created successfully: ID {task.id}")
            
            return {
                "id": task.id,
                "url": task.url,
                "content": task.content,
                "priority": priority
            }
            
        except Exception as e:
            logging.error(f"Error creating Todoist task: {str(e)}")
            raise