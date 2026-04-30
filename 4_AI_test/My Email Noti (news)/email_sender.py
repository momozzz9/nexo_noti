import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Template

import os
from dotenv import load_dotenv

# .env 파일 로드 (절대 경로)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

# SMTP 설정 (환경 변수에서 로드)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; line-height: 1.6; color: #333; background-color: #f4f7f6; margin: 0; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: #ffffff; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
        .header { text-align: center; border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 20px; }
        .header h1 { color: #2c3e50; font-size: 24px; margin: 0; }
        .date { font-size: 14px; color: #7f8c8d; }
        .news-item { margin-bottom: 25px; padding: 15px; border-left: 4px solid #3498db; background: #f9fbfd; border-radius: 0 8px 8px 0; }
        .news-title { font-weight: bold; font-size: 18px; color: #2980b9; text-decoration: none; display: block; margin-bottom: 8px; }
        .news-summary { font-size: 15px; color: #444; }
        .footer { text-align: center; margin-top: 30px; font-size: 12px; color: #bdc3c7; }
        .btn { display: inline-block; padding: 10px 20px; background-color: #3498db; color: white; text-decoration: none; border-radius: 5px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 데일리 경제 뉴스 브리핑</h1>
            <p class="date">{{ today }}</p>
        </div>
        
        {% for news in news_list %}
        <div class="news-item">
            <a href="{{ news.link }}" class="news-title">{{ news.title }}</a>
            <div class="news-summary">
                {{ news.summary }}
            </div>
        </div>
        {% endfor %}
        
        <div class="footer">
            <div style="margin-bottom: 20px; padding: 15px; background: #fdfdfd; border: 1px solid #eee; border-radius: 10px;">
                <p style="margin: 0 0 10px 0; font-weight: bold; color: #3498db;">⚙️ 구독 관리 도구</p>
                <a href="http://localhost:8000" style="display: inline-block; margin: 5px; padding: 8px 15px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; font-size: 13px;">📅 요일/시간 변경</a>
                <a href="http://localhost:8000" style="display: inline-block; margin: 5px; padding: 8px 15px; background: #9b59b6; color: white; text-decoration: none; border-radius: 5px; font-size: 13px;">👤 수신인 추가</a>
                <a href="http://localhost:8000" style="display: inline-block; margin: 5px; padding: 8px 15px; background: #27ae60; color: white; text-decoration: none; border-radius: 5px; font-size: 13px;">🔗 서비스 추천하기</a>
            </div>
            <p>본 메일은 구독자님께만 발송되는 자동 요약 서비스입니다.</p>
            <p>© 2026 Antigravity News Automation. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

def send_news_email(recipient_emails, news_list, sender_name="🚀 데일리 경제 뉴스 브리핑", smtp_config=None):
    """
    구성된 뉴스 요약본을 발송합니다. 
    smtp_config가 주어지면 해당 계정으로 발송합니다.
    """
    import datetime
    import smtplib
    today = datetime.datetime.now().strftime("%Y년 %m월 %d일")
    
    # 기본 설정 (기존 Gmail)
    user = SMTP_USER
    password = SMTP_PASSWORD
    server_addr = SMTP_SERVER
    port = SMTP_PORT
    
    # 삼성 계정 등 커스텀 설정이 들어온 경우 교체
    if smtp_config:
        user = smtp_config.get('user', user)
        password = smtp_config.get('password', password)
        server_addr = smtp_config.get('server', server_addr)
        port = smtp_config.get('port', port)
        # 발신자 이름도 이메일 주소로 변경 (요청 사항)
        sender_display = f"{sender_name} <{user}>"
    else:
        sender_display = f"{sender_name} <{user}>"
    
    msg = MIMEMultipart()
    msg['From'] = sender_display
    
    # 여러 수신인을 쉼표로 연결하여 To 필드에 설정
    if isinstance(recipient_emails, list):
        msg['To'] = ", ".join(recipient_emails)
    else:
        msg['To'] = recipient_emails
    
    msg['Subject'] = f"[경제 브리핑] {today} 주요 뉴스 요약"
    
    # Jinja2 템플릿 렌더링
    template = Template(HTML_TEMPLATE)
    html_content = template.render(today=today, news_list=news_list)
    
    msg.attach(MIMEText(html_content, 'html'))

    # 실제 메일 전송
    try:
        server = smtplib.SMTP(server_addr, port)
        server.starttls()
        server.login(user, password)
        server.send_message(msg)
        server.quit()
        print(f"[{recipient_emails}] 메일 발송 성공! (발신처: {user})")
        return True
    except Exception as e:
        print(f"메일 발송 오류 ({user}): {e}")
        return False

if __name__ == "__main__":
    # 테스트 데이터
    test_news = [
        {"title": "테스트 뉴스 제목", "link": "#", "summary": "이것은 이메일 발송 테스트를 위한 요약 내용입니다."}
    ]
    send_news_email("wowmsj79@gmail.com", test_news)
