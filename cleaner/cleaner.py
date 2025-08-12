import pandas as pd
from pathlib import Path
import json
from dotenv import load_dotenv
import os
from dataclasses import dataclass, field
from typing import List, Optional

load_dotenv()


@dataclass
class ColumnInfo:
    name: str
    type_name: str
    kind: str


def load_columns_from_json(file_path: Path, table_name: str) -> List[ColumnInfo]:
    if not file_path.exists():
        raise FileNotFoundError(f"File {file_path} does not exist.")

    with open(file_path, 'r') as file:
        data = json.load(file)

    columns = []
    for col in data.get(table_name, []):
        columns.append(ColumnInfo(**col))

    return columns


class DaylioCleaner:
    def __init__(self, name: str, table: pd.DataFrame, columns: list[ColumnInfo]) -> None:
        self.name = name
        self.table = table
        self.columns = columns
        self.column_names = [col.name for col in columns]


if __name__ == "__main__":
    # Example usage
    file_path = Path("data/columns.json")
    table_name = "daylio_data"

    try:
        columns = load_columns_from_json(file_path, table_name)
        print(f"Loaded {len(columns)} columns for table '{table_name}'.")
    except FileNotFoundError as e:
        print(e)

    # Assuming we have a DataFrame `df` to work with
    df = pd.DataFrame()  # Placeholder for actual DataFrame
    cleaner = DaylioCleaner(name="ExampleCleaner", table=df, columns=columns)
