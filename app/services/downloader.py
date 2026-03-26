import os
import requests
import logging
from time import sleep
from app.core.config import settings


def build_url(file_date):
    return f"https://sam.gov/api/prod/fileextractservices/v1/api/download/Entity%20Registration/Public%20V2/SAM_PUBLIC_UTF-8_MONTHLY_V2_{file_date}.ZIP?privacy=Public"


def download_file(file_date):
    url = build_url(file_date)
    file_name = f"SAM_{file_date}.zip"
    path = os.path.join(settings.DOWNLOAD_FOLDER, file_name)

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
        "Referer": "https://sam.gov/data-services/Entity%20Registration/Public%20V2?privacy=Public"
    }

    os.makedirs(settings.DOWNLOAD_FOLDER, exist_ok=True)

    last_error = None
    for attempt in range(settings.RETRIES):
        try:
            logging.info(f"Downloading {url}")
            with requests.get(
                url,
                headers=headers,
                stream=True,
                timeout=settings.TIMEOUT,
            ) as r:
                r.raise_for_status()
                with open(path, "wb") as f:
                    for chunk in r.iter_content(1024 * 1024):
                        f.write(chunk)

            return path

        except Exception as e:
            last_error = e
            logging.error(e)
            sleep(2 ** attempt)

    raise RuntimeError(
        f"Failed to download SAM file for {file_date} after {settings.RETRIES} retries"
    ) from last_error