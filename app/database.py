from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

from .config import settings

# 데이터베이스 엔진 생성
engine = create_engine(
    settings.database_url,
    echo=settings.debug,  # SQL 쿼리 로깅
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},  # SQLite용
)

# 세션 로컬 클래스
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 (모든 모델이 상속받을 클래스)
Base = declarative_base()


def get_db() -> Generator:
    """데이터베이스 세션 의존성 주입"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """데이터베이스 초기화 (테이블 생성)"""
    Base.metadata.create_all(bind=engine) 