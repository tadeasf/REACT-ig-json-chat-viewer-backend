import pandas as pd
from sqlalchemy import create_engine, Column, String, BigInteger, Text, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from pydantic import BaseModel, ValidationError
from glob import glob
from dotenv import load_dotenv
import os
from typing import Optional

load_dotenv()

MYSQL_URI = os.getenv("MYSQL_URI")

# Configuration
CSV_DIR = '/root/REACT-ig-json-chat-viewer-backend/python_mysql_migration/csvs/'

# SQLAlchemy setup
engine = create_engine(MYSQL_URI)
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()

# Pydantic Model for Validation
class MessageModel(BaseModel):
    _id: str
    sender_id_INTERNAL: int
    sender_name: str
    timestamp_ms: int
    timestamp: str
    content: Optional[str] = None
    sanitizedContent: Optional[str] = None
    photo_creation_timestamp: Optional[int] = None
    photo_uri: Optional[str] = None

def preprocess_dataframe(df):
    float_columns = ['photo_creation_timestamp']
    for col in float_columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64').where(pd.notnull(df[col]), None)
    return df.where(pd.notnull(df), None)

def create_dynamic_table_class(table_name):
    class_name = f"DynamicTable_{table_name}"
    if class_name in globals():
        return globals()[class_name]

    class DynamicTable(Base):
        __tablename__ = table_name
        __table_args__ = {'extend_existing': True}
        id = Column(BigInteger, primary_key=True, autoincrement=True)
        _id = Column(String(255), nullable=False)
        sender_id_INTERNAL = Column(BigInteger)
        sender_name = Column(String(255))
        timestamp_ms = Column(BigInteger)
        timestamp = Column(String(255))
        content = Column(Text, nullable=True)
        sanitizedContent = Column(Text, nullable=True)
        photo_creation_timestamp = Column(BigInteger, nullable=True)
        photo_uri = Column(Text, nullable=True)

    globals()[class_name] = DynamicTable
    return DynamicTable

def load_csv_to_db(csv_file):
    table_name = os.path.splitext(os.path.basename(csv_file))[0]
    DynamicTable = create_dynamic_table_class(table_name)

    if not inspect(engine).has_table(table_name):
        Base.metadata.create_all(engine)

    df = pd.read_csv(csv_file)
    df = preprocess_dataframe(df)

    try:
        df.to_sql(table_name, con=engine, if_exists='append', index=False, method='multi')
        print(f"Loaded data from {csv_file} to MySQL table '{table_name}'.")
    except Exception as e:
        print(f"Failed to load data from {csv_file} into MySQL table '{table_name}': {e}")

if __name__ == "__main__":
    csv_files = glob(os.path.join(CSV_DIR, '*.csv'))
    for csv_file in csv_files:
        load_csv_to_db(csv_file)
