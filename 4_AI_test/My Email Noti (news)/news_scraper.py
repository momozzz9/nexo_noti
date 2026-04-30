import requests
from bs4 import BeautifulSoup
import json

def fetch_economic_news():
    """
    구글 뉴스 경제 섹션에서 최신 뉴스를 스크래핑합니다.
    """
    # 구글 뉴스 한국 경제 섹션 (비즈니스 카테고리)
    url = "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=ko&gl=KR&ceid=KR:ko"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, features="xml")
        
        items = soup.find_all("item")
        news_list = []
        
        if not items:
            print("RSS 아이템을 찾을 수 없습니다. 구성을 확인해 주세요.")
            return []
            
        for item in items[:15]:
            news_list.append({
                "title": item.title.text,
                "link": item.link.text,
                "pubDate": item.pubDate.text if item.pubDate else "",
                "description": item.description.text if item.description else ""
            })
        
        print(f"{len(news_list)}건의 뉴스를 성공적으로 수집했습니다.")
        return news_list
    except Exception as e:
        print(f"뉴스 수집 중 오류 발생: {e}")
        return []

def summarize_news(news_list):
    """
    LLM을 사용하여 뉴스 리스트 중 상위 5개를 선정하고 요약합니다.
    (여기서는 데모를 위해 상위 5개를 선정하고 구조를 잡습니다.)
    실제 구현 시 OpenAI API 등을 연동할 수 있습니다.
    """
    # 실제 운영 시에는 이 부분에서 LLM API(OpenAI 등)를 호출하여 
    # 뉴스의 중요도를 판단하고 요약본을 생성합니다.
    
    # 예시 요약 데이터 (실제로는 LLM 결과값이 들어감)
    summarized_results = []
    
    # 상위 5개 뉴스 선택 (실제로는 LLM이 선택)
    top_5 = news_list[:5]
    
    for idx, news in enumerate(top_5):
        # 데모용 요약 텍스트 생성 (실제 API 호출 대체 영역)
        summary_text = f"본 뉴스는 {news['title']}에 대한 내용을 담고 있으며, 경제 시장의 주요 지표로 분석됩니다."
        
        summarized_results.append({
            "id": idx + 1,
            "title": news["title"],
            "link": news["link"],
            "summary": summary_text
        })
    
    return summarized_results

if __name__ == "__main__":
    raw_news = fetch_economic_news()
    summary = summarize_news(raw_news)
    print(json.dumps(summary, indent=4, ensure_ascii=False))
