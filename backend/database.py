
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker, DeclarativeBase


# --------------------------------------------------
# Load Environment Variables
# --------------------------------------------------

load_dotenv()


# --------------------------------------------------
# Select Database Mode
# --------------------------------------------------

DB_MODE = os.getenv("DB_MODE", "local").lower().strip()

if DB_MODE not in ("local", "cloud"):
    raise RuntimeError(
        "Invalid DB_MODE. Choose either 'local' or 'cloud'."
    )


# --------------------------------------------------
# Database Configuration
# --------------------------------------------------

if DB_MODE == "local":

    required_variables = [
        "DB_USER",
        "DB_PASSWORD",
        "DB_HOST",
        "DB_NAME"
    ]

    db_config = {
        "username": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "database": os.getenv("DB_NAME")
    }

else:

    required_variables = [
        "CLOUD_DB_USER",
        "CLOUD_DB_PASSWORD",
        "CLOUD_DB_HOST",
        "CLOUD_DB_NAME"
    ]

    db_config = {
        "username": os.getenv("CLOUD_DB_USER"),
        "password": os.getenv("CLOUD_DB_PASSWORD"),
        "host": os.getenv("CLOUD_DB_HOST"),
        "port": int(os.getenv("CLOUD_DB_PORT", "5432")),
        "database": os.getenv("CLOUD_DB_NAME")
    }


# --------------------------------------------------
# Validate Environment Variables
# --------------------------------------------------

missing_variables = [
    variable
    for variable in required_variables
    if not os.getenv(variable)
]

if missing_variables:
    raise RuntimeError(
        "Missing required database environment variables: "
        + ", ".join(missing_variables)
    )


# --------------------------------------------------
# Create Database URL
# --------------------------------------------------

database_url = URL.create(
    drivername="postgresql+psycopg",
    username=db_config["username"],
    password=db_config["password"],
    host=db_config["host"],
    port=db_config["port"],
    database=db_config["database"]
)


# --------------------------------------------------
# Database Connection Arguments
# --------------------------------------------------

connect_args = {
    "connect_timeout": 10
}

if DB_MODE == "cloud":
    connect_args["sslmode"] = "require"


# --------------------------------------------------
# Create Database Engine
# --------------------------------------------------

engine = create_engine(
    database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    pool_recycle=1800,
    connect_args=connect_args
)


# --------------------------------------------------
# Database Sessions
# --------------------------------------------------

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# --------------------------------------------------
# Base Class
# --------------------------------------------------

class Base(DeclarativeBase):
    pass


# --------------------------------------------------
# Database Dependency
# --------------------------------------------------

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()
