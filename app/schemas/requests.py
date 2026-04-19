from pydantic import BaseModel

class AgentRequest(BaseModel):
    user_input: str
    dry_run: bool = True
    experimental_tool_generation: bool = False
