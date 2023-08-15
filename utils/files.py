import os, shutil, pathlib
import pandas as pd


def create_folder(path: str, delete: bool = False) -> None:
    """Create a folder recursively, i.e. mkdir -p

    Args:
        path (str): Folder path.
        delete (bool, optional): Should the progrom delete exist folder? Default
        s to False.
    """    
    if os.path.exists(path) and delete:
        delete_path(path)
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


def delete_path(path: str) -> None:
    """Delete a folder/file, i.e. rm -rf

    Args:
        path (str): Folder/file path.
    """    
    if os.path.exists(path):
        shutil.rmtree(path)


def append_to_file(path: str, content: str) -> None:
    """Append content to a file.

    Args:
        path (str): File path.
        content (str): Content string, should be end with ``\\n``
    """    
    with open(path, "a") as file:
        file.write(content)


def append_csv_to_file(path: str, csv: pd.DataFrame) -> None:
    """Append pandas DataFrame to file.

    Args:
        path (str): File path.
        csv (pd.DataFrame): Pandas DataFrame.
    """    
    if not os.path.exists(path):
        open(path, "w").close()
    is_empty = os.path.getsize(path) == 0
    csv.to_csv(path, index=False, mode="a", header=is_empty)
