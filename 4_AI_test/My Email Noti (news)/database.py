from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import datetime
import os

# 데이터베이스 파일 경로 절대 경로로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "news_subscribers.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
# 세션 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 구독자 모델 정의
class Subscriber(Base):
    __tablename__ = "subscribers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    preferred_days = Column(String, default="Mon,Tue,Wed,Thu,Fri,Sat,Sun") # 구독 요일 (쉼표로 구분)
    preferred_time = Column(String, default="07:00") # 구독 시간 (HH:MM)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# 테이블 생성 함수
def init_db():
    Base.metadata.create_all(bind=engine)
    
    # 기본 수신인 추가 로직
    db = SessionLocal()
    default_emails = ["wowmsj79@gmail.com", "sangjoon.mo@samsung.com", "wowmsj79@naver.com"]
    for email in default_emails:
        existing = db.query(Subscriber).filter(Subscriber.email == email).first()
        if not existing:
            new_sub = Subscriber(
                email=email, 
                preferred_days="Mon,Tue,Wed,Thu,Fri", 
                preferred_time="07:00",
                is_active=True
            )
            db.add(new_sub)
    db.commit()
    db.close()
    print("데이터베이스 초기화 및 기본 수신인 등록 완료.")

if __name__ == "__main__":
    init_db()
    print("데이터베이스 및 기본 구독자 설정 완료.")
