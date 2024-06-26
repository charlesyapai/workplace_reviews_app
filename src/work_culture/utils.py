import pandas as pd
import re
from loguru import logger


def split_sentences_helper(para: str) -> list[str]:
    """
    helper function to split paragraphs into sentences

    Parameters
    ----------
    para : str
        paragraph to be split

    Returns
    -------
    sentences : list[str]
        list of all sentences in the paragraph
    """
    pattern = r"\."
    sentences = re.split(pattern, para)
    return sentences


def break_into_sentences(filepath: str) -> pd.DataFrame:
    """
    breaks all comments into individual sentences, each is a new row.

    Parameters
    ----------
    filepath : str
        path for the csv file containing reviews (subset or not)

    Returns
    -------
    new_df : pd.DataFrame
        dataframe where every row is a single sentence
    """
    df = pd.read_csv(filepath)
    df["sentences"] = df["comment"].apply(split_sentences_helper)
    df_exploded = df.explode("sentences").reset_index(drop=True)

    new_series = df_exploded["sentences"]
    new_df = new_series.to_frame().rename(columns={"sentences": "comment"})
    new_df.dropna(subset=["comment"], inplace=True)

    new_df = new_df[new_df != " "].dropna()
    new_df["comment"] = new_df["comment"].str.strip()

    return new_df


def count_duplicates(filepath_csv1: str, filepath_csv2: str) -> float:
    """
    Calculate the percentage of unique entries in the smaller of two CSV files that are duplicated
    in the larger CSV file, based on a specific column ('comment'). Returns -1 in case of errors.

    Parameters
    ----------
    filepath_csv1 : str
        Path of the first CSV file to compare.
    filepath_csv2 : str
        Path of the second CSV file to compare.

    Returns
    -------
    float
        The percentage of the smaller CSV file's unique entries that have a duplicate in the
        larger CSV file. Returns -1.0 in case of errors.
    """
    df1 = pd.read_csv(filepath_csv1)
    df2 = pd.read_csv(filepath_csv2)
    if df1 is None or df2 is None:
        return -1.0
    if "comment" not in df1.columns or "comment" not in df2.columns:
        logger.error("Missing 'comment' column in one or both CSV files.")
        return -1.0
    unique_df1 = df1.drop_duplicates(subset=["comment"])
    unique_df2 = df2.drop_duplicates(subset=["comment"])
    merged = pd.merge(unique_df1, unique_df2, on="comment", how="inner")
    duplicates = len(merged)
    len1, len2 = len(unique_df1), len(unique_df2)
    smaller_len = min(len1, len2)
    if smaller_len == 0:
        return 0.0  # Avoid division by zero
    return (duplicates / smaller_len) * 100


def topic_aggregation(save_path: str, selected_topics: list, df: pd.DataFrame) -> None:
    """
    Aggregates data from a DataFrame based on selected topics, removes the 'topic' column, and saves the result to a CSV file.

    This function filters the DataFrame to include only the rows corresponding to the selected topics. It then drops the 'topic'
    column from this filtered DataFrame. The result is saved to a CSV file at the specified path, without the index.

    Args:
        save_path (str): The file path where the aggregated CSV will be saved.
        selected_topics (list): A list of topics to filter the DataFrame on.
        df (pd.DataFrame): The original DataFrame containing the data to be aggregated.

    Returns:
        None
    """
    df_aggregated = (
        df.loc[df["topics"].isin(selected_topics)]
        .reset_index(drop=True)
        .drop(columns="topics")
    )
    df_aggregated.to_csv(save_path, index=False)
