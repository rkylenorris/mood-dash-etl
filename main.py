import os
import json
import pandas as pd

from pathlib import Path
from log_setup import logger
from dotenv import load_dotenv
from fitbit_sleep import clean_sleep_data
from sql_cmds import create_db_conn, insert_prefs, create_tables, create_views

from extractor.data_extractor import extract_daylio_data, DATA_DIR
from cleaner.cleaner import DaylioCleaner, create_entry_tags, create_mood_groups

load_dotenv()


def main():
    # set path to db, create if it doesn't exist
    DB_PATH = Path(os.getenv('DB_PATH', "./mood_dash.db"))
    if not DB_PATH.exists():
        logger.info(f"Database not found at {DB_PATH}, creating new database")
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        create_tables()
        create_views()

    logger.info("Mood Dash ETL beginning")
    extract_daylio_data()
    daylio_data_path = DATA_DIR / "daylio.json"
    logger.info(f"Reading extracted data from {daylio_data_path}")
    daylio_data = json.loads(daylio_data_path.read_text())

    daylio_tables = []

    for table_name, table_data in daylio_data.items():
        if table_name == 'prefs':
            insert_prefs(table_data)
            continue

        daylio_df = pd.DataFrame(table_data)

        daylio_table = DaylioCleaner(
            name=table_name,
            table=daylio_df
        )

        daylio_tables.append(daylio_table)

        if table_name == 'dayEntries':
            entry_tags_table = create_entry_tags(daylio_table)
            daylio_tables.append(entry_tags_table)

    daylio_tables.append(create_mood_groups())

    conn = create_db_conn()
    for table in daylio_tables:
        table.to_sql(conn)
    fit_bit_sleep_table = clean_sleep_data()
    fit_bit_sleep_table.to_sql(
        'fitbit_sleep', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()


if __name__ == "__main__":
    main()
