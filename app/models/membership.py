from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..database import Base


class MembershipStatus(enum.Enum):
    """멤버십 상태"""
    ACTIVE = "active"         # 활성
    INACTIVE = "inactive"     # 비활성
    SUSPENDED = "suspended"   # 정지
    EXPIRED = "expired"       # 만료


class MembershipTier(enum.Enum):
    """멤버십 등급"""
    BRONZE = "bronze"     # 브론즈
    SILVER = "silver"     # 실버  
    GOLD = "gold"         # 골드
    PLATINUM = "platinum" # 플래티넘
    VIP = "vip"          # VIP


class MembershipInfo(Base):
    """회원 멤버십 정보"""
    __tablename__ = "membership_info"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id"), unique=True, comment="지원자 ID")
    
    # 멤버십 기본 정보
    membership_id = Column(String(100), unique=True, nullable=True, comment="멤버십 ID")
    is_member = Column(Boolean, default=False, comment="회원 여부")
    membership_tier = Column(Enum(MembershipTier), nullable=True, comment="멤버십 등급")
    membership_status = Column(Enum(MembershipStatus), nullable=True, comment="멤버십 상태")
    
    # 가입 정보
    joined_date = Column(DateTime, nullable=True, comment="가입일")
    expiry_date = Column(DateTime, nullable=True, comment="만료일")
    
    # 활동 이력
    previous_campaigns = Column(Text, nullable=True, comment="이전 체험단 참여 이력 (JSON)")
    total_campaigns_count = Column(Integer, default=0, comment="총 체험단 참여 횟수")
    last_campaign_date = Column(DateTime, nullable=True, comment="마지막 체험단 참여일")
    
    # 평가 정보
    average_rating = Column(String(10), nullable=True, comment="평균 평점")
    review_quality_score = Column(Integer, nullable=True, comment="리뷰 품질 점수 (1-100)")
    reliability_score = Column(Integer, nullable=True, comment="신뢰도 점수 (1-100)")
    
    # 제재 정보
    warnings_count = Column(Integer, default=0, comment="경고 횟수")
    is_blacklisted = Column(Boolean, default=False, comment="블랙리스트 여부")
    blacklist_reason = Column(Text, nullable=True, comment="블랙리스트 사유")
    blacklist_date = Column(DateTime, nullable=True, comment="블랙리스트 등록일")
    
    # 특이사항
    special_notes = Column(Text, nullable=True, comment="특이사항")
    preferred_categories = Column(Text, nullable=True, comment="선호 카테고리 (JSON)")
    
    # 검수 정보
    verification_status = Column(String(50), default="pending", comment="검수 상태")
    verified_at = Column(DateTime, nullable=True, comment="검수 완료일")
    verified_by = Column(String(100), nullable=True, comment="검수자")
    
    # 시스템 정보
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일시")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정일시")
    
    # 관계
    applicant = relationship("Applicant", back_populates="membership_info")

    def __repr__(self):
        return f"<MembershipInfo(id={self.id}, membership_id='{self.membership_id}', is_member={self.is_member})>"
    
    @property
    def is_eligible(self) -> bool:
        """체험단 참여 자격 여부"""
        if self.is_blacklisted:
            return False
        
        if self.membership_status == MembershipStatus.SUSPENDED:
            return False
            
        # 경고 3회 이상이면 부적격
        if self.warnings_count >= 3:
            return False
            
        return True
    
    @property
    def priority_score(self) -> int:
        """우선순위 점수 계산"""
        score = 0
        
        # 멤버십 등급에 따른 점수
        tier_scores = {
            MembershipTier.VIP: 100,
            MembershipTier.PLATINUM: 80,
            MembershipTier.GOLD: 60,
            MembershipTier.SILVER: 40,
            MembershipTier.BRONZE: 20
        }
        
        if self.membership_tier:
            score += tier_scores.get(self.membership_tier, 0)
        
        # 신뢰도 점수 추가
        if self.reliability_score:
            score += self.reliability_score // 10
            
        # 경고 횟수에 따른 감점
        score -= self.warnings_count * 10
        
        return max(0, score) 