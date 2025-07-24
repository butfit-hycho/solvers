#!/usr/bin/env python3
"""
GR-EAT 체험단 모집 API - Render 배포용
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import os
import threading
import time
import random
import gspread
from google.oauth2.service_account import Credentials
import concurrent.futures

app = Flask(__name__)

# CORS 설정 - 모든 필요한 도메인 포함
CORS(app, origins=[
    "http://localhost:3000",
    "http://localhost:3001",
    "http://localhost:5173", 
    "http://localhost:8080",
    "https://solvers-liard.vercel.app",
    "https://solvers-gcycn6bc1-butfit-hychos-projects.vercel.app",
    "https://solvers-qgkgemd4e-butfit-hychos-projects.vercel.app",
    "https://solvers-dg0kgn9s5-butfit-hychos-projects.vercel.app",
    "https://solvers-5dkv6i975-butfit-hychos-projects.vercel.app",
    "https://solvers-quaas0mpi-butfit-hychos-projects.vercel.app",
    "https://butfit-hycho.github.io",
    "https://gr-eat.vercel.app",
    "https://*.vercel.app"
], supports_credentials=True)

# 데이터베이스 경로 설정 (Render 배포용)
DB_PATH = '/tmp/experience_team.db'

# 데이터베이스 초기화
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS applicants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        experience_group TEXT,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        instagram_url TEXT NOT NULL,
        address_zipcode TEXT,
        address_main TEXT NOT NULL,
        address_detail TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # experience_group 컬럼이 없으면 추가
    try:
        cursor.execute("ALTER TABLE applicants ADD COLUMN experience_group TEXT")
        print("✅ experience_group 컬럼이 추가되었습니다")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️  experience_group 컬럼이 이미 존재합니다")
        else:
            print(f"⚠️ 컬럼 추가 중 오류: {e}")
    
    conn.commit()
    conn.close()
    print("✅ 데이터베이스 초기화 완료")

# Google Sheets 설정
def get_google_sheets_service():
    try:
        # 환경변수에서 Google Sheets 인증 정보 가져오기
        service_account_info = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
        if service_account_info:
            credentials_dict = json.loads(service_account_info)
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            credentials = Credentials.from_service_account_info(credentials_dict, scopes=scope)
            return gspread.authorize(credentials)
        return None
    except Exception as e:
        print(f"Google Sheets 서비스 설정 실패: {e}")
        return None

# Instagram 데이터 수집 (Mock)
def mock_get_instagram_data(username):
    """Mock Instagram 데이터 - 실제 스크래핑 대신 더미 데이터 반환"""
    return {
        "followers": random.randint(100, 10000),
        "following": random.randint(50, 1000),
        "posts": random.randint(10, 500),
        "profile_url": f"https://instagram.com/{username}",
        "is_private": random.choice([True, False])
    }

@app.route('/')
def home():
    return jsonify({
        "message": "GR-EAT 체험단 모집 API",
        "version": "1.0.0",
        "status": "running"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/api/applicants', methods=['GET'])
def get_applicants():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM applicants ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        
        applicants = []
        for row in rows:
            applicant = {
                'id': row[0],
                'experience_group': row[1] if len(row) > 1 else '',
                'name': row[2] if len(row) > 2 else row[1],
                'phone': row[3] if len(row) > 3 else row[2],
                'instagram_url': row[4] if len(row) > 4 else row[3],
                'address_zipcode': row[5] if len(row) > 5 else row[4],
                'address_main': row[6] if len(row) > 6 else row[5],
                'address_detail': row[7] if len(row) > 7 else row[6],
                'created_at': row[8] if len(row) > 8 else row[7]
            }
            applicants.append(applicant)
        
        return jsonify(applicants)
    except Exception as e:
        print(f"지원자 조회 오류: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/applicants', methods=['POST'])
def create_applicant():
    try:
        data = request.get_json()
        print(f"📝 새 지원자 데이터 수신: {data}")
        
        # 필수 필드 검증
        required_fields = ['name', 'phone', 'instagram_url', 'address_main']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} 필드가 필요합니다'}), 400
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO applicants (experience_group, name, phone, instagram_url, address_zipcode, address_main, address_detail)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('experience_group', ''),
            data['name'],
            data['phone'],
            data['instagram_url'],
            data.get('address_zipcode', ''),
            data['address_main'],
            data.get('address_detail', '')
        ))
        
        applicant_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"✅ 지원자 저장 완료 (ID: {applicant_id})")
        
        # 백그라운드에서 Instagram 데이터 수집 및 Google Sheets 업데이트
        def background_data_collection():
            try:
                # Instagram 데이터 수집 (Mock)
                instagram_username = data['instagram_url'].split('/')[-1].split('?')[0]
                instagram_data = mock_get_instagram_data(instagram_username)
                
                applicant_data = {
                    'id': applicant_id,
                    'experience_group': data.get('experience_group', ''),
                    'name': data['name'],
                    'phone': data['phone'],
                    'instagram_url': data['instagram_url'],
                    'instagram_data': instagram_data,
                    'address': f"{data.get('address_zipcode', '')} {data['address_main']} {data.get('address_detail', '')}".strip()
                }
                
                # Google Sheets 업데이트
                update_google_sheet(applicant_data)
                
            except Exception as e:
                print(f"백그라운드 작업 오류: {e}")
        
        # 백그라운드 스레드로 실행
        threading.Thread(target=background_data_collection, daemon=True).start()
        
        return jsonify({
            'message': '지원서가 성공적으로 제출되었습니다!',
            'applicant_id': applicant_id
        }), 201
        
    except Exception as e:
        print(f"지원자 생성 오류: {e}")
        return jsonify({'error': str(e)}), 500

def update_google_sheet(applicant_data):
    """Google Sheets에 지원자 데이터 업데이트"""
    try:
        gc = get_google_sheets_service()
        if not gc:
            print("Google Sheets 서비스를 사용할 수 없습니다")
            return
        
        # 스프레드시트 열기 또는 생성
        spreadsheet = create_or_get_spreadsheet(gc)
        if not spreadsheet:
            return
        
        worksheet = spreadsheet.sheet1
        
        # 헤더가 없으면 추가
        try:
            headers = worksheet.row_values(1)
            if not headers:
                headers = ['체험단', '이름', '전화번호', '인스타그램', '주소', '팔로워', '팔로잉', '게시물', '계정 공개여부', '제출시간']
                worksheet.insert_row(headers, 1)
        except Exception:
            headers = ['체험단', '이름', '전화번호', '인스타그램', '주소', '팔로워', '팔로잉', '게시물', '계정 공개여부', '제출시간']
            worksheet.insert_row(headers, 1)
        
        # 새 행 데이터 추가
        instagram_data = applicant_data.get('instagram_data', {})
        row_data = [
            applicant_data.get('experience_group', ''),
            applicant_data['name'],
            applicant_data['phone'],
            applicant_data['instagram_url'],
            applicant_data['address'],
            instagram_data.get('followers', ''),
            instagram_data.get('following', ''),
            instagram_data.get('posts', ''),
            '비공개' if instagram_data.get('is_private') else '공개',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ]
        
        worksheet.append_row(row_data)
        print("✅ Google Sheets 업데이트 완료")
        
    except Exception as e:
        print(f"Google Sheets 업데이트 오류: {e}")

def create_or_get_spreadsheet(gc):
    """스프레드시트 생성 또는 기존 시트 가져오기"""
    try:
        # 기존 스프레드시트 찾기
        try:
            spreadsheet = gc.open("GR-EAT 체험단 지원자 명단")
            print("기존 스프레드시트를 찾았습니다")
            return spreadsheet
        except gspread.SpreadsheetNotFound:
            pass
        
        # 새 스프레드시트 생성
        spreadsheet = gc.create("GR-EAT 체험단 지원자 명단")
        print("새 스프레드시트를 생성했습니다")
        
        # 권한 설정 (편집 가능하도록)
        spreadsheet.share('', perm_type='anyone', role='writer')
        
        return spreadsheet
        
    except Exception as e:
        print(f"스프레드시트 생성/접근 오류: {e}")
        return None

# 애플리케이션 시작 시 데이터베이스 초기화
if __name__ == '__main__':
    print("🚀 GR-EAT 체험단 API 시작 중...")
    init_db()
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
else:
    # Render에서 실행될 때
    print("🚀 GR-EAT 체험단 API 시작 중...")
    init_db()

# Render에서 앱 객체 노출
application = app 