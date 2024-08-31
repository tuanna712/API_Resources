import neo4j
from qdrant_client import QdrantClient
from typing import Any, Dict, List, Optional

# QDRANT DB TRIGGERS ==============================================================================
qdrant_adress = [
    {"email":"muito1712@gmail.com",
    "qdrant_url":"https://bd26be9e-256b-4c84-85b3-2588bfdd284e.us-east-1-0.aws.cloud.qdrant.io:6333", 
    "qdrant_api_key":"qozq2_b5cqx0CI_EuDDWDUrTSEozbkQgCKplto5hlssNa064wwNKjg"},
]

def get_collections_information(qdrant_url, qdrant_api_key):
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    collections = client.get_collections()
    if len (collections.collections) == 0:
        print ("No collections found")
    else:
        print ("Collections found:")
        for collection in collections.collections:
            print (collection.name)

qdrant_email_content = """\n\n
### QDRANT TRIGGER ###

"""
for i in range (len(qdrant_adress)):
    try:
        print ("Qdrant adress: ", qdrant_adress[i]["qdrant_url"])
        get_collections_information(qdrant_adress[i]["qdrant_url"], qdrant_adress[i]["qdrant_api_key"])
        print ("-----------------------")
        _text = f"## Email: {qdrant_adress[i]['email']}\n## Status: Success"
        qdrant_email_content += _text
    except Exception as e:
        _text = f"## Email: {qdrant_adress[i]['email']}\n## Status: {e}"
        qdrant_email_content += _text



# NEO4J DB TRIGGERS ==============================================================================
class Neo4jGraph():
    def __init__(
        self,
        url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:

        self._driver = neo4j.GraphDatabase.driver(url, auth=(username, password))
        self._database = "neo4j"
        self.status = None
        try:
            self._driver.verify_connectivity()
            self.status = 'running'
        except Exception as error:
            self.status = error

    def query(self, query: str, params: dict = {}) -> List[Dict[str, Any]]:
        """Query Neo4j database."""
        from neo4j.exceptions import CypherSyntaxError

        with self._driver.session(database=self._database) as session:
            try:
                data = session.run(query, params)
                return [r.data() for r in data]
            except CypherSyntaxError as e:
                raise ValueError(f"Generated Cypher Statement is not valid\n{e}")

neo4j_dbs = [
    {
        "account": "tuanna.vpi@pvu.edu.vn",
        "project": "TCDK",
        "NEO4J_URI":"neo4j+s://6bdd6ca1.databases.neo4j.io",
        "NEO4J_USERNAME":"neo4j",
        "NEO4J_PASSWORD":"MptgCHC9QEsJLGkPiyWsd_WkofnGAWSuxN7HpRMON50",
        "AURA_INSTANCEID":"6bdd6ca1",
        "AURA_INSTANCENAME":"Instance01"
    },
    {
        "account": "tuan.a.nguyen@vpi.pvn.vn",
        "project": "STVHDN",
        "NEO4J_URI":"neo4j+s://d58fde64.databases.neo4j.io",
        "NEO4J_USERNAME":"neo4j",
        "NEO4J_PASSWORD":"UrmWtcXfYbU1Hc-KD2Wt4Aa5nYhWdhR6XMSISn6vSHQ",
        "AURA_INSTANCEID":"d58fde64",
        "AURA_INSTANCENAME":"Instance01"
    },
    {
        "account": "muito1712@gmail.com",
        "project": "VPINS",
        "NEO4J_URI":"neo4j+s://f6724121.databases.neo4j.io",
        "NEO4J_USERNAME":"neo4j",
        "NEO4J_PASSWORD":"hsPy2R3_HNAtQu_lJHWpdiAgLdi2OpeBv1D6d8uJGZk",
        "AURA_INSTANCEID":"f6724121",
        "AURA_INSTANCENAME":"Instance01"
    },
]

email_content = """
#### AUTO TRIGGER DATABASE REPORT ####\n
"""
db_content = """
### Account: {account} | Project: {project}
## Status: {status}
## Query Length: {query_length}\n
#------------------------------------------#
"""

for db in neo4j_dbs:
    try:
        AutoTrigger = Neo4jGraph(db['NEO4J_URI'], db['NEO4J_USERNAME'], db['NEO4J_PASSWORD'])
        data = AutoTrigger.query("MATCH (n) RETURN n LIMIT 3")
        _text = db_content.format(account=db['account'], project=db['project'], status=AutoTrigger.status, query_length=len(data))
        email_content += _text
        print("Account: ", db['account'], "\n | Project: ", db['project'], "\n | Status: ", AutoTrigger.status, "\n | Query Length: ", len(data),"\n\n")
    except Exception as e:
        _text = db_content.format(account=db['account'], project=db['project'], status=e, query_length=0)
        print("Account: ", db['account'], " | Project: ", db['project'], " | Status: ", e, " | Query Length: ", 0)
        email_content += _text

email_content += qdrant_email_content
print(email_content)

# EMAIL NOTIFICATION ==============================================================================
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
 
# Thông tin email của người gửi
SENDER = "tuanna.vpi@pvu.edu.vn"
AUTH = "Tc@091712"
 
# Get current date
import datetime
now = datetime.datetime.now()
date = now.strftime("%d-%m-%Y")

# Thông tin email của người nhận
RECEIVER = ['dongpn@vpi.pvn.vn', 'muito1712@gmail.com']
EMAIL_SUBJECT = f'{date} Daily Trigger Database Notification'
 
# Tạo đối tượng MIMEMultipart để đính kèm file
msg = MIMEMultipart()
msg['From'] = SENDER
msg['To'] = ', '.join(RECEIVER)
msg['Subject'] = EMAIL_SUBJECT
 
# Thêm phần tin nhắn vào email
text = email_content
 
msg.attach(MIMEText(text))
 
#=====Gửi email=============================================
smtp_server = 'smtp.office365.com'
smtp_port = 587
 
server = smtplib.SMTP(smtp_server, smtp_port)
server.ehlo('vpihost')
server.local_hostname = 'vpihost'
server.starttls()
server.login(SENDER, AUTH)
server.sendmail(SENDER, RECEIVER, msg.as_string())
server.quit()
 
print('Email sent successfully!')