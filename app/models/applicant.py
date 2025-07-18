from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..database import Base


class ApplicationStatus(enum.Enum):
    """지원 상태"""
    PENDING = "pending"           # 대기중
    UNDER_REVIEW = "under_review" # 검토중  
    APPROVED = "approved"         # 승인
    REJECTED = "rejected"         # 거절
    CANCELLED = "cancelled"       # 취소


class Applicant(Base):
    """체험단 지원자 정보"""
    __tablename__ = "applicants"

    id = Column(Integer, primary_key=True, index=True)
    
    # 기본 정보
    name = Column(String(100), nullable=False, comment="이름")
    email = Column(String(255), unique=True, nullable=False, comment="이메일")
    phone = Column(String(20), nullable=True, comment="전화번호")
    age = Column(Integer, nullable=True, comment="나이")
    gender = Column(String(10), nullable=True, comment="성별")
    address = Column(Text, nullable=True, comment="주소")
    
    # 인스타그램 정보
    instagram_username = Column(String(100), nullable=True, comment="인스타그램 사용자명")
    instagram_url = Column(String(500), nullable=True, comment="인스타그램 URL")
    
    # 지원 관련
    motivation = Column(Text, nullable=True, comment="지원 동기")
    experience = Column(Text, nullable=True, comment="관련 경험")
    expectations = Column(Text, nullable=True, comment="기대사항")
    additional_info = Column(Text, nullable=True, comment="추가 정보")
    
    # 상태 관리
    status = Column(
        Enum(ApplicationStatus), 
        default=ApplicationStatus.PENDING, 
        comment="지원 상태"
    )
    
    # 시스템 정보
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일시")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정일시")
    is_active = Column(Boolean, default=True, comment="활성 상태")
    
    # 관리자 메모
    admin_notes = Column(Text, nullable=True, comment="관리자 메모")
    
    # 관계 (다른 모델과의 연결)
    instagram_info = relationship("InstagramInfo", back_populates="applicant", uselist=False)
    membership_info = relationship("MembershipInfo", back_populates="applicant", uselist=False)

    def __repr__(self):
        return f"<Applicant(id={self.id}, name='{self.name}', email='{self.email}')>" 