import zipfile
import os
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

SAM_PIPE_COLUMNS = 142


def normalize_sam_pipe_line(line):
    """
    SAM monthly extracts are pipe-delimited with 142 columns. Some rows omit
    trailing empty fields or include extra '|' inside the last field; COPY
    requires exactly 142 columns.
    """
    line = line.rstrip("\r\n")
    if not line:
        return None
    parts = line.split("|")
    n = len(parts)
    if n < SAM_PIPE_COLUMNS:
        parts.extend([""] * (SAM_PIPE_COLUMNS - n))
    elif n > SAM_PIPE_COLUMNS:
        parts = parts[: SAM_PIPE_COLUMNS - 1] + [
            "|".join(parts[SAM_PIPE_COLUMNS - 1 :])
        ]
    return "|".join(parts) + "\n"


def extract_zip(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(settings.DOWNLOAD_FOLDER)
        return [f for f in z.namelist() if f.endswith(".dat")][0]


def clean_dat(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as inp, \
         open(output_path, 'w', encoding='utf-8') as out:

        count = 0

        for line in inp:
            if line.startswith("BOF") or line.startswith("EOF"):
                continue

            raw_parts = len(line.rstrip("\r\n").split("|"))
            normalized = normalize_sam_pipe_line(line)
            if normalized is None:
                continue
            if raw_parts != SAM_PIPE_COLUMNS:
                logger.warning(
                    "SAM row %s: had %s pipe fields, normalized to %s",
                    count + 1,
                    raw_parts,
                    SAM_PIPE_COLUMNS,
                )
            out.write(normalized)
            count += 1

        # Note: we intentionally do NOT stop based on settings.LIMIT_ROWS here.
        # The pipeline applies LIMIT_ROWS during staging load so the cleaned
        # output file can be reused across runs.