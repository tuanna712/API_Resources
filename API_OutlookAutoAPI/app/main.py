import os
from .myopenai import MyOAI, check_alive_openai_key
from fastapi import FastAPI, File, UploadFile, requests, Form
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
async def upload_pdf(file: UploadFile = File(...), openai_key: str = Form(...)):
    print("OpenAI key: ", openai_key)
    os.environ['OPENAI_API_KEY'] = openai_key
    alive_oai_key = check_alive_openai_key()
    
    ## Save the uploaded file
    content = base64.b64decode(await file.read())
    print("Content: ", content[:50])
    with open(file.filename, "wb") as buffer:
        buffer.write(content)
    
    _file_name = file.filename.split(".")[0]

    if not alive_oai_key:
        text = "Something wrong with your OpenAI API key!!!"
        print(text)
    else:
        print('OpenAI key works fine...')
        try:
            if file.filename.endswith("pdf"):
                # Read the contents of the PDF
                print("processing pdf...")
                text = handle_pdf(file.filename)
                
            elif file.filename.endswith(("xlsx", "xls")):
                print("processing excel...")
                text = handle_excel(file.filename)
        except Exception as e:
            print(e)
            return {"error": str(e)}
    try:
        print("Email content: " + text)
        ## Start sending the mail
        username = os.environ["username"]
        password = os.environ["password"]
        # target = os.environ["target"]
        target = ["quytx.epc@vpi.pvn.vn", "huydd@vpi.pvn.vn", "diemptt@vpi.pvn.vn", "thuannt@vpi.pvn.vn", "tungld@vpi.pvn.vn"]
        message = EmailMessage()
        message["From"] = username
        # message["To"] = target
        message["Subject"] = f"Daily report summarization {_file_name} "
        message.set_content(f"{text}")

        message.add_attachment(content, maintype='application', subtype=file.content_type.split('/')[1], filename=file.filename)

        await aiosmtplib.send(message, recipients=target, hostname="smtp-mail.outlook.com", port=587, username = username, password = password)
        print("MAIL SENT")

        # Remove file after processing
        os.remove(file.filename)
        print(f"File {file.filename} removed!")

        return {"result": "Done"}
    except Exception as e:
        print(e)
        return {"error": str(e)}

