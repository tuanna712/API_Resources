from fastapi import FastAPI
from pydantic import BaseModel
from .functions import KGSearch

class ChatParams(BaseModel):
    input: str
    api_key: str = None

app = FastAPI()


@app.get("/")
def hello_world():
    return {"message": "OK"}

@app.post("/chat/")
async def create_item(chat_input: ChatParams):
    user_input = chat_input.input
    api_key = chat_input.api_key

    KGS = KGSearch(api_key)
    kg_answer = KGS.kg_chat(user_input)
    references = KGS.node_relations

    return {"answer": kg_answer, "references": references}