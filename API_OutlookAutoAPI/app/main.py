from fastapi import FastAPI, File,UploadFile, requests
from pydantic import BaseModel
import base64
from pdfplumber import open as open_pdf

class ChatParams(BaseModel):
    input: str
    api_key: str = None

app = FastAPI()


@app.get("/")
def hello_world():
    return {"message": "OK"}
        
@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    # Save the uploaded file
    content = base64.b64decode(await file.read())
    print("Content: ", content)
    with open(file.filename, "wb") as buffer:
        buffer.write(content)

    # Read the contents of the PDF
    with open_pdf(file.filename) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
    print(text)
    return {"text": text}