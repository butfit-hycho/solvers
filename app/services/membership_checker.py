from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, date
import logging

from ..database import get_db

logger = logging.getLogger(__name__)


class MembershipChecker:
    """멤버십 검수 및 재등록 판별 서비스"""
    
    def __init__(self, db: Session = None):
        self.db = db or next(get_db())
    
    def get_current_membership_with_renewal_info(
        self, 
        branch_name: str = "신도림"
    ) -> List[Dict]:
        """
        현재 멤버십과 재등록 정보를 조회
        
        Args:
            branch_name: 지점명 (기본값: 신도림)
            
        Returns:
            현재 멤버십 회원 리스트와 재등록 여부 정보
        """
        
        # 사용자가 제공한 SQL 쿼리
        query = text("""
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
        """)
        
        try:
            result = self.db.execute(query, {"branch_name": f"%{branch_name}%"})
            rows = result.fetchall()
            
            # 결과를 딕셔너리 리스트로 변환
            columns = [
                "회원 이름", "전화번호", "생년월", "현재 멤버십 상품명", 
                "이용 시작일", "이용 종료일", "재등록 여부"
            ]
            
            membership_list = []
            for row in rows:
                member_data = dict(zip(columns, row))
                membership_list.append(member_data)
            
            logger.info(f"{branch_name} 지점 멤버십 조회 완료: {len(membership_list)}건")
            return membership_list
            
        except Exception as e:
            logger.error(f"멤버십 조회 중 오류 발생: {str(e)}")
            raise
    
    def check_renewal_status(self, user_id: int) -> Dict:
        """
        특정 사용자의 재등록 상태 확인
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            재등록 상태 정보
        """
        query = text("""
            WITH membership_data AS (
                SELECT
                    a.id AS mbs_id,
                    a.begin_date,
                    a.end_date,
                    a.title AS product_name,
                    e.id AS user_id,
                    e.name AS user_name
                FROM
                    b_payment_btransactionlog b
                LEFT JOIN b_class_bmembership a ON a.transaction_log_id = b.id
                LEFT JOIN b_class_bpass c ON c.id = a.b_pass_id
                LEFT JOIN user_user e ON e.id = c.user_id
                WHERE
                    a.refund_transaction_id IS NULL
                    AND a.id IS NOT NULL
                    AND e.id = :user_id
                    AND a.title NOT LIKE '%건강 선물%'
                    AND a.title NOT LIKE '%리뉴얼%'
            ),
            current_membership AS (
                SELECT *
                FROM membership_data
                WHERE CURRENT_DATE BETWEEN begin_date AND end_date
            ),
            future_memberships AS (
                SELECT *
                FROM membership_data
                WHERE begin_date > CURRENT_DATE
                ORDER BY begin_date ASC
            )
            SELECT 
                cm.user_name,
                cm.product_name AS current_product,
                cm.begin_date AS current_begin_date,
                cm.end_date AS current_end_date,
                fm.product_name AS next_product,
                fm.begin_date AS next_begin_date,
                fm.end_date AS next_end_date,
                CASE 
                    WHEN fm.begin_date IS NOT NULL THEN 'O'
                    ELSE 'X'
                END AS has_renewal
            FROM current_membership cm
            LEFT JOIN future_memberships fm ON cm.user_id = fm.user_id
            LIMIT 1
        """)
        
        try:
            result = self.db.execute(query, {"user_id": user_id})
            row = result.fetchone()
            
            if row:
                return {
                    "user_name": row[0],
                    "current_membership": {
                        "product_name": row[1],
                        "begin_date": row[2],
                        "end_date": row[3]
                    },
                    "next_membership": {
                        "product_name": row[4],
                        "begin_date": row[5],
                        "end_date": row[6]
                    } if row[4] else None,
                    "has_renewal": row[7] == 'O'
                }
            else:
                return {"user_name": None, "has_renewal": False}
                
        except Exception as e:
            logger.error(f"재등록 상태 확인 중 오류 발생: {str(e)}")
            raise
    
    def get_membership_statistics(self, branch_name: str = "신도림") -> Dict:
        """
        멤버십 통계 조회
        
        Args:
            branch_name: 지점명
            
        Returns:
            멤버십 통계 정보
        """
        query = text("""
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
                    AND d.name LIKE :branch_name
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
        """)
        
        try:
            result = self.db.execute(query, {"branch_name": f"%{branch_name}%"})
            row = result.fetchone()
            
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
            logger.error(f"멤버십 통계 조회 중 오류 발생: {str(e)}")
            raise
    
    def search_member_by_phone(self, phone_number: str) -> Optional[Dict]:
        """
        전화번호로 회원 검색
        
        Args:
            phone_number: 전화번호
            
        Returns:
            회원 정보 및 멤버십 상태
        """
        # 전화번호 정규화 (하이픈 제거)
        clean_phone = phone_number.replace("-", "").replace(" ", "")
        
        query = text("""
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
                    AND REPLACE(REPLACE(e.phone_number, '-', ''), ' ', '') LIKE :phone_number
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
        """)
        
        try:
            result = self.db.execute(query, {"phone_number": f"%{clean_phone}%"})
            row = result.fetchone()
            
            if row:
                return {
                    "user_id": row[0],
                    "user_name": row[1],
                    "phone_number": row[2],
                    "birth_date": row[3],
                    "total_memberships": row[4],
                    "latest_end_date": row[5],
                    "status": row[6]
                }
            else:
                return None
                
        except Exception as e:
            logger.error(f"회원 검색 중 오류 발생: {str(e)}")
            raise 