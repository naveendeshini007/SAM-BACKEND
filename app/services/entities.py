from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def get_entities(
    session: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
):
    query = text(
        """
        SELECT uei, entity_name, city, state, naics_code, file_date
        FROM sam_entities
        ORDER BY file_date DESC, uei
        LIMIT :limit OFFSET :offset
        """
    )

    result = await session.execute(query, {"limit": limit, "offset": offset})
    rows = result.fetchall()

    return [
        {
            "uei": row[0],
            "entity_name": row[1],
            "city": row[2],
            "state": row[3],
            "naics_code": row[4],
            "file_date": str(row[5]),
        }
        for row in rows
    ]





























# from app.db import get_conn


# def get_entities(limit: int = 10):
#     conn = get_conn()
#     cur = conn.cursor()

#     cur.execute("""
#         SELECT uei, entity_name, city, state, naics_code
#         FROM sam_entities
#         LIMIT %s
#     """, (limit,))

#     rows = cur.fetchall()

#     result = []
#     for row in rows:
#         result.append({
#             "uei": row[0],
#             "entity_name": row[1],
#             "city": row[2],
#             "state": row[3],
#             "naics_code": row[4]
#         })

#     return result