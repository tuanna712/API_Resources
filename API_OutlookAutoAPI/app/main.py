import os

from fastapi import FastAPI, File,UploadFile, requests
from pydantic import BaseModel
import base64

from .handle_excel import handle_excel
from .handle_pdf import handle_pdf

import aiosmtplib
from email.message import EmailMessage


class ChatParams(BaseModel):
    input: str
    api_key: str = None

app = FastAPI()


@app.get("/")
def hello_world():
    return {"message": "OK"}
        
@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        ## Save the uploaded file
        content = base64.b64decode(await file.read())
        print("Content: ", content[:50])
        with open(file.filename, "wb") as buffer:
            buffer.write(content)

        if file.filename.endswith("pdf"):
            # Read the contents of the PDF
            print("processing pdf...")
            text = handle_pdf(file.filename)
            
            

        elif file.filename.endswith(("xlsx", "xls")):
            print("processing excel...")
            text = handle_excel(file.filename)
            
        print("Email content: " + text)
        ## Start sending the mail
        username = os.environ["username"]
        password = os.environ["password"]
        target = os.environ["target"]
        message = EmailMessage()
        message["From"] = username
        message["To"] = target
        message["Subject"] = f"Daily report summarization."
        message.set_content(f"{text}")


        await aiosmtplib.send(message, recipients=target, hostname="smtp-mail.outlook.com", port=587, username = username, password = password)
        print("MAIL SENT")
        return {"result": "Done"}
    except Exception as e:
        return {"error": str(e)}

