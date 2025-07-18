from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class InstagramInfo(Base):
    """인스타그램 계정 정보"""
    __tablename__ = "instagram_info"

    id = Column(Integer, primary_key=True, index=True)
    applicant_id = Column(Integer, ForeignKey("applicants.id"), unique=True, comment="지원자 ID")
    
    # 기본 계정 정보
    username = Column(String(100), nullable=False, comment="사용자명")
    full_name = Column(String(200), nullable=True, comment="프로필 이름")
    bio = Column(Text, nullable=True, comment="프로필 소개")
    profile_picture_url = Column(String(500), nullable=True, comment="프로필 사진 URL")
    
    # 통계 정보
    followers_count = Column(Integer, nullable=True, comment="팔로워 수")
    following_count = Column(Integer, nullable=True, comment="팔로잉 수")
    posts_count = Column(Integer, nullable=True, comment="게시물 수")
    
    # 계정 상태
    is_private = Column(Boolean, nullable=True, comment="비공개 계정 여부")
    is_verified = Column(Boolean, nullable=True, comment="인증 계정 여부")
    is_business = Column(Boolean, nullable=True, comment="비즈니스 계정 여부")
    
    # 활동 분석
    avg_likes = Column(Float, nullable=True, comment="평균 좋아요 수")
    avg_comments = Column(Float, nullable=True, comment="평균 댓글 수")
    engagement_rate = Column(Float, nullable=True, comment="참여도 (%)")
    last_post_date = Column(DateTime, nullable=True, comment="최근 게시물 날짜")
    
    # 카테고리 분석
    content_categories = Column(Text, nullable=True, comment="콘텐츠 카테고리 (JSON)")
    hashtags_used = Column(Text, nullable=True, comment="자주 사용하는 해시태그 (JSON)")
    
    # 인플루언서 등급
    influencer_tier = Column(String(50), nullable=True, comment="인플루언서 등급")
    influence_score = Column(Float, nullable=True, comment="영향력 점수")
    
    # 스크래핑 정보
    scraped_at = Column(DateTime, nullable=True, comment="스크래핑 일시")
    scraping_success = Column(Boolean, default=False, comment="스크래핑 성공 여부")
    scraping_error = Column(Text, nullable=True, comment="스크래핑 오류 메시지")
    
    # 시스템 정보
    created_at = Column(DateTime, default=datetime.utcnow, comment="생성일시")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="수정일시")
    
    # 관계
    applicant = relationship("Applicant", back_populates="instagram_info")

    def __repr__(self):
        return f"<InstagramInfo(id={self.id}, username='{self.username}', followers={self.followers_count})>"
    
    @property
    def follower_tier(self) -> str:
        """팔로워 수에 따른 등급 분류"""
        if not self.followers_count:
            return "Unknown"
        
        if self.followers_count < 1000:
            return "Nano"      # 나노 인플루언서
        elif self.followers_count < 10000:
            return "Micro"     # 마이크로 인플루언서
        elif self.followers_count < 100000:
            return "Mid"       # 미드 인플루언서
        elif self.followers_count < 1000000:
            return "Macro"     # 매크로 인플루언서
        else:
            return "Mega"      # 메가 인플루언서 