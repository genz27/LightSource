import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.db import SessionLocal, engine
from app.models.base import Base
from app.services.persistence import ensure_default_providers, count_users, create_user_db
from app.services.auth import hash_password

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as s:
        await ensure_default_providers(s)
        n = await count_users(s)
        if n == 0:
            await create_user_db(s, email="admin@example.com", username="admin", password_hash=hash_password("Admin123!"), role="admin")
    print("ok")

if __name__ == "__main__":
    asyncio.run(main())