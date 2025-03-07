from fastapi import FastAPI
from pydantic import BaseModel
from .functions import SK_TCDK

class ChatParams(BaseModel):
    input: str
    api_key: str = None
    mode: str

app = FastAPI()


@app.get("/")
def hello_world():
    return {"message": "OK"}

@app.post("/chat/")
async def create_item(chat_input: ChatParams):
    user_input = chat_input.input
    api_key = chat_input.api_key
    mode = chat_input.mode

    response = await SK_TCDK(api_key).chat(user_input, mode)
    print(response)

    return {"answer": str(response)}
