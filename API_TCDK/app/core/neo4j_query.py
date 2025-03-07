import os
from .open_ai import MyOAI
from neo4j import GraphDatabase
from dotenv import load_dotenv; load_dotenv('app/.env')

class GraphConnector:
    def __init__(self):
        self.URI = os.environ['NEO4J_URI']
        self.AUTH = (os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD'])
        self.driver = GraphDatabase.driver(self.URI, auth=self.AUTH)
        self.OAI = MyOAI(os.environ['OPENAI_API_KEY'])
        self.cypher = """CALL db.index.vector.queryNodes('{}', {}, {}) 
        YIELD node, score"""
        self.results = None
        self.node = None
        self.keys = None
        self.values = None
        self.items = None
        self.labels = None
        self.name = None
        self.score = None

    def match_entity(self, vector_index, query_, top_k:int=3):
        query_embedding = self.OAI.get_embedding(query_)
        query_cypher = self.cypher.format(vector_index, top_k, query_embedding)
        self.results = self.driver.execute_query(query_=query_cypher, database_="neo4j")
        # print("\n\n===== CYPHER RESULT=====", self.results)
        self.get_node()
        return self.name, self.labels, self.score

    def get_node(self):
        self.node = self.results[0][0]['node']
        self.keys = self.node.keys()
        self.values = self.node.values()
        self.items = self.node.items()
        self.labels = list(self.node.labels)
        self.labels.remove('Embedding')
        self.name = self.node['name']
        self.score = self.results[0][0]['score']

    def execute(self, query_):
        try:
            self.cypher_exec = self.driver.execute_query(query_=query_, database_="neo4j")
            self.cypher_exec = [record for record in self.cypher_exec]
            return self.cypher_exec
        except Exception as e:
            print(e)
            return None
        
    def get_issues(self, query_, top_k:int=3):
        query_embedding = self.OAI.get_embedding(query_)
        query_cypher = self.cypher.format('issue-embeddings', top_k, query_embedding)
        self.results = self.driver.execute_query(query_=query_cypher, database_="neo4j")
        reference = ""
        for i in range(len(self.results[0])):
            issue_name = self.results[0][i]['node']['name']
            issue_abstract = self.results[0][i]['node']['abstract']
            issue_link = self.results[0][i]['node']['link']
            reference += f"- Reference number: #{i+1}\n++ Name: {issue_name}\n++ Abstract: {issue_abstract}\n++ Link: {issue_link}\n\n"
        return reference

from langchain.graphs import Neo4jGraph
class GetSchema:
    def __init__(self) -> None:
        self.graph = Neo4jGraph(
            url=os.environ['NEO4J_URI'], 
            username="neo4j", 
            password=os.environ['NEO4J_PASSWORD'],
        )
        self.graph.refresh_schema()
        print(self.graph.schema)
        # Save graph schema to txt file
        with open("graph_schema.txt", "w") as f:
            f.write(self.graph.schema)




