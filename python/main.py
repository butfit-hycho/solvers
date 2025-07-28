#!/usr/bin/env python3
"""
체험단 운영 툴 - Firebase Functions
"""

from firebase_functions import https_fn
from firebase_admin import initialize_app
import json
import os
from typing import List, Dict, Optional
import logging

# psycopg2를 조건부 import (배포 시 오류 방지)
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    print("⚠️ psycopg2 모듈이 설치되지 않았습니다. PostgreSQL 기능을 사용할 수 없습니다.")
    POSTGRES_AVAILABLE = False

# 멤버십 검수 함수 직접 구현
MEMBERSHIP_MODULE_AVAILABLE = True

def check_membership_by_phone_fast(phone_number):
    """빠른 멤버십 검수 - 제공받은 정확한 쿼리 사용"""
    
    # 전화번호 정규화
    clean_phone = phone_number.replace("-", "").replace(" ", "")
    
    try:
        conn = get_database_connection()
        with conn.cursor() as cursor:
            
            # 제공받은 정확한 쿼리 사용 (빠른 처리를 위해 한 번에)
            query = """
            WITH membership_data AS (
                SELECT
                    a.id AS mbs_id,
                    a.begin_date,
                    a.end_date,
                    a.title AS product_name,
                    d.name AS branch,
                    e.id AS user_id,
                    e.name AS user_name
                FROM
                    b_payment_btransactionlog b
                LEFT JOIN b_class_bmembership a ON a.transaction_log_id = b.id
                LEFT JOIN b_class_bpass c ON c.id = a.b_pass_id
                LEFT JOIN b_class_bplace d ON d.id = b.b_place_id
                LEFT JOIN user_user e ON e.id = c.user_id
                WHERE
                    a.refund_transaction_id IS NULL
                    AND a.id IS NOT NULL
                    AND a.title NOT LIKE %s
                    AND a.title NOT LIKE %s
                    AND a.title NOT LIKE %s
                    AND a.title NOT LIKE %s
                    AND REPLACE(REPLACE(e.phone_number, '-', ''), ' ', '') = %s
            ),
            current_membership AS (
                SELECT *
                FROM membership_data
                WHERE CURRENT_DATE BETWEEN begin_date AND end_date
                  AND user_name NOT LIKE %s
            ),
            next_membership AS (
                SELECT *
                FROM (
                    SELECT
                        m.user_id,
                        m.begin_date AS next_begin_date,
                        m.end_date AS next_end_date,
                        ROW_NUMBER() OVER (PARTITION BY m.user_id ORDER BY m.begin_date ASC) AS rn
                    FROM membership_data m
                    JOIN current_membership cm ON cm.user_id = m.user_id
                    WHERE m.begin_date > cm.end_date
                ) sub
                WHERE rn = 1
            )
            SELECT 
                cm.user_name,
                cm.branch AS branch_name,
                cm.product_name AS membership_name,
                cm.begin_date AS start_date,
                cm.end_date AS expiry_date,
                CASE 
                    WHEN nm.next_end_date IS NOT NULL THEN 
                        'O(' || TO_CHAR(nm.next_end_date, 'YYYY-MM-DD') || ')'
                    ELSE 'X'
                END AS renewal_status
            FROM current_membership cm
            LEFT JOIN next_membership nm ON cm.user_id = nm.user_id
            LIMIT 1
            """
            
            cursor.execute(query, ['%건강 선물%', '%리뉴얼%', clean_phone, '%(탈퇴)%'])
            result = cursor.fetchone()
            
            if result:
                renewal_status = result[5]  # 정확한 재등록 상태
                logger.info(f"✅ 빠른 멤버십 조회 성공: {phone_number} → {result[1]} ({result[2]}) | 재등록: {renewal_status}")
                
                return {
                    "is_member": True,
                    "membership_name": result[2],
                    "branch_name": result[1],
                    "start_date": str(result[3]) if result[3] else None,
                    "expiry_date": str(result[4]) if result[4] else None,
                    "status": "active",
                    "user_name": result[0],
                    "renewal_status": renewal_status  # 정확한 재등록 상태 사용
                }
            else:
                logger.info(f"❌ 멤버십 조회 실패: {phone_number} - 현재 이용중인 멤버십 없음")
                return {
                    "is_member": False,
                    "membership_name": None,
                    "branch_name": None,
                    "start_date": None,
                    "expiry_date": None,
                    "status": "inactive",
                    "user_name": None,
                    "renewal_status": "X"
                }
        
        conn.close()
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스 오류: {e}")
        raise e

# Firebase 초기화 (이미 초기화된 경우 건너뛰기)
try:
    initialize_app()
except ValueError as e:
    if "already exists" in str(e):
        print("Firebase app이 이미 초기화되었습니다.")
    else:
        raise e

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_database_connection():
    """데이터베이스 연결"""
    if not POSTGRES_AVAILABLE:
        raise Exception("PostgreSQL 모듈이 설치되지 않았습니다.")
    
    try:
        # 환경변수에서 DATABASE_URL 가져오기 (Firebase Secrets에서 설정)
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL이 설정되지 않았습니다.")
        
        # 개행문자 제거
        database_url = database_url.strip()
        
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"데이터베이스 연결 실패: {e}")
        raise

def execute_membership_query(branch_name: str = "신도림") -> List[Dict]:
    """멤버십과 재등록 판별 쿼리 실행"""
    
    # 사용자가 제공한 SQL 쿼리
    query = """
        WITH membership_data AS (
            SELECT
                a.id AS mbs_id,
                a.begin_date,
                a.end_date,
                TO_CHAR(a.end_date, 'YYYY-MM-DD') AS end_date_str,
                a.title AS product_name,
                b.item_price,
                d.name AS branch,
                e.id AS user_id,
                e.name AS user_name,
                REGEXP_REPLACE(e.phone_number, '(02|.{3})(.+)(.{4})', '\\1-\\2-\\3') AS user_phone,
                e.birth_date,
                f.pay_date
            FROM
                b_payment_btransactionlog b
            LEFT JOIN b_class_bmembership a ON a.transaction_log_id = b.id
            LEFT JOIN b_class_bpass c ON c.id = a.b_pass_id
            LEFT JOIN b_class_bplace d ON d.id = b.b_place_id
            LEFT JOIN user_user e ON e.id = c.user_id
            LEFT JOIN b_payment_btransaction f ON f.id = b.transaction_id
            WHERE
                a.refund_transaction_id IS NULL
                AND a.id IS NOT NULL
                AND d.name LIKE %s
                AND a.title NOT LIKE '%건강 선물%'
                AND a.title NOT LIKE '%리뉴얼%'
        ),
        current_membership AS (
            -- 오늘 기준으로 현재 사용 중인 멤버십
            SELECT *
            FROM membership_data
            WHERE CURRENT_DATE BETWEEN begin_date AND end_date
              AND user_name NOT LIKE '%(탈퇴)%'
        ),
        next_membership AS (
            -- 현재 멤버십 이후에 시작하는 멤버십 중 가장 빠른 것
            SELECT *
            FROM (
                SELECT
                    m.user_id,
                    m.begin_date AS next_begin_date,
                    m.end_date AS next_end_date,
                    ROW_NUMBER() OVER (PARTITION BY m.user_id ORDER BY m.begin_date ASC) AS rn
                FROM membership_data m
                JOIN current_membership cm ON cm.user_id = m.user_id
                WHERE m.begin_date > cm.end_date
            ) sub
            WHERE rn = 1
        )
        SELECT 
            cm.user_name AS "회원 이름",
            cm.user_phone AS "전화번호",
            cm.birth_date AS "생년월",
            cm.product_name AS "현재 멤버십 상품명",
            cm.begin_date AS "이용 시작일",
            cm.end_date AS "이용 종료일",
            CASE 
                WHEN nm.next_end_date IS NOT NULL THEN 
                    'O(' || TO_CHAR(nm.next_end_date, 'YYYY-MM-DD') || ')'
                ELSE 'X'
            END AS "재등록 여부"
        FROM current_membership cm
        LEFT JOIN next_membership nm ON cm.user_id = nm.user_id
        ORDER BY cm.user_name ASC
    """
    
    try:
        with get_database_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, (f"%{branch_name}%",))
                rows = cursor.fetchall()
                
                # RealDictCursor를 사용하므로 딕셔너리 형태로 반환됨
                result = [dict(row) for row in rows]
                logger.info(f"{branch_name} 지점 멤버십 조회 완료: {len(result)}건")
                return result
                
    except Exception as e:
        logger.error(f"멤버십 쿼리 실행 중 오류: {e}")
        raise

def get_membership_statistics(branch_name: str = "신도림") -> Dict:
    """멤버십 통계 조회"""
    
    query = """
        WITH membership_data AS (
            SELECT
                a.id AS mbs_id,
                a.begin_date,
                a.end_date,
                a.title AS product_name,
                d.name AS branch,
                e.id AS user_id,
                e.name AS user_name
            FROM
                b_payment_btransactionlog b
            LEFT JOIN b_class_bmembership a ON a.transaction_log_id = b.id
            LEFT JOIN b_class_bpass c ON c.id = a.b_pass_id
            LEFT JOIN b_class_bplace d ON d.id = b.b_place_id
            LEFT JOIN user_user e ON e.id = c.user_id
            WHERE
                a.refund_transaction_id IS NULL
                AND a.id IS NOT NULL
                AND d.name LIKE %s
                AND a.title NOT LIKE '%건강 선물%'
                AND a.title NOT LIKE '%리뉴얼%'
        ),
        current_membership AS (
            SELECT *
            FROM membership_data
            WHERE CURRENT_DATE BETWEEN begin_date AND end_date
              AND user_name NOT LIKE '%(탈퇴)%'
        ),
        renewal_status AS (
            SELECT 
                cm.user_id,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM membership_data m 
                        WHERE m.user_id = cm.user_id 
                        AND m.begin_date > cm.end_date
                    ) THEN 1 
                    ELSE 0 
                END AS has_renewal
            FROM current_membership cm
        )
        SELECT 
            COUNT(*) AS total_current_members,
            SUM(rs.has_renewal) AS members_with_renewal,
            COUNT(*) - SUM(rs.has_renewal) AS members_without_renewal,
            ROUND(SUM(rs.has_renewal) * 100.0 / COUNT(*), 2) AS renewal_rate_percentage
        FROM current_membership cm
        LEFT JOIN renewal_status rs ON cm.user_id = rs.user_id
    """
    
    try:
        with get_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (f"%{branch_name}%",))
                row = cursor.fetchone()
                
                if row:
                    return {
                        "total_current_members": row[0] or 0,
                        "members_with_renewal": row[1] or 0,
                        "members_without_renewal": row[2] or 0,
                        "renewal_rate_percentage": float(row[3] or 0)
                    }
                else:
                    return {
                        "total_current_members": 0,
                        "members_with_renewal": 0,
                        "members_without_renewal": 0,
                        "renewal_rate_percentage": 0.0
                    }
                    
    except Exception as e:
        logger.error(f"멤버십 통계 조회 중 오류: {e}")
        raise

def search_member_by_phone(phone_number: str) -> Optional[Dict]:
    """전화번호로 회원 검색"""
    
    # 전화번호 정규화 (하이픈 제거)
    clean_phone = phone_number.replace("-", "").replace(" ", "")
    
    query = """
        WITH membership_data AS (
            SELECT
                a.id AS mbs_id,
                a.begin_date,
                a.end_date,
                a.title AS product_name,
                e.id AS user_id,
                e.name AS user_name,
                e.phone_number,
                e.birth_date
            FROM
                b_payment_btransactionlog b
            LEFT JOIN b_class_bmembership a ON a.transaction_log_id = b.id
            LEFT JOIN b_class_bpass c ON c.id = a.b_pass_id
            LEFT JOIN user_user e ON e.id = c.user_id
            WHERE
                a.refund_transaction_id IS NULL
                AND a.id IS NOT NULL
                AND REPLACE(REPLACE(e.phone_number, '-', ''), ' ', '') LIKE %s
                AND a.title NOT LIKE '%건강 선물%'
                AND a.title NOT LIKE '%리뉴얼%'
        )
        SELECT 
            user_id,
            user_name,
            phone_number,
            birth_date,
            COUNT(*) AS total_memberships,
            MAX(end_date) AS latest_end_date,
            CASE 
                WHEN MAX(end_date) >= CURRENT_DATE THEN 'ACTIVE'
                ELSE 'EXPIRED'
            END AS status
        FROM membership_data
        GROUP BY user_id, user_name, phone_number, birth_date
        ORDER BY latest_end_date DESC
    """
    
    try:
        with get_database_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, (f"%{clean_phone}%",))
                row = cursor.fetchone()
                
                if row:
                    return {
                        "user_id": row[0],
                        "user_name": row[1],
                        "phone_number": row[2],
                        "birth_date": row[3].isoformat() if row[3] else None,
                        "total_memberships": row[4],
                        "latest_end_date": row[5].isoformat() if row[5] else None,
                        "status": row[6]
                    }
                else:
                    return None
                    
    except Exception as e:
        logger.error(f"회원 검색 중 오류: {e}")
        raise

@https_fn.on_request(
    secrets=["DATABASE_URL"]
)
def membership_api(req):
    """멤버십 관련 API 엔드포인트"""
    
    # CORS 헤더 설정
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Max-Age': '3600',
        'Content-Type': 'application/json'
    }
    
    if req.method == 'OPTIONS':
        return ('', 204, headers)
    
    try:
        # URL 경로 파싱
        path = req.path.strip('/')
        
        if path == 'membership/current-members' and req.method == 'GET':
            # 현재 멤버십 회원 및 재등록 정보 조회
            branch_name = req.args.get('branch_name', '신도림')
            
            members = execute_membership_query(branch_name)
            
            response_data = {
                "success": True,
                "data": members,
                "total_count": len(members),
                "branch_name": branch_name
            }
            
            return (json.dumps(response_data, ensure_ascii=False, default=str), 200, headers)
        
        elif path == 'membership/statistics' and req.method == 'GET':
            # 멤버십 통계 조회
            branch_name = req.args.get('branch_name', '신도림')
            
            stats = get_membership_statistics(branch_name)
            
            response_data = {
                "success": True,
                "data": stats,
                "branch_name": branch_name
            }
            
            return (json.dumps(response_data, ensure_ascii=False), 200, headers)
        
        elif path == 'membership/search' and req.method == 'GET':
            # 전화번호로 회원 검색
            phone_number = req.args.get('phone_number')
            if not phone_number:
                return (json.dumps({"error": "phone_number 파라미터가 필요합니다."}, ensure_ascii=False), 400, headers)
            
            member = search_member_by_phone(phone_number)
            
            if member:
                response_data = {
                    "success": True,
                    "data": member,
                    "found": True
                }
            else:
                response_data = {
                    "success": True,
                    "data": None,
                    "found": False,
                    "message": "해당 전화번호로 등록된 회원을 찾을 수 없습니다."
                }
            
            return (json.dumps(response_data, ensure_ascii=False), 200, headers)
        
        elif path == 'membership/health' and req.method == 'GET':
            # 헬스 체크
            try:
                # 간단한 DB 연결 테스트
                with get_database_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT 1")
                        cursor.fetchone()
                
                response_data = {
                    "status": "healthy",
                    "database": "connected",
                    "timestamp": "2024-01-01T00:00:00Z"
                }
                
                return (json.dumps(response_data, ensure_ascii=False), 200, headers)
                
            except Exception as e:
                response_data = {
                    "status": "unhealthy",
                    "database": "disconnected",
                    "error": str(e)
                }
                
                return (json.dumps(response_data, ensure_ascii=False), 500, headers)
        
        elif path.startswith('membership/') and req.method == 'GET':
            # API 목록 반환
            response_data = {
                "message": "멤버십 검수 API",
                "version": "2.0.0",
                "endpoints": {
                    "current_members": "/membership/current-members?branch_name=신도림",
                    "statistics": "/membership/statistics?branch_name=신도림", 
                    "search": "/membership/search?phone_number=010-1234-5678",
                    "health": "/membership/health"
                },
                "description": "제공된 SQL 쿼리를 사용한 멤버십 재등록 판별 시스템"
            }
            
            return (json.dumps(response_data, ensure_ascii=False), 200, headers)
        
        # 체험단 신청 처리 (POST) - 웹 앱용
        elif req.method == 'POST' and path == 'apply':
            if not MEMBERSHIP_MODULE_AVAILABLE:
                error_response = {
                    "success": False,
                    "message": "멤버십 검수 모듈을 사용할 수 없습니다."
                }
                return (json.dumps(error_response, ensure_ascii=False), 503, headers)
            
            try:
                # 요청 데이터 가져오기
                data = req.get_json()
                if not data:
                    error_response = {
                        "success": False,
                        "message": "요청 데이터가 없습니다."
                    }
                    return (json.dumps(error_response, ensure_ascii=False), 400, headers)
                
                # 필수 필드 확인 (웹 앱 형식에 맞춤)
                required_fields = ['name', 'phone', 'instagram_url']
                for field in required_fields:
                    if field not in data:
                        error_response = {
                            "success": False,
                            "message": f"필수 필드가 누락되었습니다: {field}"
                        }
                        return (json.dumps(error_response, ensure_ascii=False), 400, headers)
                
                # 멤버십 검수 (빠른 검수)
                membership_info = check_membership_by_phone_fast(data['phone'])
                
                # Google Sheets와 Firestore 업데이트 (백그라운드)
                import threading
                def background_update():
                    try:
                        # Google Sheets 업데이트를 위한 데이터 준비
                        applicant_data = {
                            'name': data['name'],
                            'phone': data['phone'],
                            'instagram_url': data['instagram_url'],
                            'address_zipcode': data.get('address_zipcode', ''),
                            'address_main': data.get('address_main', ''),
                            'address_detail': data.get('address_detail', ''),
                            'experience_group': data.get('experience_group', '오리지널소스 체험단')
                        }
                        
                        # Google Sheets 업데이트 (직접 구현)
                        try:
                            # Google Sheets 연결
                            import gspread
                            from google.oauth2.service_account import Credentials
                            
                            # 서비스 계정 파일 확인
                            credentials_file = "google_credentials.json"
                            if not os.path.exists(credentials_file):
                                logger.warning(f"❌ Google Sheets 인증 파일 없음: {credentials_file}")
                                return
                            
                            # 서비스 계정 파일에서 인증 정보 로드
                            scope = [
                                "https://spreadsheets.google.com/feeds",
                                "https://www.googleapis.com/auth/drive"
                            ]
                            
                            credentials = Credentials.from_service_account_file(credentials_file, scopes=scope)
                            gc = gspread.authorize(credentials)
                            
                            # 스프레드시트 열기
                            spreadsheet_id = "1Z2VuA49QeQxQRmYVDk6nMaj6mU_UtmxXDzizUgLBEfQ"
                            spreadsheet = gc.open_by_key(spreadsheet_id)
                            sheet = spreadsheet.sheet1
                            
                            logger.info("✅ Google Sheets 연결 성공")
                            
                            # Instagram 정보는 빈 값으로 설정 (빠른 처리)
                            instagram_info = {'followers': '', 'following': '', 'posts': ''}
                            
                            # 주소 분리 (우편번호와 주소+상세주소 분리)
                            zipcode = applicant_data.get('address_zipcode', '')
                            main_addr = applicant_data.get('address_main', '')
                            detail_addr = applicant_data.get('address_detail', '')
                            full_address = f"{main_addr} {detail_addr}".strip()
                            
                            # 현재 날짜와 시간 (제출일시)
                            from datetime import datetime
                            submit_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            
                            # 새 행 데이터 생성 (정확한 멤버십 정보 사용)
                            new_row = [
                                applicant_data.get('experience_group', '오리지널소스 체험단'),  # 1열: 체험단 (A)
                                applicant_data.get('name', ''),  # 2열: 이름 (B)
                                applicant_data.get('phone', ''),  # 3열: 휴대폰 (C)
                                applicant_data.get('instagram_url', ''),  # 4열: 인스타그램 (D)
                                zipcode,  # 5열: 우편번호 (E)
                                full_address,  # 6열: 주소 (F)
                                instagram_info.get('followers', ''),  # 7열: 팔로워 (G)
                                instagram_info.get('following', ''),  # 8열: 팔로잉 (H)
                                instagram_info.get('posts', ''),  # 9열: 게시물 (I)
                                membership_info.get('branch_name', ''),  # 10열: 지점 (J)
                                membership_info.get('membership_name', ''),  # 11열: 멤버십이름 (K)
                                membership_info.get('start_date', ''),  # 12열: 시작일 (L)
                                membership_info.get('expiry_date', ''),  # 13열: 종료일 (M)
                                membership_info.get('renewal_status', 'X'),  # 14열: 재등록여부 (N) - 정확한 값 사용!
                                submit_datetime  # 15열: 제출일시 (O)
                            ]
                            
                            logger.info(f"📊 새 행 데이터: {new_row}")
                            logger.info(f"🔥 재등록 상태: {membership_info.get('renewal_status', 'X')}")
                            
                            # 실제 Google Sheets에 행 추가
                            sheet.append_row(new_row)
                            logger.info("✅ Google Sheets 업데이트 완료!")
                            
                        except Exception as e:
                            logger.error(f"❌ Google Sheets 업데이트 실패: {e}")
                            import traceback
                            logger.error(f"상세 오류: {traceback.format_exc()}")
                            
                    except Exception as e:
                        logger.error(f"❌ 백그라운드 업데이트 실패: {e}")
                
                # 백그라운드 스레드로 실행
                threading.Thread(target=background_update).start()
                
                response_data = {
                    "success": True,
                    "message": "체험단 신청이 처리되었습니다.",
                    "applicant": {
                        "name": data['name'],
                        "phone": data['phone'],
                        "instagram_url": data['instagram_url'],
                        "address_zipcode": data.get('address_zipcode', ''),
                        "address_main": data.get('address_main', ''),
                        "address_detail": data.get('address_detail', ''),
                        "experience_group": data.get('experience_group', '오리지널소스 체험단')
                    },
                    "membership": membership_info
                }
                
                return (json.dumps(response_data, ensure_ascii=False), 200, headers)
                
            except Exception as e:
                logger.error(f"체험단 신청 처리 중 오류: {e}")
                error_response = {
                    "success": False,
                    "message": f"체험단 신청 처리 중 오류가 발생했습니다: {str(e)}"
                }
                return (json.dumps(error_response, ensure_ascii=False), 500, headers)
        

        
        else:
            # 기본 응답
            response_data = {
                "message": "체험단 운영 툴 - Firebase Functions",
                "version": "2.0.0",
                "available_apis": [
                    "/membership/current-members",
                    "/membership/statistics", 
                    "/membership/search",
                    "/membership/health",
                    "/apply (POST)"
                ]
            }
            
            return (json.dumps(response_data, ensure_ascii=False), 200, headers)
    
    except Exception as e:
        logger.error(f"API 요청 처리 중 오류: {e}")
        
        error_response = {
            "success": False,
            "error": str(e),
            "message": "서버 내부 오류가 발생했습니다."
        }
        
        return (json.dumps(error_response, ensure_ascii=False), 500, headers)

# 기존 테스트 API는 유지
@https_fn.on_request(
    secrets=["DATABASE_URL"]
)
def simple_api(req):
    """간단한 테스트 API"""
    
    # CORS 헤더 설정
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Max-Age': '3600'
    }
    
    if req.method == 'OPTIONS':
        return ('', 204, headers)
    
    if req.path == '/test' and req.method == 'POST':
        try:
            data = req.get_json()
            return ({
                'success': True,
                'message': '테스트 성공',
                'received_data': data
            }, 200, headers)
        except Exception as e:
            return ({'error': f'오류: {str(e)}'}, 500, headers)
    
    # 기본 응답
    return ({'message': '간단한 테스트 API', 'status': 'running'}, 200, headers) 