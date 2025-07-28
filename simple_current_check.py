#!/usr/bin/env python3
"""
현재 활성 멤버십 간단 확인
"""

import psycopg2
from datetime import date

def check_current_membership():
    database_url = "postgresql://hycho:gaW4Charohchee5shigh0aemeeThohyu@butfitseoul-replica.cjilul7too7t.ap-northeast-2.rds.amazonaws.com:5432/master_20221217"
    phone = "01075599875"  # 010-7559-9875
    
    try:
        conn = psycopg2.connect(database_url)
        with conn.cursor() as cursor:
            
            print(f"🔍 현재 활성 멤버십 확인: {phone}")
            print("=" * 50)
            print(f"오늘 날짜: {date.today()}")
            
            # 현재 활성 멤버십 직접 확인
            cursor.execute("""
                SELECT
                    a.title AS product_name,
                    a.begin_date,
                    a.end_date,
                    d.name AS branch,
                    e.name AS user_name,
                    CURRENT_DATE
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
                    AND e.phone_number = %s
                    AND CURRENT_DATE BETWEEN a.begin_date AND a.end_date
                    AND e.name NOT LIKE %s
            """, ['%건강 선물%', '%리뉴얼%', phone, '%(탈퇴)%'])
            
            current_results = cursor.fetchall()
            
            if current_results:
                print(f"✅ 현재 활성 멤버십 {len(current_results)}개:")
                for product, start, end, branch, name, today_db in current_results:
                    print(f"  - {product} ({branch})")
                    print(f"    기간: {start} ~ {end}")
                    print(f"    회원: {name}")
                    print(f"    DB 현재날짜: {today_db}")
            else:
                print("❌ 현재 활성 멤버십 없음")
                print("\n🔍 이유 분석:")
                
                # 모든 유효 멤버십 조회
                cursor.execute("""
                    SELECT
                        a.title AS product_name,
                        a.begin_date,
                        a.end_date,
                        d.name AS branch,
                        e.name AS user_name,
                        CASE 
                            WHEN CURRENT_DATE < a.begin_date THEN '미래 시작'
                            WHEN CURRENT_DATE > a.end_date THEN '이미 만료' 
                            ELSE '현재 활성'
                        END as status
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
                        AND e.phone_number = %s
                    ORDER BY a.end_date DESC
                """, ['%건강 선물%', '%리뉴얼%', phone])
                
                all_valid = cursor.fetchall()
                print(f"  유효한 멤버십 {len(all_valid)}개:")
                for product, start, end, branch, name, status in all_valid:
                    print(f"    - {product} ({branch}) - {start} ~ {end} [{status}]")
                
                print(f"\n📝 결론: 이 전화번호는 현재 이용중인 멤버십이 없어서")
                print(f"     시트에 멤버십 정보가 표시되지 않는 것이 정상입니다!")
                
        conn.close()
        
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_current_membership() 