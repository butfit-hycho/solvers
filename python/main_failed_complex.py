#!/usr/bin/env python3
"""
GR-EAT 체험단 모집 API - Firebase Functions 배포용 (PostgreSQL 연결)
"""

from firebase_functions import https_fn
from firebase_functions.options import set_global_options
from firebase_admin import initialize_app
import json
import random
import os
import threading
from datetime import datetime

# 라이브러리 지연 로딩 (빠른 초기화를 위해)
POSTGRES_AVAILABLE = True
REQUESTS_AVAILABLE = True
SELENIUM_AVAILABLE = False
SHEETS_AVAILABLE = True
print("⚡ 모든 라이브러리는 필요할 때 지연 로딩됩니다")

# Firebase 초기화
initialize_app()

# Firestore 클라이언트 지연 초기화
db = None
print("⚡ Firestore는 필요할 때 지연 초기화됩니다")

# 비용 제어를 위한 최대 인스턴스 수 설정
set_global_options(max_instances=10)

# 전역 변수
engine = None
SessionLocal = None
applicants_data = []  # fallback용

def init_database():
    """PostgreSQL 데이터베이스 연결 초기화 (지연 로딩)"""
    global engine, SessionLocal
    
    try:
        # 필요할 때만 import
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # 하드코딩된 연결 정보 사용 (빠른 초기화)
        database_url = "postgresql://hycho:gaW4Charohchee5shigh0aemeeThohyu@butfitseoul-replica.cjilul7too7t.ap-northeast-2.rds.amazonaws.com:5432/master_20221217"
        
        # PostgreSQL 엔진 생성 (최소 설정으로 빠르게)
        engine = create_engine(
            database_url,
            echo=False,
            pool_size=1,  # 최소 풀 크기
            max_overflow=2,  # 최소 오버플로우
            pool_pre_ping=False,  # 빠른 초기화를 위해 비활성화
            connect_args={"connect_timeout": 5}  # 5초 타임아웃
        )
        
        # 세션 생성
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        print("✅ PostgreSQL 엔진 생성 완료 (지연 로딩)")
        return True
        
    except Exception as e:
        print(f"❌ PostgreSQL 연결 실패: {e}")
        return False

def get_db():
    """데이터베이스 세션 반환"""
    if not POSTGRES_AVAILABLE or not SessionLocal:
        raise Exception("데이터베이스가 초기화되지 않았습니다.")
    
    return SessionLocal()

def get_current_members_with_renewal_status(branch_name="신도림"):
    """제공된 SQL 쿼리 그대로 사용 - 현재 멤버십 회원들의 재등록 현황 조회"""
    
    # 지연 초기화
    if not POSTGRES_AVAILABLE:
        print("⚠️  PostgreSQL 미사용")
        return []
    
    global engine, SessionLocal
    if not SessionLocal:
        print("🔌 PostgreSQL 지연 초기화 중...")
        db_initialized = init_database()
        if not db_initialized:
            print("⚠️  PostgreSQL 초기화 실패")
            return []
    
    try:
        db = get_db()
        
        # 사용자가 제공한 정확한 SQL 쿼리
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
                AND d.name LIKE :branch_name
                AND a.title NOT LIKE '%버핏레이스%'
                AND a.title NOT LIKE '%건강 선물%'
                AND a.title NOT LIKE '%리뉴얼%'
                AND a.title NOT LIKE '%베네핏%'
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
        
        from sqlalchemy import text
        result = db.execute(text(query), {"branch_name": f"%{branch_name}%"})
        rows = result.fetchall()
        
        # 결과를 딕셔너리 리스트로 변환
        columns = [
            "회원 이름", "전화번호", "생년월", "현재 멤버십 상품명", 
            "이용 시작일", "이용 종료일", "재등록 여부"
        ]
        
        member_list = []
        for row in rows:
            member_data = dict(zip(columns, row))
            member_list.append(member_data)
        
        print(f"✅ {branch_name} 지점 현재 멤버십 회원 조회 완료: {len(member_list)}명")
        return member_list
        
    except Exception as e:
        print(f"❌ 현재 멤버십 회원 조회 오류: {e}")
        return []
    finally:
        if 'db' in locals():
            db.close()


def check_membership_by_phone_fast(phone_number):
    """빠른 멤버십 검수 - 기본 정보만 (체험단 제출용)"""
    
    # 지연 초기화
    if not POSTGRES_AVAILABLE:
        return {
            "is_member": False,
            "membership_name": None,
            "branch_name": None,
            "expiry_date": None,
            "user_name": None,
            "renewal_status": "X"
        }
    
    global engine, SessionLocal
    if not SessionLocal:
        db_initialized = init_database()
        if not db_initialized:
            return {
                "is_member": False,
                "membership_name": None,
                "branch_name": None,
                "expiry_date": None,
                "user_name": None,
                "renewal_status": "X"
            }
    
    try:
        # 전화번호 정규화
        clean_phone = phone_number.replace('-', '').replace(' ', '')
        
        db = get_db()
        
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
                AND a.title NOT LIKE '%버핏레이스%'
                AND a.title NOT LIKE '%건강 선물%'
                AND a.title NOT LIKE '%리뉴얼%'
                AND a.title NOT LIKE '%베네핏%'
                AND REPLACE(REPLACE(e.phone_number, '-', ''), ' ', '') = :phone_number
        ),
        current_membership AS (
            SELECT *
            FROM membership_data
            WHERE CURRENT_DATE BETWEEN begin_date AND end_date
              AND user_name NOT LIKE '%(탈퇴)%'
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
        
        from sqlalchemy import text
        result = db.execute(text(query), {"phone_number": clean_phone}).fetchone()
        
        if result:
            renewal_status = result[5]  # 정확한 재등록 상태
            print(f"✅ 빠른 멤버십 조회 성공: {phone_number} → {result[1]} ({result[2]}) | 재등록: {renewal_status}")
            
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
            print(f"❌ 현재 활성 멤버십 없음: {phone_number}")
            return {
                "is_member": False,
                "membership_name": None,
                "branch_name": None,
                "expiry_date": None,
                "user_name": None,
                "renewal_status": "X"
            }
            
    except Exception as e:
        print(f"❌ 빠른 멤버십 조회 오류: {e}")
        return {
            "is_member": False,
            "membership_name": None,
            "branch_name": None,
            "expiry_date": None,
            "user_name": None,
            "renewal_status": "X"
        }
    finally:
        if 'db' in locals():
            db.close()


# 기존 함수명 변경
def check_membership_by_phone_detailed(phone_number):
    """실제 PostgreSQL DB에서 멤버십 정보 조회"""
    
    # 지연 초기화
    if not POSTGRES_AVAILABLE:
        print("⚠️  PostgreSQL 미사용, 신규 회원으로 처리")
        return {
            "is_member": False,
            "membership_name": None,
            "branch_name": None,
            "expiry_date": None,
            "user_name": None,
            "has_future_membership": False,
            "future_expiry_date": None
        }
    
    global engine, SessionLocal
    if not SessionLocal:
        print("🔌 PostgreSQL 지연 초기화 중...")
        db_initialized = init_database()
        if not db_initialized:
            print("⚠️  PostgreSQL 초기화 실패, 신규 회원으로 처리")
            return {
                "is_member": False,
                "membership_name": None,
                "branch_name": None,
                "expiry_date": None,
                "user_name": None,
                "has_future_membership": False,
                "future_expiry_date": None
            }
    
    try:
        # 전화번호 정규화
        clean_phone = phone_number.replace('-', '').replace(' ', '')
        
        db = get_db()
        
        # 제공받은 정확한 쿼리: 현재 이용중인 멤버십 + 재등록 판별
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
                AND a.title NOT LIKE '%버핏레이스%'
                AND a.title NOT LIKE '%건강 선물%'
                AND a.title NOT LIKE '%리뉴얼%'
                AND a.title NOT LIKE '%베네핏%'
                AND REPLACE(REPLACE(e.phone_number, '-', ''), ' ', '') = :phone_number
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
            cm.user_name,
            cm.branch AS branch_name,
            cm.product_name AS membership_name,
            cm.begin_date AS start_date,
            cm.end_date AS expiry_date,
            'active' as status,
            CASE 
                WHEN nm.next_end_date IS NOT NULL THEN 
                    'O(' || TO_CHAR(nm.next_end_date, 'YYYY-MM-DD') || ')'
                ELSE 'X'
            END AS renewal_status,
            CASE WHEN nm.next_end_date IS NOT NULL THEN 1 ELSE 0 END as has_future_membership,
            nm.next_end_date AS future_expiry_date
        FROM current_membership cm
        LEFT JOIN next_membership nm ON cm.user_id = nm.user_id
        LIMIT 1
        """
        
        # text import 지연 로딩
        from sqlalchemy import text
        result = db.execute(text(query), {"phone_number": clean_phone}).fetchone()
        
        if result:
            has_future_membership = result[7] > 0  # has_future_membership (0 또는 1)
            future_expiry_date = str(result[8]) if result[8] else None  # 미래 멤버십 만료일
            renewal_status = result[6]  # 재등록 상태 ('O(날짜)' 또는 'X')
            
            print(f"✅ 멤버십 DB 조회 성공: {phone_number} → {result[1]} ({result[2]})")
            print(f"   재등록 상태: {renewal_status}, 미래 만료일: {future_expiry_date}")
            
            return {
                "is_member": True,
                "membership_name": result[2],
                "branch_name": result[1],
                "start_date": str(result[3]) if result[3] else None,
                "expiry_date": str(result[4]) if result[4] else None,
                "status": result[5],
                "user_name": result[0],
                "has_future_membership": has_future_membership,
                "future_expiry_date": future_expiry_date,
                "renewal_status": renewal_status  # 새로 추가: 정확한 재등록 상태
            }
        else:
            print(f"❌ 멤버십 DB에서 해당 전화번호 없음: {phone_number}")
            return {
                "is_member": False,
                "membership_name": None,
                "branch_name": None,
                "expiry_date": None,
                "user_name": None,
                "has_future_membership": False,
                "future_expiry_date": None
            }
            
    except Exception as e:
        print(f"❌ 멤버십 조회 오류: {e}")
        return {
            "is_member": False,
            "membership_name": None,
            "branch_name": None,
            "expiry_date": None,
            "user_name": None,
            "has_future_membership": False,
            "future_expiry_date": None
        }
    finally:
        if 'db' in locals():
            db.close()

def scrape_instagram_profile(instagram_url):
    """Instagram 프로필 정보 스크래핑 - 빠른 제출을 위해 비활성화"""
    
    print(f"⚡ 인스타그램 스크래핑 비활성화 (빠른 제출): {instagram_url}")
    
    # 빠른 제출을 위해 스크래핑 완전 비활성화
    return {"followers": 0, "following": 0, "posts": 0, "success": False, "error": "스크래핑 비활성화 (로컬 도구 사용)"}

def scrape_instagram_profile_advanced(instagram_url):
    """Firebase 최적화된 Instagram 스크래핑 (로컬 속도 목표)"""
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox") 
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins") 
    chrome_options.add_argument("--disable-images")  # 이미지 로딩 안함
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--page-load-strategy=eager")  # 빠른 로딩
    
    # 봇 탐지 회피용 User-Agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Chrome 바이너리 경로 설정
    chrome_binary = shutil.which("google-chrome") or "/usr/bin/google-chrome"
    if os.path.exists(chrome_binary):
        chrome_options.binary_location = chrome_binary
    
    driver = None
    try:
        print(f"🚀 Chrome 시작: {instagram_url}")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(20)  # 충분한 타임아웃
        
        driver.get(instagram_url)
        print("📄 페이지 로딩 완료")
        
        # 페이지 로딩 대기 (더 견고하게)
        WebDriverWait(driver, 15).until(
            EC.any_of(
                EC.presence_of_element_located((By.TAG_NAME, "main")),
                EC.presence_of_element_located((By.TAG_NAME, "article"))
            )
        )
        print("✅ 페이지 요소 감지됨")
        
        # 팔로워/팔로잉/게시물 추출 (여러 방법 시도)
        followers = 0
        following = 0
        posts = 0
        
        # 팔로워 수 추출 (여러 선택자 시도)
        follower_selectors = [
            "//a[contains(@href, '/followers/')]/span",
            "//a[contains(@href, '/followers/')]/span/span",
            "//*[contains(text(), 'follower')]/preceding-sibling::span"
        ]
        for selector in follower_selectors:
            try:
                elem = driver.find_element(By.XPATH, selector)
                text = elem.get_attribute('title') or elem.text
                followers = int(text.replace(',', '').replace('K', '000').replace('M', '000000'))
                print(f"👥 팔로워: {followers}")
                break
            except:
                continue
        
        # 팔로잉 수 추출
        following_selectors = [
            "//a[contains(@href, '/following/')]/span",
            "//a[contains(@href, '/following/')]/span/span"
        ]
        for selector in following_selectors:
            try:
                elem = driver.find_element(By.XPATH, selector)
                following = int(elem.text.replace(',', '').replace('K', '000').replace('M', '000000'))
                print(f"👤 팔로잉: {following}")
                break
            except:
                continue
        
        # 게시물 수 추출
        post_selectors = [
            "//*[contains(text(), 'posts')]/parent::*/span[1]",
            "//*[contains(text(), 'posts')]/preceding-sibling::span[1]",
            "//div[contains(text(), 'posts')]/../span"
        ]
        for selector in post_selectors:
            try:
                elem = driver.find_element(By.XPATH, selector)
                posts = int(elem.text.replace(',', '').replace('K', '000').replace('M', '000000'))
                print(f"📸 게시물: {posts}")
                break
            except:
                continue
        
        print(f"🎉 스크래핑 성공! 팔로워: {followers}, 팔로잉: {following}, 게시물: {posts}")
        
        return {
            "followers": followers,
            "following": following,
            "posts": posts,
            "success": True,
            "error": None
        }
        
    except Exception as e:
        print(f"❌ 스크래핑 전체 실패: {e}")
        return {
            "followers": 0,
            "following": 0,
            "posts": 0,
            "success": False,
            "error": str(e)
        }
    finally:
        if driver:
            driver.quit()
            print("🔄 Chrome 종료")

def scrape_instagram_profile_quick(instagram_url):
    """클라우드 환경용 빠른 스크래핑 (5초 제한)"""
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox") 
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-plugins") 
    chrome_options.add_argument("--disable-images")
    chrome_options.add_argument("--disable-javascript")  # JS 완전 비활성화
    chrome_options.add_argument("--window-size=800,600")  # 작은 창
    chrome_options.add_argument("--page-load-strategy=none")  # 최대한 빠르게
    
    # 간단한 User-Agent
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (compatible; InstagramBot/1.0)")
    
    chrome_binary = shutil.which("google-chrome") or "/usr/bin/google-chrome"
    if os.path.exists(chrome_binary):
        chrome_options.binary_location = chrome_binary
    
    driver = None
    try:
        print(f"⚡ 빠른 Chrome 시작: {instagram_url}")
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(5)  # 5초 제한
        
        driver.get(instagram_url)
        print("⚡ 페이지 빠른 로딩")
        
        # 최소한의 대기
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # 간단한 정보만 추출 시도
        followers = 0
        following = 0
        posts = 0
        
        # 매우 간단한 선택자만 시도
        try:
            followers_elem = driver.find_element(By.XPATH, "//a[contains(@href, '/followers/')]/span")
            followers = int(followers_elem.text.replace(',', '').replace('K', '000')[:6])
        except:
            pass
            
        try:
            following_elem = driver.find_element(By.XPATH, "//a[contains(@href, '/following/')]/span")
            following = int(following_elem.text.replace(',', '').replace('K', '000')[:6])
        except:
            pass
        
        print(f"⚡ 빠른 스크래핑: 팔로워 {followers}, 팔로잉 {following}")
        
        return {
            "followers": followers,
            "following": following,
            "posts": posts,
            "success": True,
            "method": "quick"
        }
        
    except Exception as e:
        print(f"❌ 빠른 스크래핑 실패: {e}")
        raise e
    finally:
        if driver:
            driver.quit()

def scrape_instagram_profile_fallback(instagram_url):
    """requests를 사용한 Instagram 스크래핑 (fallback)"""
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
        response = requests.get(instagram_url, headers=headers, timeout=10)
        content = response.text
        
        # 정규식으로 팔로워 수 추출
        followers_match = re.search(r'"edge_followed_by":{"count":(\d+)}', content)
        following_match = re.search(r'"edge_follow":{"count":(\d+)}', content)
        posts_match = re.search(r'"edge_owner_to_timeline_media":{"count":(\d+)}', content)
        
        followers = int(followers_match.group(1)) if followers_match else 0
        following = int(following_match.group(1)) if following_match else 0
        posts = int(posts_match.group(1)) if posts_match else 0
        
        return {
            "followers": followers,
            "following": following,
            "posts": posts,
            "success": True,
            "error": None
        }
        
    except Exception as e:
        print(f"❌ requests 스크래핑 실패: {e}")
        return {
            "followers": 0,
            "following": 0,
            "posts": 0,
            "success": False,
            "error": str(e)
        }

def get_google_sheets_service():
    """Google Sheets 서비스 객체 반환"""
    try:
        # 서비스 계정 키 파일 경로
        credentials_file = "google_credentials.json"
        
        if not os.path.exists(credentials_file):
            print(f"❌ Google Sheets 인증 파일을 찾을 수 없습니다: {credentials_file}")
            return None
        
        # 인증 정보 설정
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials = Credentials.from_service_account_file(credentials_file, scopes=scope)
        gc = gspread.authorize(credentials)
        
        return gc
        
    except Exception as e:
        print(f"❌ Google Sheets 서비스 생성 실패: {e}")
        return None

def create_or_get_spreadsheet(gc, spreadsheet_id="1Z2VuA49QeQxQRmYVDk6nMaj6mU_UtmxXDzizUgLBEfQ"):
    """기존 스프레드시트 직접 사용"""
    try:
        # 기존 스프레드시트 ID로 직접 접근
        spreadsheet = gc.open_by_key(spreadsheet_id)
        print(f"✅ 기존 스프레드시트 접근 성공 (빠른 처리): {spreadsheet_id}")
        
        # 첫 번째 워크시트 가져오기
        worksheet = spreadsheet.sheet1
        
        # 헤더가 없다면 추가
        try:
            headers = worksheet.row_values(1)
            if not headers or headers[0] != "체험단":
                # 헤더 설정
                header_row = [
                    "체험단", "이름", "휴대폰", "인스타그램", "우편번호", "주소", "상세주소",
                    "팔로워", "팔로잉", "게시물", "지점", "멤버십이름", "시작일", "종료일", "재등록여부"
                ]
                worksheet.update('A1:O1', [header_row])
                print("✅ 스프레드시트 헤더 설정 완료")
        except Exception as e:
            print(f"⚠️  헤더 설정 중 오류: {e}")
        
        return worksheet
        
    except Exception as e:
        print(f"❌ 스프레드시트 접근 실패: {e}")
        print(f"❌ 스프레드시트 ID: {spreadsheet_id}")
        print("💡 스프레드시트 공유 권한을 service account에게 부여했는지 확인하세요")
        return None

def update_google_sheet(applicant_data):
    """Google Sheets에 데이터 업데이트 (스레드로 실행)"""
    try:
        # Google Sheets 연결 (간소화된 방식)
        import json
        from google.oauth2.service_account import Credentials
        
        # 실제 서비스 계정 정보 사용
        if not os.path.exists("google_credentials.json"):
            print(f"❌ Google Sheets 인증 파일 없음, 메모리에만 저장")
            return
        
        try:
            # 실제 Google Sheets 연결 (지연 로딩)
            import gspread
            from google.oauth2.service_account import Credentials
            
            # 서비스 계정 파일에서 인증 정보 로드
            scope = [
                "https://spreadsheets.google.com/feeds",
                "https://www.googleapis.com/auth/drive"
            ]
            
            credentials = Credentials.from_service_account_file("google_credentials.json", scopes=scope)
            gc = gspread.authorize(credentials)
            
            # 스프레드시트 열기
            spreadsheet_id = "1Z2VuA49QeQxQRmYVDk6nMaj6mU_UtmxXDzizUgLBEfQ"
            spreadsheet = gc.open_by_key(spreadsheet_id)
            sheet = spreadsheet.sheet1
            
            print(f"✅ Google Sheets 연결 성공")
            
        except Exception as e:
            print(f"❌ Google Sheets 연결 실패: {e}")
            return
        
        # 휴대폰 번호로 멤버십 정보 조회 (빠른 검수)
        phone_number = applicant_data.get('phone', '')
        membership_info = check_membership_by_phone_fast(phone_number)
        print(f"[DEBUG] 멤버십 정보 조회 완료: {membership_info}")
        
        # Instagram 스크래핑 완전 비활성화 - 빠른 제출을 위해
        instagram_info = {'followers': '', 'following': '', 'posts': ''}
        print(f"[DEBUG] Instagram 정보: 스크래핑 비활성화, 로컬 도구에서 별도 처리")
        
        # 주소 분리 (우편번호와 주소+상세주소 분리)
        zipcode = applicant_data.get('address_zipcode', '')
        main_addr = applicant_data.get('address_main', '')
        detail_addr = applicant_data.get('address_detail', '')
        full_address = f"{main_addr} {detail_addr}".strip()  # 주소 + 상세주소
        
        # 현재 날짜와 시간 (제출일시)
        from datetime import datetime
        submit_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 새 행 데이터 생성 (최종 컬럼 구조에 맞춤)
        new_row = [
            "오리지널소스 체험단",  # 1열: 체험단 (A)
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
            membership_info.get('renewal_status', 'X'),  # 14열: 재등록여부 (N) - 정확한 SQL 쿼리 결과 사용
            submit_datetime  # 15열: 제출일시 (O)
        ]
        
        print(f"[DEBUG] 새 행 데이터 생성 완료: {new_row}")
        
        # 실제 Google Sheets에 행 추가
        try:
            sheet.append_row(new_row)
            print(f"✅ Google Sheets 업데이트 완료!")
        except Exception as e:
            print(f"❌ Google Sheets 행 추가 실패: {e}")
        
    except Exception as e:
        print(f"[ERROR] Google Sheets 업데이트 실패: {e}")
        import traceback
        traceback.print_exc()

def save_to_firestore(applicant_data):
    """Firebase Firestore에 제출 정보 저장 (백업)"""
    try:
        global db
        
        # Firestore 지연 초기화
        if not db:
            try:
                from firebase_admin import firestore
                db = firestore.client()  # 기본 데이터베이스 사용
                print("✅ Firestore 지연 초기화 완료")
            except Exception as e:
                print(f"❌ Firestore 지연 초기화 실패: {e}")
                return
        
        # 휴대폰 번호로 멤버십 정보 조회 (빠른 검수)
        phone_number = applicant_data.get('phone', '')
        membership_info = check_membership_by_phone_fast(phone_number)
        
        # 현재 날짜와 시간
        from datetime import datetime
        submit_datetime = datetime.now()
        
        # Firestore에 저장할 데이터 구조
        firestore_data = {
            # 기본 지원자 정보
            'name': applicant_data.get('name', ''),
            'phone': applicant_data.get('phone', ''),
            'instagram_url': applicant_data.get('instagram_url', ''),
            
            # 주소 정보
            'address': {
                'zipcode': applicant_data.get('address_zipcode', ''),
                'main': applicant_data.get('address_main', ''),
                'detail': applicant_data.get('address_detail', ''),
                'full': f"{applicant_data.get('address_main', '')} {applicant_data.get('address_detail', '')}".strip()
            },
            
            # 멤버십 정보
            'membership': {
                'is_member': membership_info.get('is_member', False),
                'branch_name': membership_info.get('branch_name', ''),
                'membership_name': membership_info.get('membership_name', ''),
                'start_date': membership_info.get('start_date', ''),
                'expiry_date': membership_info.get('expiry_date', ''),
                'status': membership_info.get('status', ''),
                'user_name': membership_info.get('user_name', '')
            },
            
            # Instagram 정보 (현재는 비활성화)
            'instagram': {
                'followers': 0,
                'following': 0,
                'posts': 0,
                'scraped': False,
                'note': '로컬 도구에서 별도 처리'
            },
            
            # 체험단 정보
            'experience_group': '오리지널소스 체험단',
            
            # 시스템 정보
            'submit_datetime': submit_datetime,
            'submit_timestamp': submit_datetime.timestamp(),
            'submit_date_str': submit_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            
            # 원본 데이터 (디버깅용)
            'raw_data': applicant_data
        }
        
        # Firestore 컬렉션에 저장 (자동 ID 생성)
        doc_ref = db.collection('submissions').add(firestore_data)
        document_id = doc_ref[1].id
        
        print(f"✅ Firestore 저장 완료: {document_id}")
        print(f"   이름: {applicant_data.get('name', '')}")
        print(f"   전화번호: {phone_number}")
        print(f"   멤버십: {membership_info.get('branch_name', '')} - {membership_info.get('membership_name', '')}")
        
        # 추가로 날짜별 컬렉션에도 저장 (검색 편의를 위해)
        date_str = submit_datetime.strftime('%Y-%m-%d')
        db.collection('submissions_by_date').document(date_str).collection('submissions').document(document_id).set(firestore_data)
        
        print(f"✅ 날짜별 컬렉션에도 저장 완료: {date_str}/{document_id}")
        
        return document_id
        
    except Exception as e:
        print(f"❌ Firestore 저장 실패: {e}")
        import traceback
        traceback.print_exc()
        return None

def scrape_instagram_profile_robust(instagram_url):
    """강화된 Instagram 스크래핑 - 빠른 제출을 위해 비활성화"""
    print(f"⚡ Instagram 스크래핑 비활성화 (빠른 제출): {instagram_url}")
    return {"followers": 0, "following": 0, "posts": 0, "success": False, "error": "스크래핑 비활성화 (로컬 도구 사용)"}

# PostgreSQL 연결 초기화는 필요할 때 지연 로딩
print("🔌 PostgreSQL 연결은 요청 시 초기화됩니다")

@https_fn.on_request(memory=1024)
def api(req):
    """메인 API 엔드포인트"""
    
    # CORS 헤더 설정
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Max-Age': '3600'
    }
    
    if req.method == 'OPTIONS':
        return ('', 204, headers)
    
    if req.path == '/applicants' and req.method == 'POST':
        try:
            # 지원자 데이터 받기
            applicant_data = req.get_json()
            
            if not applicant_data:
                return ({'error': '데이터가 없습니다.'}, 400, headers)
            
            # 메모리에도 저장 (fallback)
            applicants_data.append({
                **applicant_data,
                'timestamp': datetime.now().isoformat()
            })
            
            # Google Sheets와 Firestore에 빠른 업데이트 (Instagram 스크래핑 없이)
            def background_update():
                try:
                    # Google Sheets 업데이트
                    update_google_sheet(applicant_data)
                    print(f"✅ 빠른 Google Sheets 업데이트 완료")
                except Exception as e:
                    print(f"❌ Google Sheets 업데이트 실패: {e}")
                
                try:
                    # Firestore 백업 저장
                    doc_id = save_to_firestore(applicant_data)
                    if doc_id:
                        print(f"✅ Firestore 백업 저장 완료: {doc_id}")
                    else:
                        print(f"❌ Firestore 백업 저장 실패")
                except Exception as e:
                    print(f"❌ Firestore 백업 저장 실패: {e}")
            
            # 백그라운드 스레드로 빠른 실행
            threading.Thread(target=background_update).start()
            
            print(f"✅ 지원자 접수 완료: {applicant_data.get('name', '')}")
            
            return ({
                'success': True,
                'message': '지원이 정상적으로 접수되었습니다.',
                'applicant_id': len(applicants_data)
            }, 200, headers)
            
        except Exception as e:
            print(f"❌ 지원자 처리 오류: {e}")
            return ({'error': f'처리 중 오류가 발생했습니다: {str(e)}'}, 500, headers)
    
    # 기본 응답
    return ({'message': '버핏체험단 PLUS API', 'status': 'running'}, 200, headers)