from log_setup import logger
from extractor.data_extractor import extract_daylio_data
from fitbit_sleep import clean_sleep_data


def main():
    logger.info("Hello from daylio-data-cleaner!")
    # extract_daylio_data()
    sleep_data = clean_sleep_data()
    print(sleep_data.head())


if __name__ == "__main__":
    main()
