import os
from fastapi import FastAPI, HTTPException
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from starlette.middleware.sessions import SessionMiddleware
from fastapi.responses import ORJSONResponse, StreamingResponse, RedirectResponse
from config import DATABASE_URL, SECRET_KEY
from admin import create_admin
from models import Batch
import qrcode
import io
from sqlalchemy import select, update


BASE_DOMAIN = os.getenv("DOMAIN", "localhost")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

app = FastAPI(default_response_class=ORJSONResponse, debug=True)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

admin = create_admin(engine)

@app.get("/admin/batch/download_qr/{pk}")
async def download_qr(pk: int):
    async with AsyncSessionLocal() as session:
        stmt = select(Batch).where(Batch.id == pk)
        result = await session.execute(stmt)
        obj = result.scalar_one_or_none()

        if not obj or not obj.public_id:
            raise HTTPException(status_code=404, detail="Batch not found")

        confirm_url = f"http://{BASE_DOMAIN}/admin/batch/confirm/{obj.public_id}"

        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(confirm_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)

        return StreamingResponse(
            buf,
            media_type="image/png",
            headers={"Content-Disposition": f"attachment; filename=qr_{obj.public_id}.png"}
        )

@app.get("/admin/batch/confirm/{uuid}")
async def confirm_batch(uuid: str):
    async with AsyncSessionLocal() as session:
        stmt = select(Batch).where(Batch.public_id == uuid)
        result = await session.execute(stmt)
        obj = result.scalar_one_or_none()

        if not obj:
            raise HTTPException(status_code=404, detail="Batch not found")

        update_stmt = update(Batch).where(Batch.public_id == uuid).values(status=1)
        await session.execute(update_stmt)
        await session.commit()

    return RedirectResponse(url="/admin/batch/list", status_code=303)

admin.mount_to(app)