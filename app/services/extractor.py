import logging
from typing import Generator

logger = logging.getLogger(__name__)

SAM_PIPE_COLUMNS = 142

# 8 MB read buffer – reduces OS syscalls on large .dat files.
_FILE_BUFFER_SIZE = 8 * 1024 * 1024


def _normalize_parts(parts: list[str]) -> list[str]:
    """Pad or truncate a split row to exactly SAM_PIPE_COLUMNS fields."""
    n = len(parts)
    if n < SAM_PIPE_COLUMNS:
        parts.extend([""] * (SAM_PIPE_COLUMNS - n))
    elif n > SAM_PIPE_COLUMNS:
        parts = parts[: SAM_PIPE_COLUMNS - 1] + [
            "|".join(parts[SAM_PIPE_COLUMNS - 1 :])
        ]
    return parts


# ---------------------------------------------------------------------------
# Streaming generator – used by the single-pass load path
# ---------------------------------------------------------------------------
def iter_cleaned_parts(
    dat_path: str,
    max_rows: int | None = None,
) -> Generator[list[str], None, int]:
    """
    Lazily iterate the raw SAM .dat file, yielding one normalized list of
    strings per data row (BOF/EOF sentinel lines are skipped).

    Designed to be consumed by the pipeline's COPY loader – no intermediate
    clean file is written, keeping memory usage flat and disk I/O minimal.

    Returns (via StopIteration value) the count of rows that needed
    normalization.
    """
    rows = 0
    normalized_count = 0

    try:
        with open(dat_path, "r", encoding="utf-8", buffering=_FILE_BUFFER_SIZE) as f:
            for raw_line in f:
                if raw_line[:3] in ("BOF", "EOF"):
                    continue
                line = raw_line.rstrip("\r\n")
                if not line:
                    continue

                parts = line.split("|")
                if len(parts) != SAM_PIPE_COLUMNS:
                    normalized_count += 1
                    parts = _normalize_parts(parts)

                yield parts
                rows += 1

                if max_rows is not None and rows >= max_rows:
                    break

    except Exception as exc:
        logger.error("Failed to iterate dat file %s: %s", dat_path, exc)
        raise

    if normalized_count:
        logger.warning(
            "iter_cleaned_parts: normalized %d rows to %d columns",
            normalized_count,
            SAM_PIPE_COLUMNS,
        )
    return normalized_count


# ---------------------------------------------------------------------------
# File-based clean (used only when a cached clean file is desired)
# ---------------------------------------------------------------------------
def clean_dat(input_path: str, output_path: str) -> None:
    """
    Write a normalized pipe-delimited file to *output_path*.
    Prefer the single-pass ``stream_load_to_staging`` for production runs;
    use this only when a cached clean file is explicitly needed.
    """
    rows = 0
    normalized_count = 0

    try:
        with (
            open(input_path, "r", encoding="utf-8", buffering=_FILE_BUFFER_SIZE) as inp,
            open(output_path, "w", encoding="utf-8", buffering=_FILE_BUFFER_SIZE) as out,
        ):
            for raw_line in inp:
                if raw_line[:3] in ("BOF", "EOF"):
                    continue
                line = raw_line.rstrip("\r\n")
                if not line:
                    continue

                parts = line.split("|")
                if len(parts) != SAM_PIPE_COLUMNS:
                    normalized_count += 1
                    parts = _normalize_parts(parts)

                out.write("|".join(parts) + "\n")
                rows += 1

        if normalized_count:
            logger.warning(
                "clean_dat: normalized %d / %d rows to %d columns",
                normalized_count,
                rows,
                SAM_PIPE_COLUMNS,
            )

    except Exception as exc:
        logger.error(
            "Failed to clean dat file %s -> %s: %s", input_path, output_path, exc
        )
        raise
