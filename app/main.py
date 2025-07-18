from flask import Flask, jsonify, request
from flask_cors import CORS
import os

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.database import init_db, get_db
from app.models import applicant, instagram, membership

# Flask 앱 생성
app = Flask(__name__)

# CORS 설정
CORS(app, origins=["http://localhost:3000", "http://localhost:5173"])

# 앱 설정
app.config['DEBUG'] = settings.debug

# 초기화 플래그
initialized = False

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
        print(f"📖 기본 API: http://{settings.host}:{settings.port}/")
        initialized = True


@app.before_request
def before_request():
    """요청 전에 실행"""
    initialize_app()


@app.route("/")
def root():
    """홈페이지"""
    return jsonify({
        "message": "체험단 운영 툴 API",
        "version": "1.0.0",
        "status": "running"
    })


@app.route("/health")
def health_check():
    """헬스 체크"""
    return jsonify({
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00Z"
    })


@app.route("/applicants", methods=["GET", "POST"])
def applicants():
    """지원자 목록 조회 및 생성"""
    if request.method == "GET":
        return jsonify({
            "message": "지원자 목록 조회 (미구현)",
            "count": 0,
            "data": []
        })
    
    elif request.method == "POST":
        return jsonify({
            "message": "지원자 생성 (미구현)",
            "data": request.get_json()
        })


if __name__ == "__main__":
    app.run(
        host=settings.host,
        port=settings.port,
        debug=settings.debug
    ) 