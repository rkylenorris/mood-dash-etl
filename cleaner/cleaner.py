import json
import pandas as pd

from typing import List
from pathlib import Path
from dotenv import load_dotenv
from dataclasses import dataclass

from pandas.api.types import is_datetime64_any_dtype

load_dotenv()


@dataclass
class ColumnInfo:
    name: str
    type_name: str
    kind: str


class DaylioCleaner:
    def __init__(self, name: str, table: pd.DataFrame) -> None:
        self.name = name
        self.table = table
        self.col_info_path = Path("data/table_info.json")
        self.columns = self._load_columns()
        self.column_names = [col.name for col in self.columns]
        self._normalize_dates()
        if self.name == "customMoods":
            self._modify_custom_moods()

    def _load_columns(self) -> List[ColumnInfo]:
        if not self.col_info_path.exists():
            raise FileNotFoundError(
                f"Column info file {self.col_info_path} does not exist.")

        with open(self.col_info_path, 'r') as file:
            data = json.load(file)

        if self.name not in data:
            raise ValueError(f"No column information found for '{self.name}'.")

        return [ColumnInfo(**col) for col in data[self.name]]

    def _normalize_dates(self):
        name_map = {
            "createdAt": "date",
            "datetime": "date",
            "created_at": "date",
            "end_date": "date_end",
        }

        invalid_dates = {0}
        if getattr(self, 'name', None) == "goals":
            invalid_dates.add(-1)

        for col_name in (c.name for c in self.columns if c.type_name == 'timestamp'):
            if col_name in name_map:
                col = self.table[col_name]

                col = col.mask(col.isin(invalid_dates))

                if not is_datetime64_any_dtype(col):
                    col = pd.to_datetime(col, errors='coerce', unit='ms')

        self.table[col_name] = col
        self.table[name_map[col_name]] = col.dt.normalize()

    def _modify_custom_moods(self):
        self.table['mood_value'] = 6 - self.table['mood_group_id']

        # these 3 moods are blank in the source data so we need to fill them in
        mapping = {2: "Good", 3: "Meh", 4: "Bad"}
        mask = (self.table["mood_group_id"].isin(mapping.keys())) & (
            self.table["mood_group_order"] == 0)

        self.table.loc[mask, "custom_name"] = self.table.loc[mask,
                                                             "mood_group_id"].map(mapping)

    def to_sql(self, engine) -> None:
        if not self.table.empty:
            self.table[self.column_names].to_sql(
                self.name,
                con=engine,
                if_exists='replace',
                index=False,
                dtype={col.name: col.type_name for col in self.columns}
            )
        else:
            print(f"Table {self.name} is empty, skipping SQL upload.")


def create_entry_tags(cleaner: DaylioCleaner) -> DaylioCleaner:
    if cleaner.name != 'dayEntries':
        raise ValueError(
            "Cleaner must be for 'dayEntries' to create entry tags.")

    tags_df = cleaner.table[['id', 'tags']].explode('tags')
    tags_df = tags_df.rename(columns={'id': 'entry_id', 'tags': 'tag'})

    with pd.option_context('future.no_silent_downcasting', True):
        tags_df['tag'] = tags_df['tag'].fillna(0).astype(int)

    return DaylioCleaner(
        name='entry_tags',
        table=tags_df
    )


def create_mood_groups() -> DaylioCleaner:
    mood_groups_path = Path("data/mood_groups.json")
    df = pd.read_json(mood_groups_path)
    return DaylioCleaner(
        name='mood_groups',
        table=df
    )


if __name__ == "__main__":
    pass
