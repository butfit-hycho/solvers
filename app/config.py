from pydantic import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 데이터베이스
    database_url: str = "sqlite:///./experience_team.db"
    
    # 환경 설정
    environment: str = "development"
    debug: bool = True
    secret_key: str = "experience-team-secret-key-development"
    
    # Instagram 스크래핑 설정
    instagram_delay_min: int = 2
    instagram_delay_max: int = 5
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    
    # Google Sheets API
    google_sheets_credentials_file: str = "credentials.json"
    google_sheets_spreadsheet_id: Optional[str] = None
    
    # 서버 설정
    host: str = "0.0.0.0"
    port: int = 8000
    
    # JWT 설정
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"
    
    # 로깅 설정
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 전역 설정 인스턴스
settings = Settings() 