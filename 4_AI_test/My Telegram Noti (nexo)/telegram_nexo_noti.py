"""
=============================================================================
Telegram 정기 브리핑 스크립트
=============================================================================
실행 스케줄 (KST): 06:40 / 12:00 / 17:00 / 23:30 (하루 4회 실행)

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
# =============================================================================
# 1. Google News RSS - 뉴스 수집 (무료, API 키 불필요)
# =============================================================================
def fetch_google_news(query: str, count: int) -> list:
    """
    Google News RSS 피드를 사용하여 특정 키워드의 최신 뉴스를 수집한다.
    
    Args:
        query: 검색할 키워드 (예: "Nexo crypto", "cryptocurrency")
        count: 가져올 뉴스 개수
        
    Returns:
        뉴스 리스트 (각 항목: {title, url, published_at, source})
    """
    import urllib.parse
    # 검색 키워드를 URL 인코딩 처리하여 쿼리 스트링 구성
    encoded_query = urllib.parse.quote_plus(query)
    # 구글 뉴스 RSS URL (영어 뉴스 기준)
    rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"

    print(f"[INFO] Google News RSS에서 '{query}' 뉴스 수집 중...")

    try:
        # RSS 피드 파싱 수행
        feed = feedparser.parse(rss_url)

        if feed.bozo:
            # 파싱 중 경고나 에러가 발생한 경우 출력
            print(f"[경고] RSS 파싱 경고: {feed.bozo_exception}")

        entries = feed.entries

        if not entries:
            print(f"[경고] '{query}' 관련 뉴스를 찾을 수 없습니다.")
            return []

        # 최신순 정렬 (발행 시간 기준 내림차순)
        entries.sort(key=lambda x: x.get("published_parsed", (0,)), reverse=True)

        # 최신 뉴스 count개만 추출하여 데이터 정제
        news_list = []
        for item in entries[:count]:
            # Google News RSS에서 소스는 제목 뒤에 " - 소스명" 형태로 포함됨
            title_full = item.get("title", "제목 없음")

            # "뉴스 제목 - 출처" 형식에서 분리하여 제목과 언론사 분리
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

        print(f"[INFO] '{query}' 뉴스 {len(news_list)}건 수집 완료")
        return news_list

    except Exception as e:
        print(f"[오류] Google News RSS 수집 중 예외 발생: {e}")
        return []


def fetch_nexo_news(count: int = 3) -> list:
    """
    Nexo 관련 최신 뉴스를 수집한다. (기본 3건)
    """
    return fetch_google_news("Nexo crypto", count)


def fetch_crypto_news(count: int = 3) -> list:
    """
    암호화폐 관련 일반 최신 뉴스를 수집한다. (기본 3건)
    """
    return fetch_google_news("cryptocurrency", count)


# =============================================================================
# 2. 암호화폐 가격 정보 조회 (업비트 및 외부 API 사용, 무료)
# =============================================================================
def fetch_upbit_prices() -> dict:
    """
    업비트 API를 사용하여 USDT/KRW 및 BTC/KRW 현재 가격 정보를 조회한다.
    인증 없이 사용 가능한 공개 API이다.

    Returns:
        마켓 코드를 키로 하고 가격 정보를 값으로 하는 딕셔너리
    """
    # 업비트 Ticker API 엔드포인트
    url = "https://api.upbit.com/v1/ticker"
    params = {
        "markets": "KRW-USDT,KRW-BTC"    # USDT/KRW, BTC/KRW 마켓 동시 요청
    }
    headers = {
        "accept": "application/json"
    }

    print("[INFO] 업비트 현재가 조회 중 (USDT/KRW, BTC/KRW)...")

    prices = {}
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)

        if response.status_code == 200:
            data = response.json()

            # 조회된 각 마켓의 가격 정보 추출 및 결과 딕셔너리 구성
            for ticker in data:
                market = ticker.get("market")
                prices[market] = {
                    "trade_price": ticker.get("trade_price", 0),           # 현재가
                    "change": ticker.get("change", ""),                    # 전일 대비 (RISE/FALL/EVEN)
                    "change_rate": ticker.get("change_rate", 0),           # 전일 대비 변동률
                    "change_price": ticker.get("change_price", 0),         # 전일 대비 변동 금액
                    "high_price": ticker.get("high_price", 0),             # 당일 최고가
                    "low_price": ticker.get("low_price", 0),               # 당일 최저가
                    "prev_closing_price": ticker.get("prev_closing_price", 0),  # 전일 종가
                }
                print(f"[INFO] {market} 현재가: {prices[market]['trade_price']:,.0f}원")
            return prices
        else:
            print(f"[경고] 업비트 API 요청 실패: {response.status_code}")
            return {}

    except requests.exceptions.RequestException as e:
        print(f"[오류] 업비트 API 요청 중 예외 발생: {e}")
        return {}


def fetch_btc_usd_price() -> dict:
    """
    외부 API (Coinbase 또는 Binance)를 사용하여 BTC/USD 현재 가격 정보를 조회한다.

    Returns:
        BTC/USD 가격 정보 딕셔너리
    """
    print("[INFO] BTC/USD 현재가 조회 중...")

    # 1차 시도: Coinbase API 사용 (별도 인증 없이 빠르고 깔끔한 JSON 제공)
    try:
        url_coinbase = "https://api.coinbase.com/v2/prices/BTC-USD/spot"
        response = requests.get(url_coinbase, timeout=10)
        if response.status_code == 200:
            data = response.json()
            trade_price = float(data.get("data", {}).get("amount", 0))
            if trade_price > 0:
                print(f"[INFO] BTC/USD 현재가 (Coinbase): ${trade_price:,.2f}")
                return {"trade_price": trade_price, "source": "Coinbase"}
    except Exception as e:
        print(f"[경고] Coinbase API 조회 실패, 바이낸스 API로 재시도합니다. ({e})")

    # 2차 시도 (fallback): Binance API 사용 (안정적인 글로벌 대형 거래소 API)
    try:
        url_binance = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        response = requests.get(url_binance, timeout=10)
        if response.status_code == 200:
            data = response.json()
            trade_price = float(data.get("price", 0))
            if trade_price > 0:
                print(f"[INFO] BTC/USD 현재가 (Binance): ${trade_price:,.2f}")
                return {"trade_price": trade_price, "source": "Binance"}
    except Exception as e:
        print(f"[오류] Binance API 조회 실패: {e}")

    return {}


# =============================================================================
# 3. 메시지 텍스트 생성
# =============================================================================
def build_message(crypto_news: list, nexo_news: list, upbit_prices: dict, btc_usd_info: dict) -> str:
    """
    수집한 데이터를 Telegram 메시지 형태로 구성한다.
    Telegram은 HTML 형식을 지원하므로 HTML 태그를 사용한다.

    Args:
        crypto_news: 암호화폐 관련 최신 뉴스 리스트 (Top 3)
        nexo_news: Nexo 관련 최신 뉴스 리스트 (Top 3)
        upbit_prices: 업비트 가격 정보 딕셔너리 (USDT/KRW, BTC/KRW)
        btc_usd_info: 외부 API BTC/USD 가격 정보

    Returns:
        Telegram으로 전송할 HTML 메시지 문자열
    """
    # 현재 한국 시간 표시 형식 지정
    now_kst = datetime.now(KST)
    date_str = now_kst.strftime("%Y-%m-%d %H:%M KST")

    # --- 메시지 헤더 (HTML 형식) ---
    msg = f"📌 <b>정기 브리핑</b>\n"
    msg += f"🕐 {date_str}\n"
    msg += "━━━━━━━━━━━━━━━\n\n"

    # --- 암호화폐 시세 섹션 ---
    msg += "💰 <b>주요 암호화폐 시세</b>\n"

    # 1. 업비트 USDT/KRW 출력 처리
    usdt_info = upbit_prices.get("KRW-USDT")
    if usdt_info:
        trade_price = usdt_info.get("trade_price", 0)
        change = usdt_info.get("change", "")
        change_rate = usdt_info.get("change_rate", 0)
        change_price = usdt_info.get("change_price", 0)

        # 전일 대비 변동 방향에 따른 아이콘 및 기호 설정
        if change == "RISE":
            direction = "🔴 ▲"
            sign = "+"
        elif change == "FALL":
            direction = "🔵 ▼"
            sign = "-"
        else:
            direction = "⚪ ─"
            sign = ""

        msg += f"  USDT/KRW: <b>{trade_price:,.0f}원</b> ({direction} {sign}{change_price:,.0f}원, {sign}{change_rate * 100:.2f}%)\n"
    else:
        msg += "  USDT/KRW: ⚠️ 가격 정보를 가져올 수 없습니다.\n"

    # 2. 업비트 BTC/KRW 출력 처리
    btc_krw_info = upbit_prices.get("KRW-BTC")
    if btc_krw_info:
        trade_price = btc_krw_info.get("trade_price", 0)
        change = btc_krw_info.get("change", "")
        change_rate = btc_krw_info.get("change_rate", 0)
        change_price = btc_krw_info.get("change_price", 0)

        # 전일 대비 변동 방향에 따른 아이콘 및 기호 설정
        if change == "RISE":
            direction = "🔴 ▲"
            sign = "+"
        elif change == "FALL":
            direction = "🔵 ▼"
            sign = "-"
        else:
            direction = "⚪ ─"
            sign = ""

        msg += f"  BTC/KRW: <b>{trade_price:,.0f}원</b> ({direction} {sign}{change_price:,.0f}원, {sign}{change_rate * 100:.2f}%)\n"
    else:
        msg += "  BTC/KRW: ⚠️ 가격 정보를 가져올 수 없습니다.\n"

    # 3. BTC/USD 가격 정보 출력 처리
    if btc_usd_info:
        btc_usd_price = btc_usd_info.get("trade_price", 0)
        source = btc_usd_info.get("source", "API")
        msg += f"  BTC/USD: <b>${btc_usd_price:,.2f}</b> (출처: {source})\n"
    else:
        msg += "  BTC/USD: ⚠️ 가격 정보를 가져올 수 없습니다.\n"

    msg += "\n"

    # --- 암호화폐 관련 최신 뉴스 Top 3 섹션 ---
    msg += "📰 <b>암호화폐 관련 최신 뉴스 (Top 3)</b>\n"
    if crypto_news:
        for i, news in enumerate(crypto_news, 1):
            title = html_escape(news.get("title", "제목 없음"))
            source = html_escape(news.get("source", "알 수 없음"))
            url = news.get("url", "")

            # 발행 시간 파싱 및 한국 시간(KST)으로 변환
            published = news.get("published_at", "")
            time_str = ""
            if published:
                try:
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
        msg += "  ⚠️ 현재 암호화폐 관련 뉴스가 없습니다.\n"

    msg += "\n"

    # --- Nexo 최신 뉴스 섹션 ---
    msg += "📰 <b>Nexo 최신 뉴스 (Top 3)</b>\n"
    if nexo_news:
        for i, news in enumerate(nexo_news, 1):
            title = html_escape(news.get("title", "제목 없음"))
            source = html_escape(news.get("source", "알 수 없음"))
            url = news.get("url", "")

            # 발행 시간 파싱 및 한국 시간(KST)으로 변환
            published = news.get("published_at", "")
            time_str = ""
            if published:
                try:
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
    3. 암호화폐 및 Nexo 관련 뉴스 수집 (Google News RSS - 무료)
    4. 업비트 및 해외 API를 통해 시세 정보 조회
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
    # Step 3: 뉴스 수집 (Google News RSS - 무료)
    # -----------------------------------------------
    # 암호화폐 관련 최신 뉴스 Top 3 수집
    crypto_news = fetch_crypto_news(count=3)
    # Nexo 관련 최신 뉴스 Top 3 수집
    nexo_news = fetch_nexo_news(count=3)

    # -----------------------------------------------
    # Step 4: 암호화폐 시세 조회 (업비트 및 해외 API - 무료)
    # -----------------------------------------------
    # 업비트에서 USDT/KRW, BTC/KRW 가격 조회
    upbit_prices = fetch_upbit_prices()
    # 외부 API에서 BTC/USD 가격 조회
    btc_usd_price = fetch_btc_usd_price()

    # -----------------------------------------------
    # Step 5: 메시지 구성
    # -----------------------------------------------
    message = build_message(crypto_news, nexo_news, upbit_prices, btc_usd_price)
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
