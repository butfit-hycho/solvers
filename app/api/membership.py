from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from ..database import get_db
from ..services.membership_checker import MembershipChecker

router = APIRouter(prefix="/membership", tags=["membership"])


# Pydantic 모델들
class MembershipRenewalResponse(BaseModel):
    """멤버십 재등록 응답 모델"""
    회원_이름: str
    전화번호: str
    생년월: Optional[str]
    현재_멤버십_상품명: str
    이용_시작일: str
    이용_종료일: str
    재등록_여부: str


class MembershipStatisticsResponse(BaseModel):
    """멤버십 통계 응답 모델"""
    total_current_members: int
    members_with_renewal: int
    members_without_renewal: int
    renewal_rate_percentage: float


class MemberSearchResponse(BaseModel):
    """회원 검색 응답 모델"""
    user_id: int
    user_name: str
    phone_number: str
    birth_date: Optional[str]
    total_memberships: int
    latest_end_date: str
    status: str


class RenewalStatusResponse(BaseModel):
    """재등록 상태 응답 모델"""
    user_name: Optional[str]
    current_membership: Optional[Dict]
    next_membership: Optional[Dict]
    has_renewal: bool


@router.get(
    "/current-members", 
    response_model=List[Dict],
    summary="현재 멤버십 회원 및 재등록 정보 조회",
    description="지정된 지점의 현재 활성 멤버십 회원들과 재등록 여부를 조회합니다."
)
async def get_current_members_with_renewal(
    branch_name: str = Query(default="신도림", description="지점명"),
    db: Session = Depends(get_db)
):
    """
    현재 멤버십 회원 및 재등록 정보 조회
    
    **주요 기능:**
    - 현재 활성 멤버십 회원 목록 조회
    - 각 회원의 재등록 여부 확인
    - 재등록이 있는 경우 다음 멤버십 종료일 표시
    
    **사용 예시:**
    ```
    GET /membership/current-members?branch_name=신도림
    ```
    """
    try:
        checker = MembershipChecker(db)
        members = checker.get_current_membership_with_renewal_info(branch_name)
        
        return {
            "success": True,
            "data": members,
            "total_count": len(members),
            "branch_name": branch_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"멤버십 조회 중 오류 발생: {str(e)}")


@router.get(
    "/statistics",
    response_model=Dict,
    summary="멤버십 통계 조회",
    description="지정된 지점의 멤버십 관련 통계를 조회합니다."
)
async def get_membership_statistics(
    branch_name: str = Query(default="신도림", description="지점명"),
    db: Session = Depends(get_db)
):
    """
    멤버십 통계 조회
    
    **반환 정보:**
    - 현재 활성 멤버십 회원 수
    - 재등록이 있는 회원 수
    - 재등록이 없는 회원 수
    - 재등록률 (%)
    
    **사용 예시:**
    ```
    GET /membership/statistics?branch_name=신도림
    ```
    """
    try:
        checker = MembershipChecker(db)
        stats = checker.get_membership_statistics(branch_name)
        
        return {
            "success": True,
            "data": stats,
            "branch_name": branch_name
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류 발생: {str(e)}")


@router.get(
    "/search",
    response_model=Dict,
    summary="전화번호로 회원 검색",
    description="전화번호를 이용하여 회원 정보 및 멤버십 상태를 검색합니다."
)
async def search_member_by_phone(
    phone_number: str = Query(..., description="검색할 전화번호"),
    db: Session = Depends(get_db)
):
    """
    전화번호로 회원 검색
    
    **기능:**
    - 전화번호 부분 일치 검색
    - 회원의 멤버십 이력 조회
    - 현재 멤버십 상태 확인
    
    **사용 예시:**
    ```
    GET /membership/search?phone_number=010-1234-5678
    ```
    """
    try:
        checker = MembershipChecker(db)
        member = checker.search_member_by_phone(phone_number)
        
        if member:
            return {
                "success": True,
                "data": member,
                "found": True
            }
        else:
            return {
                "success": True,
                "data": None,
                "found": False,
                "message": "해당 전화번호로 등록된 회원을 찾을 수 없습니다."
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"회원 검색 중 오류 발생: {str(e)}")


@router.get(
    "/renewal-status/{user_id}",
    response_model=Dict,
    summary="개별 회원 재등록 상태 확인",
    description="특정 회원의 재등록 상태를 상세히 조회합니다."
)
async def get_renewal_status(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    개별 회원 재등록 상태 확인
    
    **반환 정보:**
    - 현재 멤버십 정보
    - 다음 멤버십 정보 (있는 경우)
    - 재등록 여부
    
    **사용 예시:**
    ```
    GET /membership/renewal-status/12345
    ```
    """
    try:
        checker = MembershipChecker(db)
        status = checker.check_renewal_status(user_id)
        
        return {
            "success": True,
            "data": status,
            "user_id": user_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"재등록 상태 확인 중 오류 발생: {str(e)}")


@router.get(
    "/export/csv",
    summary="멤버십 데이터 CSV 내보내기",
    description="현재 멤버십 데이터를 CSV 형식으로 내보냅니다."
)
async def export_membership_csv(
    branch_name: str = Query(default="신도림", description="지점명"),
    db: Session = Depends(get_db)
):
    """
    멤버십 데이터 CSV 내보내기
    
    **기능:**
    - 현재 활성 멤버십 데이터를 CSV로 변환
    - 다운로드 가능한 형태로 반환
    
    **사용 예시:**
    ```
    GET /membership/export/csv?branch_name=신도림
    ```
    """
    try:
        import csv
        import io
        from fastapi.responses import StreamingResponse
        
        checker = MembershipChecker(db)
        members = checker.get_current_membership_with_renewal_info(branch_name)
        
        # CSV 데이터 생성
        output = io.StringIO()
        writer = csv.writer(output)
        
        # 헤더 작성
        if members:
            headers = list(members[0].keys())
            writer.writerow(headers)
            
            # 데이터 작성
            for member in members:
                writer.writerow(list(member.values()))
        
        output.seek(0)
        
        # CSV 파일 응답
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8-sig')), 
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=membership_{branch_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV 내보내기 중 오류 발생: {str(e)}")


# 추가 유틸리티 엔드포인트들
@router.get(
    "/health",
    summary="멤버십 서비스 상태 확인",
    description="멤버십 서비스의 건강 상태를 확인합니다."
)
async def health_check(db: Session = Depends(get_db)):
    """
    멤버십 서비스 상태 확인
    """
    try:
        # 간단한 DB 연결 테스트
        result = db.execute("SELECT 1").fetchone()
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"서비스 상태 확인 실패: {str(e)}")


@router.get(
    "/branches",
    summary="이용 가능한 지점 목록",
    description="멤버십 데이터가 있는 지점들의 목록을 조회합니다."
)
async def get_available_branches(db: Session = Depends(get_db)):
    """
    이용 가능한 지점 목록 조회
    """
    try:
        from sqlalchemy import text
        
        query = text("""
            SELECT DISTINCT d.name AS branch_name, COUNT(*) AS member_count
            FROM b_payment_btransactionlog b
            LEFT JOIN b_class_bmembership a ON a.transaction_log_id = b.id
            LEFT JOIN b_class_bpass c ON c.id = a.b_pass_id
            LEFT JOIN b_class_bplace d ON d.id = b.b_place_id
            WHERE a.refund_transaction_id IS NULL
                AND a.id IS NOT NULL
                AND d.name IS NOT NULL
            GROUP BY d.name
            ORDER BY member_count DESC
        """)
        
        result = db.execute(query)
        branches = [{"branch_name": row[0], "member_count": row[1]} for row in result.fetchall()]
        
        return {
            "success": True,
            "data": branches,
            "total_branches": len(branches)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"지점 목록 조회 중 오류 발생: {str(e)}") 