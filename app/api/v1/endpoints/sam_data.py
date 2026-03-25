from fastapi import APIRouter, HTTPException, status
from app.services.sam_download import SamDownloadService

router = APIRouter()

@router.get(
    "/download",
    summary="Download and extract SAM data"
)
async def download_sam_data(year: int, month: int):
    """
    Download SAM data for given year and month
    """
    try:

        if month < 1 or month > 12:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Month must be between 1 and 12"
            )

        service = SamDownloadService()

        result = service.download_and_extract(year, month)
        if result["status"] == "file_not_available":
            return {
                "message": "File not available for selected month",
                "data": result
            }
        if result["status"] == "already_exists":
            return {
                "message": "File already exists",
                "data": result
            }
        if result["status"] == "extracted_existing_zip":
            return {
                "message": "ZIP extracted successfully",
                "data": result
            }
        if result["status"] == "downloaded":
            return {
                "message": "Download and extraction successful",
                "data": result
            }

        return result

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )