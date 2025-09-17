import os
import json
import pandas as pd

from pathlib import Path
from log_setup import setup_logger
from dotenv import load_dotenv
from fitbit_sleep import clean_sleep_data
from sql_cmds import create_db_conn, insert_prefs, create_tables, create_views, add_users, execute_sql_command

from extractor.data_extractor import extract_daylio_data, DATA_DIR, LAST_UPDATED_PATH
from cleaner.cleaner import DaylioCleaner, create_entry_tags, create_mood_groups

load_dotenv()

logger = setup_logger()


def main():
    # set path to db, create if it doesn't exist
    DB_PATH = os.getenv('DB_PATH')
    if not DB_PATH:
        logger.error("DB_PATH not set in environment variables.")
        return

    if not Path(DB_PATH).exists():
        logger.info(f"Database not found at {DB_PATH}, creating new database")
        create_tables()
        add_users()
        create_views()

    logger.info("Mood Dash ETL beginning")
    extract_daylio_data()
    daylio_data_path = DATA_DIR / "daylio.json"
    logger.info(f"Reading extracted data from {daylio_data_path}")
    daylio_data = json.loads(daylio_data_path.read_text())

    daylio_tables = []

    logger.info("Cleaning and loading Daylio data into memory")
    for table_name, table_data in daylio_data.items():
        if table_name == 'prefs':
            # prefs table is small and consists of one record, so just insert it directly
            insert_prefs(table_data)
            continue

        logger.info(f"Loading data for table '{table_name}'")
        daylio_df = pd.DataFrame(table_data)

        logger.info(f"Cleaning data for table '{table_name}'")
        daylio_table = DaylioCleaner(
            name=table_name,
            table=daylio_df
        )

        daylio_tables.append(daylio_table)

        if table_name == 'dayEntries':
            logger.info("Creating entry_tags table from dayEntries")
            entry_tags_table = create_entry_tags(daylio_table)
            daylio_tables.append(entry_tags_table)

    logger.info("Creating mood_groups table")
    daylio_tables.append(create_mood_groups())

    logger.info(f"Writing cleaned data to database at {DB_PATH}")
    for table in daylio_tables:
        table.to_sql(create_db_conn(DB_PATH))
    fit_bit_sleep_table = clean_sleep_data()
    fit_bit_sleep_table.to_sql(
        'fitbit_sleep', create_db_conn(DB_PATH), if_exists='replace', index=False)

    logger.info("Mood Dash ETL complete")


if __name__ == "__main__":
    main()
