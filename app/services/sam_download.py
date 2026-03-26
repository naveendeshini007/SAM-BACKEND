import os
import requests
import zipfile
import logging
from time import sleep

from fastapi import HTTPException, status
from app.services.sam_date import SamDateService

class SamDownloadService:

    def __init__(self):
        self.download_folder = os.getenv("DOWNLOAD_FOLDER", "./data")
        self.retries = 3
        self.timeout = 60
        self.chunk_size = 8 * 1024 * 1024 

        os.makedirs(self.download_folder, exist_ok=True)

    def build_url(self, file_date: str) -> str:
        return (
            f"https://sam.gov/api/prod/fileextractservices/v1/api/download/"
            f"Entity%20Registration/Public%20V2/"
            f"SAM_PUBLIC_UTF-8_MONTHLY_V2_{file_date}.ZIP?privacy=Public"
        )

    def extract_zip(self, zip_path: str) -> str:
        try:
            logging.info("Extracting ZIP file...")

            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(self.download_folder)

                dat_files = [f for f in z.namelist() if f.endswith(".dat")]

                if not dat_files:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No .dat file found in ZIP"
                    )

                return os.path.join(self.download_folder, dat_files[0])

        except zipfile.BadZipFile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ZIP file"
            )

        except Exception as exception:
            logging.error(f"Extraction failed: {exception}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extract ZIP file"
            )

    def download_and_extract(self, year: int, month: int) -> dict:
        try:
            file_date = SamDateService.get_first_sunday(year, month)

            url = self.build_url(file_date)
            file_name = f"SAM_{file_date}.zip"
            zip_path = os.path.join(self.download_folder, file_name)

            dat_file_name = f"SAM_PUBLIC_UTF-8_MONTHLY_V2_{file_date}.dat"
            dat_path = os.path.join(self.download_folder, dat_file_name)

            if os.path.exists(dat_path):
                logging.info("DAT already exists")

                return {
                    "file_date": file_date,
                    "zip_path": zip_path,
                    "dat_path": dat_path,
                    "status": "already_exists"
                }

            if os.path.exists(zip_path):
                logging.info("ZIP exists. Extracting...")

                dat_path = self.extract_zip(zip_path)

                return {
                    "file_date": file_date,
                    "zip_path": zip_path,
                    "dat_path": dat_path,
                    "status": "extracted_existing_zip"
                }

            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "*/*",
                "Referer": "https://sam.gov/data-services/"
            }

            for attempt in range(self.retries):
                try:
                    logging.info(f"Downloading: {url}")

                    r = requests.get(
                        url,
                        headers=headers,
                        stream=True,
                        timeout=self.timeout
                    )

                    if r.status_code == 404:
                        logging.warning("File not available for this date")

                        return {
                            "file_date": file_date,
                            "zip_path": None,
                            "dat_path": None,
                            "status": "file_not_available"
                        }

                    r.raise_for_status()

                    with open(zip_path, "wb") as f:
                        for chunk in r.iter_content(self.chunk_size):
                            if chunk:
                                f.write(chunk)

                    logging.info("Download success")

                    dat_path = self.extract_zip(zip_path)

                    return {
                        "file_date": file_date,
                        "zip_path": zip_path,
                        "dat_path": dat_path,
                        "status": "downloaded"
                    }

                except requests.exceptions.RequestException as exception:
                    logging.error(f"Retry {attempt + 1} failed: {exception}")
                    sleep(2 ** attempt)

            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Download failed after retries"
            )

        except HTTPException:
            raise

        except Exception as exception:
            logging.error(exception)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Something went wrong"
            )

