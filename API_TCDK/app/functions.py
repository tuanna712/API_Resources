import os
from .core.open_ai import token_count
import semantic_kernel as sk
from .core.open_ai import MyOAI
from .core.neo4j_query import GraphConnector
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from dotenv import load_dotenv; load_dotenv()
from semantic_kernel.functions.kernel_arguments import KernelArguments
class SK_TCDK:
    def __init__(self, api_key):
        self.kernel = sk.Kernel()
        os.environ['OPENAI_API_KEY'] = api_key
        api_key, org_id = os.environ['OPENAI_API_KEY'], ""
        openai_model = os.environ['OPENAI_MODEL_NAME']
        self.plugins_path = "app/Plugins"
        self.kernel.add_service(OpenAIChatCompletion(service_id='default',
                                                     ai_model_id=openai_model, 
                                                     api_key=api_key, org_id=org_id,
                                                     ))
        self.plugins = self.kernel.add_plugin(parent_directory=self.plugins_path, plugin_name="Orchestration")
        self.get_intent = self.plugins["GetIntent"]
        self.gen_chat = self.plugins["GeneralChat"]
        self.gen_cypher = self.plugins["GenerateCypher"]
        self.gen_answer = self.plugins["GenerateAnswer"]
        self.gen_right_question = self.plugins["GenerateRightQuestion"]
        self.gen_issue_answer = self.plugins["GenerateIssueAnswer"]
        self.gen_ner= self.plugins["GetSubjectName"]
        self.response = None
        self.openai = self.check_alive_openai_key()

    async def chat(self, query, mode:str='csdl'):
        if self.openai == False:
            return self.response
        else:
            if mode == 'csdl':
                self.intent = await self.kernel.invoke(self.get_intent, 
                                            KernelArguments(user_question=query))
                print("\n===== USER INTENT =====")
                print("Your intent: ",str(self.intent))
                if str(self.intent) == 'chat':
                    self.response = await self.kernel.invoke(self.gen_chat, 
                                            KernelArguments(user_question=query))
                elif str(self.intent) == 'database':
                    await self.gen_answer_with_cypher_exec(query)
                elif str(self.intent) in ['author', 'organization']:
                    print('Directly Cypher query...')
                    await self.gen_answer_with_cypher_exec(query)
                    print(f'Cypher response: {self.response}')
                    if self.response == []:
                        print('Correct Entity name...')
                        await self.match_entity_and_gen_answer(query) 
            
                elif str(self.intent) == 'terminology':
                    await self.gen_issues_reference(query)

                return self.response
            
            else:
                self.response = self.issue_full_text_search(query)

                return self.response
            
    def issue_full_text_search(self, query):
        query_template = """
        CALL db.index.fulltext.queryNodes("issueFulltextIndex", "{}") YIELD node, score
        RETURN node.name, node.keywords, node.abstract, node.conclusion, node.link, score
        LIMIT 6
        """.format(query) 
        answer_return = """Bạn có thể tham khảo các bài báo sau:\n"""
        answer_template = """Bài báo: "{}"\n- Từ khoá: {}\n- Tóm tắt: {}\n- Kết luận: {}\n- Đường dẫn: {}\n\n"""
        ref_template = """- Bài báo: "{}". Đường dẫn: {}\n"""
        #------------------------------------------------------------
        GC = GraphConnector()
        print(query_template)
        res = GC.execute(query_template)
        for i, r in enumerate(res[0]):
            if i==0:
                _r = answer_template.format(r[0], r[1], r[2], r[3], r[4])
                answer_return += _r
                answer_return += "\nCác bài báo liên quan:"
            else:
                _r = ref_template.format(r[0], r[4])
                answer_return += _r
        self.response = answer_return
        return self.response
    
    async def gen_issues_reference(self, query):
        GC = GraphConnector()
        issue_refer = GC.get_issues(query)
        self.response = await self.kernel.invoke(self.gen_issue_answer, 
                                    KernelArguments(user_question=query,
                                                       issue_reference=issue_refer,
                                                       ))

    async def match_entity_and_gen_answer(self, query):
        if str(self.intent) == 'author':
            vector_index = 'author-embeddings'
            _score_limit = 0.92
        elif str(self.intent) == 'organization':
            vector_index = 'organization-embeddings'
            _score_limit = 0.85
        print("Vector index: ", vector_index)
        print("Query: ", query)

        _ner = await self.kernel.invoke(self.gen_ner,
                                        KernelArguments(user_question=query))
        print("NER: ", str(_ner))
        
        GC = GraphConnector()
        _name, _label, _score = GC.match_entity(vector_index, str(_ner))
        print("Name", _name, "| Label", _label,"| Score", _score)
        if _name is None or len(_name) == 0:
            self.response = f"Can not find information of: {query}\n Please ask another question!"
        else:
            if _score < _score_limit:
                self.response = f"Không thấy thông tin về {_ner}!"
            else:
                self.re_query = await self.kernel.invoke(self.gen_right_question,
                                        KernelArguments(user_question=query,
                                                            entity_label=_label,
                                                            entity_name=_name,
                                                            ))
                print("Re-query: ", self.re_query)
                await self.gen_answer_with_cypher_exec(self.re_query)

    async def gen_answer_with_cypher_exec(self, query):
        GC = GraphConnector()
        self.cypher = await self.kernel.invoke(self.gen_cypher,
                                KernelArguments(user_question=query))
        print("\n===== CYPHER =====")
        print("Cypher query: ", self.cypher)
        self.cypher_res = GC.execute(str(self.cypher))
        print("Cypher results: ", str(self.cypher_res[0]))
        if self.cypher_res[0] != []:
            try:
                if token_count(str(self.cypher_res[0])) > 13000:
                    self.response = str(self.cypher_res[0])
                    self.response += "\n\nThe requested information is too long, can not summarize, please ask another question!"
                    return self.response

                else:
                    self.response = await self.kernel.invoke(self.gen_answer,
                                                KernelArguments(user_question=query,
                                                                    cypher_query=str(self.cypher),
                                                                    cypher_result=str(self.cypher_res[0])
                                                                    ))
                    print("ANSWER: ",str(self.response))
                    return self.response
            except Exception as e:
                self.response = f"!!!{e}"
                print(e)
                return self.response
        else:
            self.response = []
            return self.response
    
    def check_alive_openai_key(self):
        if os.environ['OPENAI_API_KEY'] == "":
            self.response = "Please set OPENAI_API_KEY in .env file"
            return False
        else:
            try:
                OAI = MyOAI(os.environ['OPENAI_API_KEY'])
                embedding = OAI.get_embedding("hello")
                return True
            except Exception as e:
                self.response = f"!!! Openai API key is not valid. {e}"
                return False

    