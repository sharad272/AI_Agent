import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        
    def get_openai_key(self) -> str:
        return os.getenv('OPENAI_API_KEY', '')
    
    def get_huggingface_token(self) -> str:
        return os.getenv('HUGGINGFACE_TOKEN', '')
    
    def get_model_type(self) -> str:
        return os.getenv('MODEL_TYPE', 'huggingface')  # 'openai', 'huggingface', or 'local'
