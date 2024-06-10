from myopenai import MyOAI
import pandas as pd
import os

def starts_with_number(s):
    return str(s)[0].isdigit()

def contains_keywords(s, keywords):
    return any(keyword in str(s) for keyword in keywords)

def split_excel(df: pd.DataFrame, split_criteria: callable):
    # Find the indices where 'Column0' starts with a number
    start_indices = df.index[df.iloc[:, 0].apply(split_criteria)].tolist()

    # Add an extra index to mark the end of the last segment
    start_indices.append(len(df))

    # Split the dataframe into multiple dataframes
    dataframes = []
    for i in range(len(start_indices) - 1):
        dataframes.append(df.iloc[start_indices[i]:start_indices[i + 1]].reset_index(drop=True))
    return dataframes

def clean_dataframe(df):
    # Drop columns where all elements are NaN
    df_cleaned = df.dropna(axis=1, how='all')
    # Drop rows where all elements are NaN
    df_cleaned = df_cleaned.dropna(axis=0, how='all').reset_index(drop=True)
    return df_cleaned

def column_contains_keywords(df, keywords):
    return any(keyword in df.iloc[:, 0].values for keyword in keywords)


def write_report(df_dicts):
    api_key = os.environ("OPENAI_API_KEY")
    myoai = MyOAI(api_key)

    table_content = ""

    for df_dict in df_dicts:
        table_content += f'Name: {df_dict["name"]} \n Table: {df_dict["value"].to_markdown()}'

    sysprompt = """
    You are a master in writing daily well drilling/production report. 
    Your job is to write a concise report based on the report table given, that would be already prepared to be included in an email. 
    """

    prompt = f"""
    Give me a quick report from the below markdown contents of tables, focused on the "Notes" column of each table.
    If the note includes keywords that warn or indicate any abnormal production events, please highlight and take the warning by the name of the well.
    Ignore the table if the notes are empty.

    The table:
    {table_content}
    """

    return myoai.get_chat(prompt, sysprompt)

from functools import partial

def handle_excel(file_name: str):
    keywords = ["Production", "Well Testing"]

    dataframe = pd.read_excel(file_name)
    # text = dataframe[:].to_string()
    dataframes = split_excel(dataframe, split_criteria=starts_with_number)
    dataframes = [clean_dataframe(df) for df in dataframes]

    #checks out those that should be processed
    dataframes = [df for df in dataframes if column_contains_keywords(df, keywords)]
    
    split_dataframe_dicts = []
    for dataframe in dataframes:
        dataframe_name = dataframe.iloc[0, 0]
        split_dataframes = [clean_dataframe(df) for df in split_excel(dataframe, split_criteria=partial(contains_keywords, keywords = keywords))]
        for split_dataframe in split_dataframes:
            splitdf_name = f"{dataframe_name} - {split_dataframe.iloc[0, 0]}"
            split_dataframe.columns = split_dataframe.iloc[1]
            splitdf_value = split_dataframe.iloc[2:,:].reset_index(drop=True)
            # print(f"DataFrame {splitdf_name}:\n{splitdf_value.to_string()}\n")
            split_dataframe_dicts.append({"name": splitdf_name, "value": splitdf_value})
    text = write_report(split_dataframe_dicts)
    return text