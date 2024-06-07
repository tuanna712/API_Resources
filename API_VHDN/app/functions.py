from openai import OpenAI
from neo4j import GraphDatabase

class KGSearch():
    def __init__(self, open_api_key:str):
        self.URI = "neo4j+s://d58fde64.databases.neo4j.io"
        self.AUTH = ("neo4j", "UrmWtcXfYbU1Hc-KD2Wt4Aa5nYhWdhR6XMSISn6vSHQ")
        self.driver = GraphDatabase.driver(self.URI, auth=self.AUTH)
        self.OPENAI_API_KEY = open_api_key
        self.openai_client = OpenAI(api_key=self.OPENAI_API_KEY)

    def openai_embedding(self, user_input) -> list:
        return self.openai_client.embeddings.create(input=user_input, model="text-embedding-ada-002").data[0].embedding

    def kg_chat(self, user_input) -> str:
        self.node_relations = self._kg_semantic_search(user_input)
        _prompt = self._prompt(user_input, self.node_relations)
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo-0125",
            messages=[{"role": "user", "content": _prompt}],
            temperature=0,
            max_tokens=2000,
            stream=False,
        )
        # for chunk in response:
        #     if chunk.choices[0].delta.content is not None:
        #         print(chunk.choices[0].delta.content, end="")
        return response.choices[0].message.content

    def _prompt(self, question, information):
        return f"""
        You are AI chatbot assistant built by Vietnam Petroleum Institute.
        You are master in assistance to answer questions from given information. 
        If the given information is not enough to answer the question, use your knowledge to answer the question.
        Only use the provided information.
        Always answer in Vietnamese.
        Given information:
        {information}
        Question:
        {question}
        """

    def _kg_semantic_search(self, user_input, top_k:int=3):
        semantic_node_query = """
        CALL db.index.vector.queryNodes('entities-embeddings', {}, {}) 
        YIELD node, score
        """.format(top_k, self.openai_embedding(user_input))

        # Get the similar nodes
        self.semantic_nodes_results = self.driver.execute_query(query_=semantic_node_query, database_="neo4j")
        # Get node's name
        list_nodes = []
        for i in range(len(self.semantic_nodes_results[0])):
            list_nodes.append(self.semantic_nodes_results[0][i]['node']['name'])

        # print(list_nodes)
        relationship_query = """
        MATCH (s:Entity {{name: '{}'}})-[r]-(p)
        RETURN r.description
        """

        self.node_relations = []
        for node in list_nodes:
            # print("Getting relationships of ",node)
            self.relation_results = self.driver.execute_query(query_=relationship_query.format(node), database_="neo4j")
            for i in range(len(self.relation_results[0])):
                self.node_relations.append(self.relation_results[0][i]['r.description'])
        self.node_relations = list(dict.fromkeys(self.node_relations))

        return self.node_relations