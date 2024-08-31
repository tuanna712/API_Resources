import neo4j
from typing import Any, Dict, List, Optional

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
    }
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