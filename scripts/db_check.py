import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app.db import SessionLocal
from sqlalchemy import text

async def main():
    async with SessionLocal() as s:
        u = await s.execute(text('SELECT COUNT(*) FROM users'))
        p = await s.execute(text('SELECT COUNT(*) FROM providers'))
        j = await s.execute(text('SELECT COUNT(*) FROM jobs'))
        a = await s.execute(text('SELECT COUNT(*) FROM assets'))
        print('users', u.scalar(), 'providers', p.scalar(), 'jobs', j.scalar(), 'assets', a.scalar())

if __name__ == '__main__':
    asyncio.run(main())