def main():
    print("Hello from daylio-data-cleaner!")
    from log_setup import logger
    from extractor.daylio_extractor import get_latest_backup
    print(get_latest_backup())


if __name__ == "__main__":
    main()
