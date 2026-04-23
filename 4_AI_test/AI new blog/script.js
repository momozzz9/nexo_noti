/**
 * AI Pulse 블로그 - 실시간 뉴스 피드 + 인터랙티브 기능
 * 실행 시마다 최신 AI 뉴스를 RSS 피드에서 실시간으로 가져옵니다.
 */

// ===== RSS 피드 및 프록시 설정 =====
const CORS_PROXY = 'https://api.allorigins.win/raw?url=';
const RSS_FEEDS = [
  { name: 'The Verge AI', url: 'https://www.theverge.com/rss/ai-artificial-intelligence/index.xml' },
  { name: 'TechCrunch AI', url: 'https://techcrunch.com/category/artificial-intelligence/feed/' },
  { name: 'Ars Technica', url: 'https://feeds.arstechnica.com/arstechnica/technology-lab' },
];

// 디자인을 위한 상수
const TAG_STYLES = [
  { cls: 'tag-breaking', label: '🔴 BREAKING' },
  { cls: 'tag-trending', label: '📈 TRENDING' },
  { cls: 'tag-product', label: '🚀 PRODUCT' },
  { cls: 'tag-research', label: '🔬 RESEARCH' },
  { cls: 'tag-analysis', label: '📊 ANALYSIS' },
  { cls: 'tag-live', label: '⚡ LIVE' },
];
const GRADIENTS = ['g1', 'g2', 'g3', 'g4', 'g5'];

// ===== 초기화 =====
document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initScrollTop();
  initSearch();
  initCountUp();
  updateDateTime();
  fetchLiveNews(); // 실시간 뉴스 가져오기 시작
});

// ===== 실시간 뉴스 가져오기 로직 =====
async function fetchLiveNews() {
  const liveGrid = document.getElementById('live-news-grid');
  if (!liveGrid) return;

  // 로딩 상태 표시
  liveGrid.innerHTML = '<div class="loading-text" style="grid-column: 1/-1; text-align:center; padding: 3rem;"><span class="loading-spinner"></span>최신 글로벌 AI 뉴스를 동기화 중입니다...</div>';

  let allArticles = [];

  // 모든 피드에서 데이터 수집
  for (const feed of RSS_FEEDS) {
    const articles = await fetchFeed(feed);
    allArticles = allArticles.concat(articles);
  }

  // 날짜순 정렬 (최신순)
  allArticles.sort((a, b) => new Date(b.pubDate) - new Date(a.pubDate));

  // 데이터가 없을 경우 폴백 뉴스 사용
  let displayArticles = allArticles.slice(0, 9);
  if (displayArticles.length === 0) {
    displayArticles = getFallbackNews();
  }

  // 화면 렌더링
  renderNewsGrid(liveGrid, displayArticles);
}

// 개별 RSS 피드 파싱
async function fetchFeed(feed) {
  try {
    const response = await fetch(CORS_PROXY + encodeURIComponent(feed.url));
    const xmlText = await response.text();
    const parser = new DOMParser();
    const xml = parser.parseFromString(xmlText, "text/xml");
    const items = xml.querySelectorAll("item");

    return Array.from(items).slice(0, 5).map(item => {
      // 썸네일 이미지 추출 시도
      let thumb = '';
      const content = item.querySelector("description")?.textContent || '';
      const imgMatch = content.match(/<img[^>]+src="([^">]+)"/);
      if (imgMatch) thumb = imgMatch[1];

      return {
        title: item.querySelector("title")?.textContent || '제목 없음',
        description: stripHtml(item.querySelector("description")?.textContent || '').substring(0, 100),
        link: item.querySelector("link")?.textContent || '#',
        pubDate: item.querySelector("pubDate")?.textContent || new Date().toISOString(),
        source: feed.name,
        thumbnail: thumb
      };
    });
  } catch (e) {
    console.error(`피드 로딩 실패 (${feed.name}):`, e);
    return [];
  }
}

// 뉴스 그리드 렌더링
function renderNewsGrid(container, articles) {
  container.innerHTML = articles.map((article, i) => {
    const tag = TAG_STYLES[i % TAG_STYLES.length];
    const grad = GRADIENTS[i % GRADIENTS.length];
    const timeAgo = getTimeAgo(article.pubDate);

    return `
      <article class="card-news" onclick="window.open('${article.link}', '_blank')" style="animation-delay: ${i * 0.1}s">
        <div class="card-image">
          <div class="img-gradient ${grad}"></div>
          ${article.thumbnail ? `<img src="${article.thumbnail}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0.6;">` : ''}
          <div class="overlay"></div>
        </div>
        <div class="card-body">
          <span class="card-tag ${tag.cls}">${tag.label}</span>
          <h3 class="card-title">${article.title}</h3>
          <p class="card-excerpt">${article.description}...</p>
          <div class="card-meta">
            <div class="author"><span class="avatar">${article.source[0]}</span> ${article.source}</div>
            <span>${timeAgo}</span>
          </div>
        </div>
      </article>
    `;
  }).join('');
  
  // 애니메이션 적용
  initAnimations();
}

// ===== 폴백 뉴스 (오프라인/에러 시) =====
function getFallbackNews() {
  return [
    {
      title: "OpenAI, 차세대 추론 모델 'Strawberry' 통합 계획 발표",
      description: "더 복잡한 수학적 추론과 논리적 문제 해결이 가능한 새로운 엔진이 곧 GPT-5에 탑재될 예정입니다.",
      link: "#", pubDate: new Date().toISOString(), source: "AI Insight", thumbnail: ""
    },
    {
      title: "NVIDIA, 역대 최강 AI 칩 'Blackwell' 양산 돌입",
      description: "전 세계 데이터 센터의 연산 성능을 20배 이상 끌어올릴 새로운 GPU 아키텍처가 공급을 시작합니다.",
      link: "#", pubDate: new Date().toISOString(), source: "Tech Trend", thumbnail: ""
    },
    {
      title: "Google Gemini, 실시간 음성 대화 기능 'Live' 한국어 지원 시작",
      description: "이제 한국어로도 자연스러운 대화와 감정 표현이 가능한 Gemini Live를 모바일에서 만나볼 수 있습니다.",
      link: "#", pubDate: new Date().toISOString(), source: "Global News", thumbnail: ""
    }
  ];
}

// ===== 유틸리티 함수들 =====

function getTimeAgo(dateStr) {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}분 전`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}시간 전`;
  return `${Math.floor(hours / 24)}일 전`;
}

function stripHtml(html) {
  const tmp = document.createElement("div");
  tmp.innerHTML = html;
  return tmp.textContent || tmp.innerText || "";
}

function initNavbar() {
  const nav = document.getElementById('navbar');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 50) nav.classList.add('scrolled');
    else nav.classList.remove('scrolled');
  });
}

function initScrollTop() {
  const btn = document.getElementById('scrollTopBtn');
  window.addEventListener('scroll', () => {
    if (window.scrollY > 400) btn.classList.add('visible');
    else btn.classList.remove('visible');
  });
}

function scrollToTop() {
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function initAnimations() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.opacity = '1';
        entry.target.style.transform = 'translateY(0)';
      }
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.card-news, .trending-item, .timeline-item').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'all 0.6s cubic-bezier(0.22, 1, 0.36, 1)';
    observer.observe(el);
  });
}

function initSearch() {
  const input = document.getElementById('searchInput');
  input.addEventListener('input', (e) => {
    const val = e.target.value.toLowerCase();
    document.querySelectorAll('.card-news, .card-featured, .trending-item').forEach(el => {
      const text = el.textContent.toLowerCase();
      el.style.display = text.includes(val) ? '' : 'none';
    });
  });
}

function initCountUp() {
  const animate = (el, target) => {
    let curr = 0;
    const step = target / 50;
    const timer = setInterval(() => {
      curr += step;
      if (curr >= target) {
        el.textContent = target;
        clearInterval(timer);
      } else {
        el.textContent = Math.floor(curr);
      }
    }, 30);
  };
  
  const obs = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) {
      animate(document.getElementById('statArticles'), 247);
      animate(document.getElementById('statSources'), 52);
      obs.disconnect();
    }
  });
  obs.observe(document.querySelector('.hero-stats'));
}

function updateDateTime() {
  const badge = document.querySelector('.hero-badge');
  const update = () => {
    const now = new Date();
    const str = now.toLocaleDateString('ko-KR', { 
      year: 'numeric', month: 'long', day: 'numeric', 
      weekday: 'long', hour: '2-digit', minute: '2-digit' 
    });
    badge.innerHTML = `<span class="pulse"></span> 실시간 업데이트 · ${str}`;
  };
  update();
  setInterval(update, 60000);
}

function subscribe(e) {
  e.preventDefault();
  const btn = e.target.querySelector('button');
  btn.innerHTML = '✅ 구독 완료!';
  btn.style.background = 'linear-gradient(90deg, #10b981, #3b82f6)';
  e.target.querySelector('input').value = '';
}
