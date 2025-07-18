#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
"""
import sys
import os

# 부모 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import init_db, engine
from app.models.applicant import Applicant
from app.models.instagram import InstagramInfo  
from app.models.membership import MembershipInfo
from sqlalchemy import text


def create_tables():
    """테이블 생성"""
    print("📋 데이터베이스 테이블 생성 중...")
    
    try:
        # 모든 테이블 생성
        init_db()
        print("✅ 테이블 생성 완료")
        
        # 테이블 목록 확인
        with engine.connect() as conn:
            db_url = str(conn.engine.url)
            if "sqlite" in db_url:
                # SQLite용 테이블 목록 쿼리
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """))
            else:
                # PostgreSQL용 테이블 목록 쿼리
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
            
            tables = result.fetchall()
            
            print("\n📊 생성된 테이블 목록:")
            for table in tables:
                print(f"  - {table[0]}")
                
    except Exception as e:
        print(f"❌ 테이블 생성 실패: {e}")
        raise e


def check_connection():
    """데이터베이스 연결 확인"""
    print("🔌 데이터베이스 연결 확인 중...")
    
    try:
        with engine.connect() as conn:
            # SQLite와 PostgreSQL 모두 호환되는 쿼리 사용
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
            
            # 데이터베이스 유형 확인
            db_url = str(conn.engine.url)
            if "sqlite" in db_url:
                print(f"✅ SQLite 연결 성공: {db_url}")
            else:
                # PostgreSQL의 경우 version() 함수 사용
                version_result = conn.execute(text("SELECT version()"))
                version = version_result.fetchone()[0]
                print(f"✅ PostgreSQL 연결 성공: {version}")
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        raise e


def main():
    """메인 실행 함수"""
    print("🚀 체험단 관리 DB 초기화 시작\n")
    
    # 1. 연결 확인
    check_connection()
    print()
    
    # 2. 테이블 생성
    create_tables()
    print()
    
    print("🎉 데이터베이스 초기화 완료!")
    print("\n다음 단계:")
    print("1. 서버 실행: python3 app/main.py")
    print("2. API 문서 확인: http://localhost:8000/docs")


if __name__ == "__main__":
    main() 