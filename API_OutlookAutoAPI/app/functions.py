from pdfplumber import open as open_pdf
import pandas as pd

def handle_excel(file_name: str):
    dataframe = pd.read_excel(file_name)
    text = dataframe[:].to_string()
    return text

def handle_pdf(filename):
    with open_pdf(filename) as pdf:
        text = ""
        for page in pdf.pages[:min(3, len(pdf.pages))]:
            text += page.extract_text()
    return text