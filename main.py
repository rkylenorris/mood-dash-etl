from log_setup import logger
from extractor.data_extractor import extract_daylio_data


def main():
    logger.info("Hello from daylio-data-cleaner!")
    extract_daylio_data()


if __name__ == "__main__":
    main()
