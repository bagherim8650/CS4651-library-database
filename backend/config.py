import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SQL_CONNECTION_STRING = os.getenv('SQL_CONNECTION_STRING')
    
    @classmethod
    def validate(cls):
        if not cls.SQL_CONNECTION_STRING:
            raise ValueError(
                "SQL_CONNECTION_STRING environment variable not set. "
                "Copy .env.example to .env and fill in your connection string."
            )