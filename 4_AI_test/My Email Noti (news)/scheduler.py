import schedule
import time
import datetime
from database import SessionLocal, Subscriber
from news_scraper import fetch_economic_news, summarize_news
from email_sender import send_news_email

def job(force=False, sender_name="🚀 데일리 경제 뉴스 브리핑", smtp_config=None):
    """
    뉴스레터 발송 작업. force=True일 경우 요일/시간 무시하고 즉시 발송
    """
    now = datetime.datetime.now()
    current_day = now.strftime("%a")
    current_time = now.strftime("%H:%M")
    
    db = SessionLocal()
    
    if force:
        # 강제 발송 시 모든 활성 구독자 대상
        subscribers = db.query(Subscriber).filter(Subscriber.is_active == True).all()
        print(f"[{now}] 강제 메일 발송 시작 (대상: {len(subscribers)}명)")
    else:
        # 스케줄에 맞는 구독자만 대상
        subscribers = db.query(Subscriber).filter(
            Subscriber.is_active == True,
            Subscriber.preferred_time == current_time,
            Subscriber.preferred_days.contains(current_day)
        ).all()
    
    if not subscribers:
        db.close()
        return

    # 뉴스 수집 및 요약
    raw_news = fetch_economic_news()
    summarized_news = summarize_news(raw_news)
    
    if not summarized_news:
        print("수집된 뉴스가 없습니다.")
        db.close()
        return

    # 모든 대상 구독자 이메일을 리스트로 추출
    email_list = [sub.email for sub in subscribers]
    
    # 단 한 번의 발송으로 모든 수신자에게 전송 (서로 노출됨)
    send_news_email(email_list, summarized_news, sender_name=sender_name, smtp_config=smtp_config)
    
    db.close()

def run_immediate(sender_name="🚀 데일리 경제 뉴스 브리핑", smtp_config=None):
    """외부에서 호출 가능한 즉시 발송 함수"""
    job(force=True, sender_name=sender_name, smtp_config=smtp_config)

# 매분마다 체크
schedule.every().minute.do(job)

if __name__ == "__main__":
    print("맞춤형 뉴스 레터 스케줄러가 실행 중입니다 (매분 체크)...")
    # 시작 시 테스트로 한 번 실행하고 싶다면 job() 호출 가능
    # job() 
    
    while True:
        schedule.run_pending()
        time.sleep(60)
