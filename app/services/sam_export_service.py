from fastapi import HTTPException
import pandas as pd
from io import BytesIO
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sam_data import SamData


class SamExportService:
    @staticmethod
    async def export_organization(db: AsyncSession, record_id: str, format: str):
        result = await db.execute(select(SamData).where(SamData.record_id == record_id))
        org = result.scalar_one_or_none()
        
        if not org:
            raise HTTPException(status_code=404, detail="Not found")
        
        EXCLUDE_FIELDS = {"sam_data_id"}
        
        # Convert to DataFrame
        data = {
            c.name: [getattr(org, c.name)]
            for c in org.__table__.columns
            if c.name not in EXCLUDE_FIELDS
        }
        df = pd.DataFrame(data)
        
        for col in df.select_dtypes(include=["datetimetz"]).columns:
            df[col] = df[col].dt.tz_localize(None)

        if format == "excel":
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            output.seek(0)
            return StreamingResponse(output, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            return StreamingResponse(iter([df.to_csv(index=False)]), media_type="text/csv")