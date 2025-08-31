from pathlib import Path
from datetime import datetime
import os
import base64
import json
import zipfile as zf
import shutil
from log_setup import logger
from dotenv import load_dotenv
load_dotenv()

# Module-level config
EXPECTED_CWD = os.getenv('EXPECTED_WD', 'daylio-data-cleaner')


def set_cwd(expected_cwd=EXPECTED_CWD) -> None:
    if Path.cwd().name != expected_cwd:
        logger.info(
            f"CWD not '{expected_cwd}' searching for correct directory...")
        for folder in Path.home().rglob(expected_cwd):
            if folder.is_dir() and folder.name == expected_cwd:
                logger.info(
                    f"'{expected_cwd}' directory found, changing working directory")
                os.chdir(str(folder))
                break
        else:
            logger.error(f"'{expected_cwd}' does not exist on this system")
            raise FileNotFoundError(f'{expected_cwd} does not exist')


# Ensure correct working directory
set_cwd()

PICKUP_DIR = Path(os.getenv('DAYLIO_PICKUP_DIR',
                  'C:/Users/YourUsername/Downloads'))
DATA_DIR = Path.cwd() / "data"
JSON_PATH = DATA_DIR / "daylio.json"
SELECTED_TABLES_PATH = DATA_DIR / "static" / "tables_needed.txt"
LAST_UPDATED_PATH = DATA_DIR / "static" / "last_updated.txt"


class Extractor:

    @staticmethod
    def find_backup_file(pickup_dir: Path = PICKUP_DIR) -> Path | None:
        pickup_path = Path(pickup_dir, datetime.today().strftime(
            'backup_%Y_%m_%d.daylio'))
        logger.info(f"Searching for todays backup file: {pickup_path.name}")
        if not pickup_path.exists():
            logger.info('Todays backup not found, finding latest backup...')

            return Extractor.get_latest_backup(pickup_dir)
        elif pickup_path.exists():
            return pickup_path
        else:
            logger.error(
                f"{pickup_path.name} does not exist in designated pickup directory: {pickup_dir}")
            raise FileNotFoundError(f"{pickup_path} does not exist")

    @staticmethod
    def get_latest_backup(pickup_dir: Path = PICKUP_DIR) -> Path | None:
        if not pickup_dir.exists():
            logger.error(f"Pickup directory {pickup_dir} does not exist.")
            raise FileNotFoundError(f"{pickup_dir} does not exist")
        files = pickup_dir.glob('backup_*.daylio')
        if not files:
            logger.error("No backup files found in the pickup directory.")
            return None
        logger.info("Found backup files, returning the latest one.")
        return max(files, key=os.path.getctime, default=None)

    @staticmethod
    def get_selected_tables(selected_tables_path: Path = SELECTED_TABLES_PATH) -> list[str]:
        if not selected_tables_path.exists():
            logger.error(
                f"Selected tables file {selected_tables_path} does not exist.")
            raise FileNotFoundError(f"{selected_tables_path} does not exist")
        return [table.strip() for table in selected_tables_path.read_text().split('\n') if table.strip()]

    @staticmethod
    def extract_backup(pickup_path: Path, data_dir: Path = DATA_DIR):
        logger.info(
            "Extracting zipped data from backup file into data directory")
        with zf.ZipFile(pickup_path, 'r') as zr:
            zr.extractall(data_dir)
            # remove assets folder from extraction, it is not needed
            assets_path = data_dir / "assets"
            if assets_path.exists():
                shutil.rmtree(assets_path)

    @staticmethod
    def decode_backup_to_json(data_dir: Path = DATA_DIR):
        backup_path = data_dir / "backup.daylio"
        logger.info('Decoding backup from base64 to utf-8')
        with open(str(backup_path), 'r') as backup:
            contents = base64.b64decode(backup.read()).decode("utf-8")
        data = json.loads(contents)
        return data

    @staticmethod
    def save_to_json(daylio_data: dict, selected_tables: list[str], json_path: Path = JSON_PATH):
        selected_tables_data = {
            table: daylio_data[table] for table in selected_tables}
        if json_path.exists():
            os.remove(json_path)
        logger.info(f'Saving decoded data as json: {json_path}')
        with open(str(json_path), "w", encoding='utf-8') as j:
            json.dump(selected_tables_data, j, indent=4)

    @staticmethod
    def archive_json(json_path: Path = JSON_PATH, data_dir: Path = DATA_DIR):
        # create date string for archive name
        date_str = datetime.today().strftime('%Y%m%d_%H%M')
        # Create archive path
        archive_path = data_dir / "archive" / f"daylio_{date_str}.json"
        logger.info(
            f"Creating archive copy of todays json file: {archive_path.name}")

        # make directory if it does not exist
        archive_path.parent.mkdir(parents=True, exist_ok=True)

        # erase existing archive if it exists
        if archive_path.exists():
            os.remove(archive_path)

        # copy json to archive
        shutil.copy(json_path, archive_path)

    @staticmethod
    def is_new_data(file_name: str) -> bool:
        if LAST_UPDATED_PATH.exists():
            last_updated = LAST_UPDATED_PATH.read_text().strip()
            if last_updated == file_name:
                logger.info("Data has already been processed.")
                return False
            else:
                LAST_UPDATED_PATH.write_text(file_name)
                return True
        else:
            LAST_UPDATED_PATH.write_text(file_name)
            return True


def extract_daylio_data():
    backup_file = Extractor.find_backup_file()
    if backup_file and Extractor.is_new_data(backup_file.name):
        Extractor.extract_backup(backup_file)
        daylio_data = Extractor.decode_backup_to_json()
        selected_tables = Extractor.get_selected_tables()
        Extractor.save_to_json(daylio_data, selected_tables)
        Extractor.archive_json()
    else:
        logger.error("No data to extract.")


if __name__ == "__main__":
    pass
