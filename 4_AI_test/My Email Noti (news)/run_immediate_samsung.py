import scheduler
import datetime
import email_sender
import os

def main():
    print("=" * 50)
    print("[Samsung Account Mode] Newsletter Dispatching...")
    print(f"   Sender: sangjoon.mo@samsung.com")
    print(f"   Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 발신인 표시 이름을 강제로 변경하기 위해 임시로 환경변수나 설정을 조작할 수 있습니다.
    # 여기서는 email_sender의 발신자 이름을 sangjoon.mo@samsung.com으로 고정하여 실행합니다.
    
    # 삼성 계정 설정 로드
    samsung_config = {
        'user': os.getenv('SAMSUNG_SMTP_USER', 'sangjoon.mo@samsung.com'),
        'password': os.getenv('SAMSUNG_SMTP_PASSWORD'), # .env에서 로드 필요
        'server': os.getenv('SAMSUNG_SMTP_SERVER', 'smtp.office365.com'),
        'port': int(os.getenv('SAMSUNG_SMTP_PORT', 587))
    }
    
    if not samsung_config['password']:
        print("\n[ERROR] 삼성 계정 비밀번호가 .env 파일에 설정되지 않았습니다.")
        print("SAMSUNG_SMTP_PASSWORD 항목을 추가해 주세요.")
        return

    try:
        print(f"[INFO] Sending emails via REAL account: {samsung_config['user']}...")
        scheduler.run_immediate(
            sender_name="Samsung Economic Briefing",
            smtp_config=samsung_config
        )
        print(f"\n[SUCCESS] Newsletter sent from ACTUAL account: {samsung_config['user']}")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
