import os

from fastapi import FastAPI, File,UploadFile, requests
from pydantic import BaseModel
import base64
from pdfplumber import open as open_pdf
import pandas as pd

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
        print("Content: ", content)
        with open(file.filename, "wb") as buffer:
            buffer.write(content)

        if file.filename.endswith("pdf"):
            # Read the contents of the PDF
            with open_pdf(file.filename) as pdf:
                text = ""
                for page in pdf.pages[:min(3, len(pdf.pages))]:
                    text += page.extract_text()

        elif file.filename.endswith(("xlsx", "xls")):
            dataframe = pd.read_excel(file.filename)
            text = dataframe[:min(5, len(dataframe))].to_string()
        
        ## Start sending the mail
        username = os.environ["username"]
        password = os.environ["password"]
        message = EmailMessage()
        message["From"] = username
        message["To"] = "metalwallcrusher@gmail.com"
        message["Subject"] = f"File received from mail: {file.filename}"
        message.set_content(f"File content: \n {text}")

        await aiosmtplib.send(message, hostname="smtp-mail.outlook.com", port=587, username = username, password = password)
        return {"result": "Done"}
    except Exception as e:
        return {"error": str(e)}

