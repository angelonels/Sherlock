from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd
import uuid
import io

from database import get_db, engine
from models.user import User
from models.chat import ChatSession
from schemas.chat import ChatSessionResponse
from utils.auth import get_current_user

router = APIRouter(prefix="/chats", tags=["Chat & Data"])

def _sync_to_sql(conn, df, table_name):
    """
    Synchronous helper function strictly used to bridge pandas.to_sql
    into the async event loop using run_sync.
    """
    df.to_sql(name=table_name, con=conn, if_exists='fail', index=False)

@router.post("/upload", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def upload_csv_and_create_chat(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Validation
    if not (file.filename.endswith('.csv') or file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported.")

    try:
        # 2. Ingestion: Read file into memory as bytes, then into Pandas
        contents = await file.read()
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            # Requires the 'openpyxl' engine installed
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error parsing CSV: {str(e)}")

    # 3. Security: Generate a SQL-safe physical table name
    # We replace hyphens with underscores because Postgres table names shouldn't contain hyphens
    safe_uuid = str(uuid.uuid4()).replace("-", "_")
    physical_table_name = f"ds_{safe_uuid}"

    try:
        # 4. Storage: Safely execute pandas blocking logic natively inside our async engine context
        async with engine.begin() as conn:
            await conn.run_sync(_sync_to_sql, df=df, table_name=physical_table_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error while saving data: {str(e)}")

    # 5. Ledger: Create the record mapping this user to this specific table asynchronously
    new_chat = ChatSession(
        user_id=current_user.id,
        title=f"Analysis: {file.filename}",
        original_filename=file.filename,
        physical_table_name=physical_table_name
    )

    db.add(new_chat)
    await db.commit()
    await db.refresh(new_chat)

    return new_chat
