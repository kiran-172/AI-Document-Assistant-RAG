
from sqlalchemy import text
from backend.database import engine

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT version()"))
        print("PostgreSQL Connected Successfully!")
        print(result.scalar())

        result = connection.execute(
            text("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
        )
        print("pgvector version:", result.scalar())

except Exception as e:
    print("Database Connection Failed:", e)
