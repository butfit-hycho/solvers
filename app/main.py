from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import os

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import init_db, get_db
from app.models import applicant, instagram, membership
from app.api.membership import router as membership_router

import threading
import time
import requests
from datetime import datetime
from sqlalchemy.orm import Session

# FastAPI 앱 생성
app = FastAPI(
    title="체험단 운영 툴 API",
    description="체험단 모집부터 관리까지 자동화된 워크플로우를 제공하는 통합 관리 도구",
    version="2.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 초기화 플래그
initialized = False

# 백그라운드 작업 큐 (메모리)
background_tasks_queue = {}

# Pydantic 모델들
class ApplicantCreate(BaseModel):
    name: str
    phone: str
    instagram_url: str
    address_main: str
    email: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None

class ApplicantResponse(BaseModel):
    success: bool
    message: str
    applicant_id: str
    status: str
    note: Optional[str] = None

class StatusResponse(BaseModel):
    applicant_id: str
    status: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    instagram_scraped: bool = False
    membership_checked: bool = False
    error: Optional[str] = None

def initialize_app():
    """앱 초기화"""
    global initialized
    if not initialized:
        print("🚀 체험단 운영 툴 시작 중...")
        
        # 데이터베이스 초기화
        try:
            init_db()
            print("✅ 데이터베이스 연결 성공")
        except Exception as e:
            print(f"❌ 데이터베이스 연결 실패: {e}")
            raise e
        
        print(f"🌐 서버 실행: http://{settings.host}:{settings.port}")
        print(f"📖 API 문서: http://{settings.host}:{settings.port}/docs")
        print(f"📊 멤버십 API: http://{settings.host}:{settings.port}/membership/")
        initialized = True

# 라우터 등록
app.include_router(membership_router)

@app.on_event("startup")
async def startup_event():
    """앱 시작 시 실행"""
    initialize_app()

@app.get("/", tags=["기본"])
async def root():
    """홈페이지"""
    return {
        "message": "체험단 운영 툴 API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "membership_api": "/membership/"
    }

@app.get("/health", tags=["기본"])
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


def process_applicant_background(applicant_data, applicant_id):
    """백그라운드에서 지원자 Instagram 정보 처리"""
    try:
        print(f"🔄 지원자 {applicant_id} 백그라운드 처리 시작: {applicant_data['name']}")
        
        # Instagram 스크래핑 요청 (로컬 서버 활용)
        instagram_url = applicant_data.get('instagram_url')
        if instagram_url:
            try:
                # 로컬 Instagram 서버에 특정 계정 스크래핑 요청
                scrape_data = {
                    "target_rows": [applicant_data['name']]
                }
                
                print(f"📱 Instagram 스크래핑 시작: {instagram_url}")
                response = requests.post(
                    'http://localhost:5555/scrape_specific',
                    json=scrape_data,
                    timeout=5
                )
                
                if response.status_code == 200:
                    print(f"✅ Instagram 스크래핑 요청 성공: {applicant_data['name']}")
                else:
                    print(f"⚠️ Instagram 스크래핑 요청 실패: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Instagram 서버 연결 실패: {e}")
        
        # 멤버십 검수 (시뮬레이션)
        print(f"🔍 멤버십 검수 중: {applicant_data['name']}")
        time.sleep(1)  # 실제로는 DB 조회
        
        # 완료 상태 업데이트
        background_tasks[applicant_id] = {
            'status': 'completed',
            'completed_at': datetime.now().isoformat(),
            'instagram_scraped': True,
            'membership_checked': True
        }
        
        print(f"🎉 지원자 {applicant_id} 백그라운드 처리 완료")
        
    except Exception as e:
        print(f"❌ 백그라운드 처리 오류: {e}")
        background_tasks[applicant_id] = {
            'status': 'failed',
            'error': str(e),
            'completed_at': datetime.now().isoformat()
        }

@app.route("/applicants", methods=["GET", "POST"])
def applicants():
    """지원자 목록 조회 및 생성 (비동기 처리)"""
    if request.method == "GET":
        return jsonify({
            "message": "지원자 목록 조회 (미구현)",
            "count": 0,
            "data": []
        })
    
    elif request.method == "POST":
        try:
            data = request.get_json()
            
            # 필수 필드 검증
            required_fields = ['name', 'phone', 'instagram_url', 'address_main']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'error': f'{field} 필드가 필요합니다.'}), 400
            
            # 지원자 ID 생성 (실제로는 DB에서 생성)
            applicant_id = f"APP_{int(time.time())}_{hash(data['name']) % 10000}"
            
            print(f"📝 새 지원자 접수: {data['name']} (ID: {applicant_id})")
            
            # 1. 즉시 기본 정보 저장 (시뮬레이션)
            print("💾 기본 정보 저장 중...")
            time.sleep(0.1)  # DB 저장 시뮬레이션
            
            # 2. 백그라운드 작업 시작
            background_tasks[applicant_id] = {
                'status': 'processing',
                'started_at': datetime.now().isoformat(),
                'instagram_scraped': False,
                'membership_checked': False
            }
            
            # 별도 스레드에서 백그라운드 처리
            thread = threading.Thread(
                target=process_applicant_background,
                args=(data, applicant_id)
            )
            thread.daemon = True
            thread.start()
            
            # 3. 즉시 성공 응답
            return jsonify({
                'success': True,
                'message': '지원서가 성공적으로 접수되었습니다.',
                'applicant_id': applicant_id,
                'status': 'processing',
                'note': 'Instagram 정보 수집 및 멤버십 검수는 백그라운드에서 진행됩니다.'
            }), 200
            
        except Exception as e:
            print(f"❌ 지원서 처리 오류: {e}")
            return jsonify({'error': f'처리 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route("/applicants/<applicant_id>/status", methods=["GET"])
def get_applicant_status(applicant_id):
    """지원자 처리 상태 조회"""
    if applicant_id not in background_tasks:
        return jsonify({'error': '해당 지원자를 찾을 수 없습니다.'}), 404
    
    status_data = background_tasks[applicant_id]
    return jsonify({
        'applicant_id': applicant_id,
        'status': status_data['status'],
        'started_at': status_data.get('started_at'),
        'completed_at': status_data.get('completed_at'),
        'instagram_scraped': status_data.get('instagram_scraped', False),
        'membership_checked': status_data.get('membership_checked', False),
        'error': status_data.get('error')
    })


if __name__ == "__main__":
    app.run(
        host=settings.host,
        port=settings.port,
        debug=settings.debug
    ) 