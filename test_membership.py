#!/usr/bin/env python3
"""
멤버십 재등록 로직 테스트 스크립트
"""

import os

def test_membership_logic():
    """수정된 멤버십 재등록 로직 테스트"""
    
    print("🔍 멤버십 재등록 판별 로직 테스트")
    print("=" * 50)
    
    # PostgreSQL 연결 시도
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # 환경변수에서 DATABASE_URL 가져오기
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            print("❌ DATABASE_URL 환경변수가 설정되지 않았습니다.")
            print("💡 export DATABASE_URL='postgresql://...' 로 설정하세요")
            return
        
        print(f"✅ DATABASE_URL: {database_url[:50]}...")
        
        # 테스트 전화번호 (실제 데이터 확인)
        test_phone = input("📱 테스트할 전화번호를 입력하세요 (예: 010-1234-5678): ").strip()
        if not test_phone:
            test_phone = "010-1234-5678"  # 기본값
        
        # 전화번호 정규화
        clean_phone = test_phone.replace('-', '').replace(' ', '')
        
        # 수정된 멤버십 쿼리 실행
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
                AND a.title NOT LIKE '%건강 선물%'
                AND a.title NOT LIKE '%리뉴얼%'
                AND REPLACE(REPLACE(e.phone_number, '-', ''), ' ', '') = %s
                AND e.name NOT LIKE '%(탈퇴)%'
        ),
        current_membership AS (
            -- 오늘 기준으로 현재 사용 중인 멤버십
            SELECT *
            FROM membership_data
            WHERE CURRENT_DATE BETWEEN begin_date AND end_date
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
        
        # DB 연결 및 쿼리 실행
        conn = psycopg2.connect(database_url)
        with conn.cursor() as cursor:
            cursor.execute(query, [clean_phone])
            result = cursor.fetchone()
            
            if result:
                print("\n✅ 멤버십 조회 성공!")
                print("-" * 30)
                print(f"회원 이름: {result[0]}")
                print(f"지점: {result[1]}")
                print(f"멤버십: {result[2]}")
                print(f"시작일: {result[3]}")
                print(f"종료일: {result[4]}")
                print(f"상태: {result[5]}")
                print(f"🔥 재등록 상태: {result[6]}")
                print(f"미래 멤버십 여부: {result[7]}")
                print(f"미래 만료일: {result[8]}")
                
                print("\n📋 구글 시트 업데이트 값:")
                print(f"재등록여부 컬럼: {result[6]}")
                
            else:
                print(f"❌ 해당 전화번호의 멤버십을 찾을 수 없습니다: {test_phone}")
                
        conn.close()
        
    except ImportError:
        print("❌ psycopg2 모듈이 설치되지 않았습니다.")
        print("💡 pip install psycopg2-binary 로 설치하세요")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_membership_logic() 