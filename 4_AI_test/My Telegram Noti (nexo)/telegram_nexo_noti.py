"""
=============================================================================
Telegram 정기 브리핑 스크립트
=============================================================================
실행 스케줄 (KST): 07:00 / 11:00 / 15:00 / 19:00 / 24:00 (4시간 간격, 하루 5회)

기능:
  1. Google News RSS를 통해 Nexo 관련 최신 뉴스 3건 수집 (무료, API 키 불필요)
  2. 업비트 API를 통해 USDT/KRW 현재가 조회 (무료, API 키 불필요)
  3. 수집한 정보를 Telegram Bot API로 전송 (무료)

필요한 환경 변수 (GitHub Actions Secrets 또는 로컬 .env):
  - TELEGRAM_BOT_TOKEN   : Telegram 봇 토큰 (@BotFather에서 발급)
  - TELEGRAM_CHAT_ID     : 메시지 수신할 Chat ID

Telegram 봇 설정 방법:
  1. Telegram에서 @BotFather 검색 → /newbot 명령으로 봇 생성
  2. 발급받은 Bot Token 저장
  3. 생성된 봇에게 아무 메시지 전송 (채팅방 활성화)
  4. https://api.telegram.org/bot{TOKEN}/getUpdates 접속하여 chat_id 확인
=============================================================================
"""

import os
import sys
import json
import requests
import feedparser
from datetime import datetime, timezone, timedelta
from html import escape as html_escape

# 보안 유틸리티 임포트
try:
    from utils.secret_guard import mask_text, check_env_files
except ImportError:
    # 유틸리티가 없는 경우를 대비한 기본 함수
    def mask_text(t): return t
    def check_env_files(d): pass

# =============================================
# Windows 콘솔 UTF-8 인코딩 설정
# (cp949에서 이모지 출력 시 UnicodeEncodeError 방지)
# =============================================
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr.reconfigure(encoding="utf-8")

# =============================================
# 한국 시간대 설정 (KST = UTC+9)
# =============================================
KST = timezone(timedelta(hours=9))


# =============================================================================
# .env 파일 로드 (로컬 테스트용)
# =============================================================================
def load_env_file():
    """
    .env 파일이 존재하면 환경 변수로 로드한다.
    GitHub Actions에서는 Secrets가 자동으로 환경 변수에 설정되므로 불필요.
    로컬 테스트 시에만 사용된다.
    """
    # 스크립트 파일과 같은 디렉토리의 .env 파일 경로
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, ".env")

    if os.path.exists(env_path):
        print("[INFO] .env 파일 로드 중...")
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                # 빈 줄이나 주석(#) 건너뛰기
                if not line or line.startswith("#"):
                    continue
                # KEY=VALUE 형식 파싱
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    # 기존 환경 변수가 없을 때만 설정 (Secrets 우선)
                    if key and not os.environ.get(key):
                        os.environ[key] = value
        print("[INFO] .env 파일 로드 완료")


def get_env_variable(name: str) -> str:
    """
    환경 변수에서 값을 가져오는 헬퍼 함수.
    환경 변수가 설정되지 않았으면 에러 메시지를 출력하고 종료한다.
    """
    value = os.environ.get(name)
    if not value:
        print(f"[오류] 환경 변수 '{name}'이(가) 설정되지 않았습니다.")
        sys.exit(1)
    return value


# =============================================================================
# 1. Google News RSS - Nexo 관련 최신 뉴스 수집 (무료, API 키 불필요)
# =============================================================================
def fetch_nexo_news(count: int = 3) -> list:
    """
    Google News RSS 피드를 사용하여 Nexo 관련 최신 뉴스를 수집한다.
    API 키가 필요 없고 완전 무료이다.

    Args:
        count: 가져올 뉴스 개수 (기본값: 3)

    Returns:
        뉴스 리스트 (각 항목: {title, url, published_at, source})
    """
    # Google News RSS 피드 URL
    # q=Nexo+crypto : "Nexo crypto" 키워드로 검색
    # hl=en-US      : 영어 뉴스
    # gl=US         : 미국 기준
    rss_url = "https://news.google.com/rss/search?q=Nexo+crypto&hl=en-US&gl=US&ceid=US:en"

    print("[INFO] Google News RSS에서 Nexo 뉴스 수집 중...")

    try:
        # RSS 피드 파싱
        feed = feedparser.parse(rss_url)

        if feed.bozo:
            # 파싱 에러가 발생한 경우
            print(f"[경고] RSS 파싱 경고: {feed.bozo_exception}")

        entries = feed.entries

        if not entries:
            print("[경고] Nexo 관련 뉴스를 찾을 수 없습니다.")
            return []

        # 최신순 정렬 (발행 시간 기준 내림차순)
        # feedparser의 entries는 기본적으로 최신순인 경우가 많으나 명시적으로 정렬 수행
        entries.sort(key=lambda x: x.get("published_parsed", (0,)), reverse=True)

        # 최신 뉴스 count개만 추출
        news_list = []
        for item in entries[:count]:
            # Google News RSS에서 소스는 제목 뒤에 " - 소스명" 형태로 포함됨
            title_full = item.get("title", "제목 없음")

            # "뉴스 제목 - 출처" 형식에서 분리
            if " - " in title_full:
                parts = title_full.rsplit(" - ", 1)
                title = parts[0]
                source = parts[1] if len(parts) > 1 else "알 수 없음"
            else:
                title = title_full
                source = "Google News"

            news = {
                "title": title,
                "url": item.get("link", ""),
                "published_at": item.get("published", ""),
                "source": source,
            }
            news_list.append(news)

        print(f"[INFO] Nexo 뉴스 {len(news_list)}건 수집 완료")
        return news_list

    except Exception as e:
        print(f"[오류] Google News RSS 수집 중 예외 발생: {e}")
        return []


# =============================================================================
# 2. 업비트 API - USDT/KRW 현재가 조회 (무료, API 키 불필요)
# =============================================================================
def fetch_upbit_usdt_price() -> dict:
    """
    업비트 API를 사용하여 USDT/KRW 현재 가격 정보를 조회한다.
    인증 없이 사용 가능한 공개 API이다.

    Returns:
        가격 정보 딕셔너리 (trade_price, change, change_rate, change_price 등)
    """
    # 업비트 Ticker API 엔드포인트
    url = "https://api.upbit.com/v1/ticker"
    params = {
        "markets": "KRW-USDT"    # USDT/KRW 마켓
    }
    headers = {
        "accept": "application/json"
    }

    print("[INFO] 업비트 USDT/KRW 현재가 조회 중...")

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # 업비트 API는 배열로 응답하므로 첫 번째 요소 추출
            if data and len(data) > 0:
                ticker = data[0]
                price_info = {
                    "trade_price": ticker.get("trade_price", 0),           # 현재가
                    "change": ticker.get("change", ""),                    # 전일 대비 (RISE/FALL/EVEN)
                    "change_rate": ticker.get("change_rate", 0),           # 전일 대비 변동률
                    "change_price": ticker.get("change_price", 0),         # 전일 대비 변동 금액
                    "high_price": ticker.get("high_price", 0),             # 당일 최고가
                    "low_price": ticker.get("low_price", 0),               # 당일 최저가
                    "prev_closing_price": ticker.get("prev_closing_price", 0),  # 전일 종가
                }
                print(f"[INFO] USDT/KRW 현재가: {price_info['trade_price']:,.0f}원")
                return price_info
            else:
                print("[경고] 업비트 API 응답 데이터가 비어있습니다.")
                return {}
        else:
            print(f"[경고] 업비트 API 요청 실패: {response.status_code}")
            return {}

    except requests.exceptions.RequestException as e:
        print(f"[오류] 업비트 API 요청 중 예외 발생: {e}")
        return {}


# =============================================================================
# 3. 메시지 텍스트 생성
# =============================================================================
def build_message(news_list: list, usdt_info: dict) -> str:
    """
    수집한 데이터를 Telegram 메시지 형태로 구성한다.
    Telegram은 HTML 형식을 지원하므로 HTML 태그를 사용한다.

    Args:
        news_list: Nexo 관련 뉴스 리스트
        usdt_info: 업비트 USDT/KRW 가격 정보

    Returns:
        Telegram으로 전송할 HTML 메시지 문자열
    """
    # 현재 한국 시간
    now_kst = datetime.now(KST)
    date_str = now_kst.strftime("%Y-%m-%d %H:%M KST")

    # --- 메시지 헤더 (HTML 형식) ---
    msg = f"📌 <b>정기 브리핑</b>\n"
    msg += f"🕐 {date_str}\n"
    msg += "━━━━━━━━━━━━━━━\n\n"

    # --- USDT/KRW 현재가 섹션 ---
    msg += "💰 <b>업비트 USDT/KRW</b>\n"

    if usdt_info:
        trade_price = usdt_info.get("trade_price", 0)
        change = usdt_info.get("change", "")
        change_rate = usdt_info.get("change_rate", 0)
        change_price = usdt_info.get("change_price", 0)

        # 전일 대비 방향 표시 (상승/하락/보합)
        if change == "RISE":
            direction = "🔴 ▲"
            sign = "+"
        elif change == "FALL":
            direction = "🔵 ▼"
            sign = "-"
        else:
            direction = "⚪ ─"
            sign = ""

        msg += f"  현재가: <b>{trade_price:,.0f}원</b>\n"
        msg += f"  전일비: {direction} {sign}{change_price:,.0f}원 ({sign}{change_rate * 100:.2f}%)\n"
        msg += f"  고가/저가: {usdt_info.get('high_price', 0):,.0f} / {usdt_info.get('low_price', 0):,.0f}원\n"
    else:
        msg += "  ⚠️ 가격 정보를 가져올 수 없습니다.\n"

    msg += "\n"

    # --- Nexo 뉴스 섹션 ---
    msg += "📰 <b>Nexo 최신 뉴스</b>\n"

    if news_list:
        for i, news in enumerate(news_list, 1):
            title = html_escape(news.get("title", "제목 없음"))
            source = html_escape(news.get("source", "알 수 없음"))
            url = news.get("url", "")

            # 발행 시간 파싱
            published = news.get("published_at", "")
            time_str = ""
            if published:
                try:
                    # feedparser가 반환하는 다양한 날짜 형식 처리
                    from email.utils import parsedate_to_datetime
                    pub_dt = parsedate_to_datetime(published)
                    pub_kst = pub_dt.astimezone(KST)
                    time_str = pub_kst.strftime("%m/%d %H:%M")
                except (ValueError, TypeError):
                    time_str = ""

            # HTML 링크로 뉴스 제목 구성
            if url:
                msg += f"\n{i}. <a href='{url}'>{title}</a>\n"
            else:
                msg += f"\n{i}. {title}\n"

            msg += f"   📎 {source}"
            if time_str:
                msg += f" | {time_str}"
            msg += "\n"
    else:
        msg += "  ⚠️ 현재 Nexo 관련 뉴스가 없습니다.\n"

    msg += "\n━━━━━━━━━━━━━━━"

    return msg


# =============================================================================
# 4. Telegram Bot으로 메시지 전송
# =============================================================================
def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    """
    Telegram Bot API를 사용하여 메시지를 전송한다.

    Args:
        bot_token: Telegram 봇 토큰
        chat_id: 메시지 수신할 Chat ID
        message: 전송할 메시지 텍스트 (HTML 형식)

    Returns:
        전송 성공 여부 (True/False)
    """
    # Telegram Bot API - sendMessage 엔드포인트
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    # 요청 데이터 구성
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",                   # HTML 형식 파싱 활성화
        "disable_web_page_preview": True,        # 링크 미리보기 비활성화 (깔끔한 메시지)
    }

    print("[INFO] Telegram 메시지 전송 중...")

    try:
        response = requests.post(url, json=payload, timeout=10)

        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                print("[INFO] ✅ Telegram 메시지 전송 성공!")
                return True
            else:
                # 민감 정보 마스킹 후 출력
                print(f"[경고] Telegram 전송 응답 오류: {mask_text(str(result))}")
                return False
        else:
            print(f"[오류] Telegram 메시지 전송 실패: {response.status_code}")
            # 민감 정보 마스킹 후 출력
            print(f"[오류] 응답: {mask_text(response.text)}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"[오류] Telegram API 요청 중 예외 발생: {e}")
        return False


# =============================================================================
# 메인 실행 함수
# =============================================================================
def main():
    """
    메인 실행 흐름:
    1. .env 파일 로드 (로컬 테스트용)
    2. 환경 변수에서 Telegram 토큰 로드
    3. Nexo 뉴스 수집 (Google News RSS - 무료)
    4. 업비트 USDT/KRW 현재가 조회 (무료)
    5. 메시지 구성
    6. Telegram 전송
    """
    print("=" * 50)
    print("🚀 정기 브리핑 시작")
    print(f"   실행 시간: {datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST')}")
    print("=" * 50)

    # -----------------------------------------------
    # Step 0: 보안 검사 (.env 파일 노출 경고)
    # -----------------------------------------------
    check_env_files(os.path.dirname(os.path.abspath(__file__)))

    # -----------------------------------------------
    # Step 1: .env 파일 로드 (로컬 테스트용)
    # -----------------------------------------------
    load_env_file()

    # -----------------------------------------------
    # Step 2: 환경 변수에서 Telegram 토큰 로드
    # -----------------------------------------------
    telegram_bot_token = get_env_variable("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = get_env_variable("TELEGRAM_CHAT_ID")

    # -----------------------------------------------
    # Step 3: Nexo 뉴스 수집 (Google News RSS - 무료)
    # -----------------------------------------------
    nexo_news = fetch_nexo_news(count=3)

    # -----------------------------------------------
    # Step 4: 업비트 USDT/KRW 현재가 조회 (무료)
    # -----------------------------------------------
    usdt_price = fetch_upbit_usdt_price()

    # -----------------------------------------------
    # Step 5: 메시지 구성
    # -----------------------------------------------
    message = build_message(nexo_news, usdt_price)
    print("\n--- 전송할 메시지 미리보기 ---")
    print(message)
    print("--- 미리보기 끝 ---\n")

    # -----------------------------------------------
    # Step 6: Telegram 전송
    # -----------------------------------------------
    success = send_telegram_message(telegram_bot_token, telegram_chat_id, message)

    if success:
        print("\n🎉 정기 브리핑 전송 완료!")
    else:
        print("\n❌ 정기 브리핑 전송 실패!")
        sys.exit(1)

# =============================================================================
# 스크립트 직접 실행 시 main() 호출
# =============================================================================
if __name__ == "__main__":
    main()
