import fitz, os
import pandas as pd
from fitz import Rect

from .myopenai import MyOAI
import dotenv; dotenv.load_dotenv()
class PdfExtractor:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.pdf_file = fitz.open(file_path)
        self.tables = []
        self.texts = []
    def get_file_info(self):
        return {
            "file_size": os.path.getsize(self.file_path),
            "file_pages": self.pdf_file.page_count,
            "file_metadata": self.pdf_file.metadata,
            "file_path": self.file_path,
        }
    def extract_tables(self):
        """
        Extract all information, images, tables, and text.
 
        Returns:
            document: instance of PdfDocument class after extracting.
        """
        self.extract_tables()
    
    def extract_tables(self):
        for page_idx in range(len(self.pdf_file) - 1):
            page = self.pdf_file[page_idx]
            try:
                print("Page:", page_idx)
                table_list = page.find_tables()
                for table in table_list:
                    rect = Rect(table.bbox)
                    dataframe = table.to_pandas()
                    self.tables.append(dataframe)
            except Exception as e:
                print(e)
                pass
            
def pdf_extraction(file_path):
    DPR = PdfExtractor(file_path)
    DPR.extract_tables()
    target_table = DPR.tables[0]
    print(target_table.head(10))
    target_table.columns = ["Col" + str(i + 1) for i in range(len(target_table.columns))]
 
    # Get start and end index
    start_keyword = "II. OPERATION SUMMARY"
    end_keyword = "III. PROVISIONAL PRODUCTION DATA"
    start_index = target_table[target_table["Col1"].str.contains(start_keyword, na=False)].index.tolist()
    end_index = target_table[target_table["Col1"].str.contains(end_keyword, na=False)].index.tolist()
 
    # Extract main df
    if len(end_index) == 0:
        main_df = target_table.iloc[start_index[0]:]
    else:
        main_df = target_table.iloc[start_index[0]:end_index[0]]
 
    # Reset the index
    main_df = main_df.reset_index(drop=True)
 
    #Loop over the rows
    main_content = ""
    for i in range(len(main_df)):
        row_string = ""
        for value in main_df.iloc[i]:
            if not pd.isna(value):
                row_string += str(value) + " "
        main_content += row_string + "\n"
    print("MAIN CONTENT:" + main_content)
    return main_content

def handle_pdf(file_path):
    text = pdf_extraction(file_path)
    api_key = os.environ["OPENAI_API_KEY"]
    myoai = MyOAI(api_key)

    sysprompt = """
    You are a master in writing daily well drilling/production report. 
    Your job is to write a concise report based on the report table given, that would be already prepared to be included in an email. 
    """

    prompt = f"""
        You are master in summarize the well drilling report events.
        Based on the following report, please provide a concise summary which is focusing on the abnormal events.
        This summary should be in 100 words or less that will be used for prompting the user by email.
        
        Input:
        {text}
        
        Output:
        """
    return myoai.get_chat(prompt, sysprompt)


