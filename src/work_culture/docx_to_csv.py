import pandas as pd
import re

from docx import Document


def read_docx(file_path: str) -> str:
    """
    reads the client's docx file and converts it into a raw string

    Parameters
    ----------
    filepath : str
        path for the docx file

    Returns
    -------
    full_text : str
        string of the whole docx file
    """
    doc = Document(file_path)
    full_text = ""
    for paragraph in doc.paragraphs:
        full_text += paragraph.text + "\n"

    return full_text


def nan_to_nocomment(text: str) -> str:
    """
    detects 'nan' responses and replaces them with 'No comment'

    Parameters
    ----------
    text : str
        string to detect nan

    Returns
    -------
    output_text : str
        translated response that is not 'nan'
    """
    if text == "nan":
        output_text = "No comment"
    else:
        output_text = text

    return output_text


def string_to_df(input_string: str) -> pd.DataFrame:
    """
    cleans raw string attained from docx conversion and puts each comment into a dataframe

    Parameters
    ----------
    input_string : str
        raw string attained after read_docx function

    Returns
    -------
    df : pd.DataFrame
        each comment in a row of the dataframe
    """
    comments_pattern = r"Comments: \(\d+\)"
    split_string = re.split(comments_pattern, input_string)

    if len(split_string) == 1:
        raise ValueError("The Comments section was not found")

    data_raw = split_string[1].strip()

    newline_pattern = r"\n"
    comment_list_raw = re.split(newline_pattern, data_raw)

    comment_list_pre = [
        comment.split(". ", 1)[-1].strip()
        for comment in comment_list_raw
        if comment != ""
        and comment != "Restricted Information - Not for Further Distribution"
    ]

    df = pd.DataFrame(comment_list_pre, columns=["comment"])
    df = df.replace("nan", "No comment")
    df = df[df["comment"] != ""]

    return df


def docx_to_csv(filepath: str, output_path: str = "comments.csv"):
    """
    extracts comments from the docx file and saves them into a csv

    Parameters
    ----------
    filepath : str
        path for the docx file
    output_path : str
        path for the output csv file. Default is 'comments.csv'.

    Returns
    ------
    None
        .csv of the comments section is saved in the present working directory
    """
    text = read_docx(filepath)
    df = string_to_df(text)
    df.to_csv(output_path, index=False)
