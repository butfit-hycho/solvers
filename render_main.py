#!/usr/bin/env python3
"""
GR-EAT 체험단 운영 툴 - Render 배포용
"""

import os
import time
import random
import json
import sqlite3
import threading
from datetime import datetime
import concurrent.futures

from flask import Flask, jsonify, request
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials

# Flask 앱 생성
app = Flask(__name__)
CORS(app, origins=[
    "http://localhost:3000",
    "http://localhost:5173", 
    "http://localhost:8080",
    "https://solvers-liard.vercel.app",
    "https://solvers-gcycn6bc1-butfit-hychos-projects.vercel.app",
    "https://solvers-qgkgemd4e-butfit-hychos-projects.vercel.app",
    "https://solvers-dg0kgn9s5-butfit-hychos-projects.vercel.app",
    "https://solvers-5dkv6i975-butfit-hychos-projects.vercel.app",
    "https://butfit-hycho.github.io"
], supports_credentials=True)

# 데이터베이스 경로 설정 (Render에서는 /tmp 사용)
DB_PATH = os.getenv('DB_PATH', '/tmp/experience_team.db')

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
        address_full TEXT NOT NULL,
        agrees_privacy BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 기존 테이블에 experience_group 컬럼 추가 (이미 있으면 무시)
    try:
        cursor.execute('ALTER TABLE applicants ADD COLUMN experience_group TEXT')
        print("✅ experience_group 컬럼 추가 완료")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️  experience_group 컬럼이 이미 존재합니다")
        else:
            print(f"⚠️ 컬럼 추가 중 오류: {e}")
    
    # 인스타그램 데이터 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS instagram_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        applicant_id INTEGER,
        followers_count INTEGER,
        media_count INTEGER,
        username TEXT,
        account_type TEXT,
        collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (applicant_id) REFERENCES applicants (id)
    )
    ''')
    
    # 멤버십 데이터 테이블
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS membership_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        applicant_id INTEGER,
        is_member BOOLEAN DEFAULT 0,
        membership_type TEXT,
        member_id TEXT,
        expiry_date DATE,
        start_date DATE,
        branch_name TEXT,
        checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (applicant_id) REFERENCES applicants (id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ 데이터베이스 초기화 완료")

# Mock 인스타그램 스크래핑 함수
def scrape_instagram_profile_mock(username):
    """Mock 인스타그램 프로필 스크래핑"""
    time.sleep(random.uniform(1, 3))  # 실제 스크래핑 시뮬레이션
    
    # Mock 데이터 반환
    return {
        'followers_count': random.randint(100, 5000),
        'media_count': random.randint(10, 500),
        'username': username,
        'account_type': random.choice(['personal', 'business'])
    }

# 구글 시트 연동 설정
def setup_google_sheets():
    """구글 시트 연동 설정"""
    try:
        # 환경변수에서 Google credentials JSON 확인
        google_creds_json = os.getenv('GOOGLE_CREDENTIALS_JSON')
        
        if google_creds_json:
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
                tmp_file.write(google_creds_json)
                tmp_credentials_file = tmp_file.name
            
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = Credentials.from_service_account_file(tmp_credentials_file, scopes=scope)
            os.unlink(tmp_credentials_file)
            
        else:
            print("⚠️  구글 시트 인증 파일이 없습니다.")
            return None
            
        client = gspread.authorize(creds)
        print("✅ 구글 시트 연동 준비 완료")
        return client
        
    except Exception as e:
        print(f"❌ 구글 시트 연동 실패: {e}")
        return None

def update_google_sheet(applicant_data):
    """구글 시트에 지원자 데이터 업데이트"""
    try:
        client = setup_google_sheets()
        if not client:
            return False
            
        # 기존 시트 ID 사용
        EXISTING_SPREADSHEET_ID = "1Z2VuA49QeQxQRmYVDk6nMaj6mU_UtmxXDzizUgLBEfQ"
        spreadsheet = client.open_by_key(EXISTING_SPREADSHEET_ID)
        worksheet = spreadsheet.sheet1
        
        # 체험단 / 지원일시 / 이름/ 전화번호/인스타그램ID/인스타링크/팔로워수/게시물수/주소/지점명/멤버십상품명/시작일/종료일/재등록여부
        row_data = [
            applicant_data.get('experience_group', ''),             # 체험단
            applicant_data.get('created_at', ''),                   # 지원일시
            applicant_data.get('name', ''),                         # 이름
            applicant_data.get('phone', ''),                        # 전화번호
            applicant_data.get('ig_username', ''),                  # 인스타그램ID
            applicant_data.get('instagram_url', ''),                # 인스타링크
            applicant_data.get('followers_count', '') or '0',       # 팔로워수
            applicant_data.get('media_count', '') or '0',           # 게시물수
            applicant_data.get('address_full', ''),                 # 주소
            applicant_data.get('branch_name', ''),                  # 지점명
            applicant_data.get('membership_type', ''),              # 멤버십상품명
            str(applicant_data.get('membership_start_date', '')) if applicant_data.get('membership_start_date') else '',  # 시작일
            str(applicant_data.get('membership_end_date', '')) if applicant_data.get('membership_end_date') else '',      # 종료일
            applicant_data.get('future_membership_status', 'X')     # 미래 멤버십 여부 (X 또는 O (종료일))
        ]
        
        worksheet.append_row(row_data)
        print(f"✅ 구글 시트 업데이트 완료: {applicant_data.get('name')}")
        return True
        
    except Exception as e:
        print(f"❌ 구글 시트 업데이트 실패: {e}")
        return False

def background_data_collection(applicant_id, instagram_url, phone):
    """백그라운드에서 인스타그램 데이터 수집 및 구글 시트 업데이트"""
    start_time = time.time()
    print(f"🚀 백그라운드 데이터 수집 시작 - ID: {applicant_id}")
    
    try:
        # 인스타그램 사용자명 추출
        username = instagram_url.split('/')[-1] if instagram_url.split('/')[-1] else instagram_url.split('/')[-2]
        
        # 인스타그램 데이터 수집 (Mock)
        ig_data = scrape_instagram_profile_mock(username)
        
        # 데이터베이스에 저장
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 인스타그램 데이터 저장
        cursor.execute('''
            INSERT INTO instagram_data (applicant_id, followers_count, media_count, username, account_type)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            applicant_id,
            ig_data['followers_count'],
            ig_data['media_count'],
            ig_data['username'],
            ig_data['account_type']
        ))
        
        # 멤버십 Mock 데이터 (실제로는 멤버십 DB 조회)
        cursor.execute('''
            INSERT INTO membership_data (applicant_id, is_member, membership_type, member_id)
            VALUES (?, ?, ?, ?)
        ''', (
            applicant_id,
            False,  # Mock: 비회원
            '',
            ''
        ))
        
        conn.commit()
        
        # 구글 시트 업데이트용 데이터 조회
        cursor.execute('''
        SELECT 
            a.*,
            i.followers_count, i.media_count, i.username as ig_username, i.account_type, i.collected_at,
            m.is_member, m.membership_type, m.member_id, m.expiry_date, m.start_date, m.branch_name, m.checked_at
        FROM applicants a
        LEFT JOIN instagram_data i ON a.id = i.applicant_id
        LEFT JOIN membership_data m ON a.id = m.applicant_id
        WHERE a.id = ?
        ''', (applicant_id,))
        
        row = cursor.fetchone()
        
        if row:
            applicant_data = {
                'experience_group': row[1],
                'created_at': row[10],
                'name': row[2],
                'phone': row[3],
                'instagram_url': row[4],
                'address_full': row[8],
                'agrees_privacy': bool(row[9]),
                'followers_count': row[11],
                'media_count': row[12],
                'ig_username': row[13],
                'account_type': row[14],
                'instagram_collected_at': row[15],
                'is_member': bool(row[16]) if row[16] is not None else False,
                'membership_type': row[17],
                'member_id': row[18],
                'expiry_date': row[19],
                'start_date': row[20],
                'branch_name': row[21],
                'membership_checked_at': row[22],
                'future_membership_status': 'X'
            }
            
            # 구글 시트 업데이트
            update_google_sheet(applicant_data)
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 백그라운드 데이터 수집 실패: {e}")
    
    print(f"🎉 백그라운드 데이터 수집 완료 - ID: {applicant_id}, 소요시간: {time.time() - start_time:.2f}초")

# API 엔드포인트들
@app.route('/')
def home():
    """홈페이지"""
    return jsonify({
        'message': 'GR-EAT 체험단 API 서버',
        'status': 'running',
        'version': '1.0.0',
        'endpoints': [
            '/api/applicants',
            '/api/admin/applicants'
        ]
    })

@app.route('/api/applicants', methods=['GET', 'POST'])
def api_applicants():
    """지원자 API"""
    # 데이터베이스 초기화
    init_db()
    
    if request.method == 'GET':
        # 지원자 목록 조회
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT 
            a.*,
            i.followers_count, i.media_count, i.username as ig_username, i.account_type,
            m.is_member, m.membership_type, m.member_id, m.expiry_date, m.start_date, m.branch_name
        FROM applicants a
        LEFT JOIN instagram_data i ON a.id = i.applicant_id
        LEFT JOIN membership_data m ON a.id = m.applicant_id
        ORDER BY a.created_at DESC
        LIMIT 50
        ''')
        
        applicants = []
        for row in cursor.fetchall():
            applicants.append({
                'id': row[0],
                'experience_group': row[1],
                'name': row[2],
                'phone': row[3],
                'instagram_url': row[4],
                'address_zipcode': row[5],
                'address_main': row[6],
                'address_detail': row[7],
                'address_full': row[8],
                'agrees_privacy': bool(row[9]),
                'created_at': row[10],
                'followers_count': row[11],
                'media_count': row[12], 
                'ig_username': row[13],
                'account_type': row[14],
                'is_member': bool(row[15]) if row[15] is not None else None,
                'membership_type': row[16],
                'member_id': row[17],
                'expiry_date': row[18],
                'start_date': row[19],
                'branch_name': row[20]
            })
        
        conn.close()
        return jsonify({'applicants': applicants, 'count': len(applicants)})
    
    elif request.method == 'POST':
        # 새 지원자 생성
        data = request.get_json()
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO applicants (experience_group, name, phone, instagram_url, address_zipcode, address_main, address_detail, address_full, agrees_privacy)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data.get('experience_group'),
                data.get('name'),
                data.get('phone'),
                data.get('instagram_url'),
                data.get('address_zipcode'),
                data.get('address_main'),
                data.get('address_detail'),
                data.get('address_full'),
                data.get('agrees_privacy', False)
            ))
            
            conn.commit()
            applicant_id = cursor.lastrowid
            conn.close()
            
            # 백그라운드에서 인스타그램 데이터 + 멤버십 조회 실행
            thread = threading.Thread(
                target=background_data_collection,
                args=(applicant_id, data.get('instagram_url'), data.get('phone'))
            )
            thread.daemon = True
            thread.start()
            
            return jsonify({'success': True, 'id': applicant_id}), 201
            
        except sqlite3.IntegrityError:
            return jsonify({'error': '이미 등록된 정보입니다. 중복 지원은 불가능합니다.'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/health')
def health_check():
    """헬스 체크 엔드포인트"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False) 