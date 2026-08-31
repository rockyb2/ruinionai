from smolagents import CodeAgent, LiteLLMModel 
from tools import BuildWord , BuildPDF
from prompt import PROMPT_SYSTEM
import os




api_key= os.getenv("MISTRAL_API_KEY")


def create_agent(model_id):
    model = LiteLLMModel(model_id=model_id, api_key=api_key)
    agent = CodeAgent(
        model=model,
        tools=[
            
            BuildWord(),
            BuildPDF()
        ],
        instructions=PROMPT_SYSTEM,
    )
    
    return agent