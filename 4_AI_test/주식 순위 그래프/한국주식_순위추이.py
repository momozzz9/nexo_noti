import yfinance as yf
import pandas as pd
import json
import os

def create_chart():
    print("데이터를 수집하는 중입니다... (약 1~2분 소요될 수 있습니다)")
    tickers = {
        '005930.KS': '삼성전자',
        '000660.KS': 'SK하이닉스',
        '005380.KS': '현대차',
        '000270.KS': '기아',
        '051910.KS': 'LG화학',
        '005490.KS': 'POSCO홀딩스',
        '035420.KS': 'NAVER',
        '035720.KS': '카카오',
        '068270.KS': '셀트리온',
        '207940.KS': '삼성바이오로직스',
        '373220.KS': 'LG에너지솔루션',
        '105560.KS': 'KB금융',
        '055550.KS': '신한지주',
        '006400.KS': '삼성SDI',
        '012330.KS': '현대모비스',
        '017670.KS': 'SK텔레콤',
        '066570.KS': 'LG전자',
        '028260.KS': '삼성물산',
        '086790.KS': '하나금융지주',
        '015760.KS': '한국전력',
        '033780.KS': 'KT&G',
        '096770.KS': 'SK이노베이션',
        '010130.KS': '고려아연',
        '032830.KS': '삼성생명',
        '003550.KS': 'LG',
        '034730.KS': 'SK',
        '011200.KS': 'HMM',
        '323410.KS': '카카오뱅크',
        '259960.KS': '크래프톤'
    }

    start_date = '2004-01-01'
    end_date = '2024-01-01'

    shares = {}
    print("종목별 주식수를 확인합니다...")
    for t in tickers.keys():
        try:
            info = yf.Ticker(t).info
            s = info.get('sharesOutstanding')
            if not s:
                s = info.get('impliedSharesOutstanding')
            if not s:
                s = 10000000 
            shares[t] = s
        except:
            shares[t] = 10000000

    print("주가 데이터를 다운로드합니다...")
    
    all_data = []

    print("데이터를 변환합니다...")
    for t in tickers.keys():
        try:
            df = yf.download(t, start=start_date, end=end_date, interval='1mo', progress=False)
            if df.empty:
                continue
            
            # 일부 버전에서 Adj Close 대신 Close 사용
            price_col = 'Adj Close' if 'Adj Close' in df.columns else 'Close'
            # yfinance 최신버전(MultiIndex) 대응
            if isinstance(df.columns, pd.MultiIndex):
                # 단일 종목 다운로드 시 MultiIndex의 최상위가 Price, 두번째가 Ticker일 수 있음
                if ('Adj Close', t) in df.columns:
                    price_series = df[('Adj Close', t)]
                elif ('Close', t) in df.columns:
                    price_series = df[('Close', t)]
                else:
                    price_series = df.iloc[:, 0] # fallback
            else:
                price_series = df[price_col] if price_col in df.columns else df.iloc[:, 0]

            price_series = price_series.ffill().fillna(0)
            
            for date, price in price_series.items():
                if pd.notna(price) and price > 0:
                    try:
                        price_val = float(price.iloc[0]) if isinstance(price, pd.Series) else float(price)
                        market_cap = (price_val * shares[t]) / 1_000_000_000
                        
                        all_data.append({
                            'date': date.strftime('%Y-%m'),
                            'name': tickers[t],
                            'value': round(market_cap, 2)
                        })
                    except Exception as e:
                        pass
        except Exception as e:
            print(f"{tickers[t]} 다운로드 실패: {e}")

    html_template = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>한국주식 순위추이 (Top 10)</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        :root {
            --bg-color: #0d1117;
            --panel-bg: #161b22;
            --text-color: #c9d1d9;
            --accent: #58a6ff;
            --btn-hover: #1f6feb;
        }
        body { font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; background: var(--bg-color); color: var(--text-color); margin: 0; padding: 30px; display: flex; flex-direction: column; align-items: center; }
        h1 { color: #fff; font-size: 32px; margin-bottom: 5px; font-weight: 800; }
        .subtitle { color: #8b949e; margin-bottom: 30px; font-size: 15px; }
        #chart-container { width: 100%; max-width: 1100px; background: var(--panel-bg); padding: 30px 20px; border-radius: 16px; box-shadow: 0 8px 24px rgba(0,0,0,0.6); border: 1px solid #30363d; }
        .controls { display: flex; justify-content: center; align-items: center; gap: 15px; margin-bottom: 25px; flex-wrap: wrap; }
        button { background: var(--accent); color: #fff; border: none; padding: 12px 28px; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; transition: all 0.2s; display: flex; align-items: center; gap: 8px; }
        button:hover { background: var(--btn-hover); transform: translateY(-2px); }
        button:active { transform: translateY(0); }
        button#replay { background: #238636; }
        button#replay:hover { background: #2ea043; }
        .slider-container { display: flex; align-items: center; gap: 12px; background: #21262d; padding: 10px 20px; border-radius: 8px; border: 1px solid #30363d; }
        input[type=range] { cursor: pointer; width: 180px; accent-color: var(--accent); }
        text { fill: var(--text-color); }
        .tick text { fill: #8b949e; font-size: 14px; }
        .tick line { stroke: #30363d; }
        .domain { display: none; }
        .bar { border-radius: 6px; }
        .label { font-weight: bold; font-size: 16px; fill: #fff; }
        .value { font-size: 15px; fill: #8b949e; font-variant-numeric: tabular-nums; }
        .date-label { font-size: 72px; font-weight: 900; fill: rgba(255,255,255,0.1); text-anchor: end; }
    </style>
</head>
<body>
    <h1>한국주식 시가총액 Top 10 순위추이 (2004~2024)</h1>
    <div class="subtitle">* 실제 데이터를 로드하려면 파이썬 스크립트(한국주식_순위추이.py)를 실행해주세요. (현재 샘플 데이터 표시 중)</div>
    
    <div id="chart-container">
        <div class="controls">
            <button id="play-pause">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" id="play-icon"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                <span id="play-text">Play</span>
            </button>
            <button id="replay">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg>
                Replay
            </button>
            <div class="slider-container">
                <label for="speed">속도: <span id="speed-val">500</span>ms</label>
                <input type="range" id="speed" min="100" max="2000" step="100" value="500">
            </div>
        </div>
        <div id="chart"></div>
    </div>

    <script>
        // 파이썬에서 실제 데이터 주입 시 __DATA__ 를 치환합니다.
        let rawData = '__DATA__';
        let data = [];

        if (typeof rawData !== 'string' || rawData !== '__' + 'DATA__') {
            // If it's already an object (because Python replaced the quotes too), use it directly
            data = typeof rawData === 'string' ? JSON.parse(rawData) : rawData;
            document.querySelector('.subtitle').innerHTML = "* 시가총액 단위: 10억원 (현재 발행주식수 기준 과거 추정치)";
        } else {
            // 샘플 데이터 생성
            const companies = ["삼성전자", "SK하이닉스", "현대차", "기아", "LG화학", "POSCO홀딩스", "NAVER", "카카오", "셀트리온", "KB금융"];
            let currentDate = new Date(2004, 0, 1);
            let endMockDate = new Date(2024, 0, 1);
            let values = companies.map(() => Math.random() * 50000 + 10000);
            
            while(currentDate <= endMockDate) {
                let dateStr = currentDate.toISOString().slice(0,7);
                for(let i=0; i<companies.length; i++) {
                    values[i] += (Math.random() - 0.45) * 5000;
                    if(values[i] < 1000) values[i] = 1000 + Math.random()*1000;
                    
                    if(companies[i] === "삼성전자") values[i] += 1000;
                    if(currentDate.getFullYear() > 2018 && companies[i] === "SK하이닉스") values[i] += 800;
                    if(currentDate.getFullYear() > 2020 && companies[i] === "NAVER") values[i] += 1200;
                    
                    data.push({
                        date: dateStr,
                        name: companies[i],
                        value: values[i]
                    });
                }
                currentDate.setMonth(currentDate.getMonth() + 1);
            }
        }

        const n = 10;
        const margin = {top: 40, right: 80, bottom: 20, left: 160};
        const width = 1000;
        const height = 600;
        const barSize = 48;

        const colors = [
            "#58a6ff", "#3fb950", "#d29922", "#f85149", "#a371f7", 
            "#2ea043", "#db6d28", "#8957e5", "#e3b341", "#f0883e",
            "#1f6feb", "#238636", "#9e6a03", "#da3633", "#8250df"
        ];
        const colorScale = d3.scaleOrdinal(colors);

        const dataByDate = d3.group(data, d => d.date);
        const dates = Array.from(dataByDate.keys()).sort();

        const rankedData = dates.map(date => {
            let entries = dataByDate.get(date);
            entries.sort((a, b) => d3.descending(a.value, b.value));
            return {
                date: date,
                entries: entries.slice(0, n).map((d, i) => ({...d, rank: i}))
            };
        });

        const svg = d3.select("#chart").append("svg")
            .attr("viewBox", [0, 0, width, height])
            .attr("width", "100%")
            .attr("height", height);

        const x = d3.scaleLinear().range([margin.left, width - margin.right]);
        const y = d3.scaleBand()
            .domain(d3.range(n))
            .range([margin.top, margin.top + barSize * n])
            .padding(0.15);

        const xAxis = d3.axisTop(x)
            .ticks(width / 160)
            .tickFormat(d => d3.formatPrefix(".1~s", d)(d));

        const gX = svg.append("g")
            .attr("class", "tick")
            .attr("transform", `translate(0,${margin.top})`);

        const gBars = svg.append("g");
        const gLabels = svg.append("g");

        const dateLabel = svg.append("text")
            .attr("class", "date-label")
            .attr("x", width - margin.right)
            .attr("y", height - margin.bottom)
            .text(dates[0].replace("-", ". "));

        let currentFrame = 0;
        let tickDuration = 500;
        let timer = null;
        let isPlaying = false;

        const playIcon = `<polygon points="5 3 19 12 5 21 5 3"></polygon>`;
        const pauseIcon = `<rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect>`;

        function update(frameIndex) {
            const frameData = rankedData[frameIndex];
            if (!frameData) return;

            dateLabel.text(frameData.date.replace("-", ". "));

            x.domain([0, d3.max(frameData.entries, d => d.value)]);
            gX.transition().duration(tickDuration).ease(d3.easeLinear).call(xAxis);

            const bars = gBars.selectAll("rect")
                .data(frameData.entries, d => d.name);

            bars.join(
                enter => enter.append("rect")
                    .attr("fill", d => colorScale(d.name))
                    .attr("x", margin.left)
                    .attr("y", margin.top + barSize * n)
                    .attr("width", d => Math.max(0, x(d.value) - margin.left))
                    .attr("height", y.bandwidth())
                    .attr("rx", 6)
                    .call(enter => enter.transition().duration(tickDuration).ease(d3.easeLinear)
                        .attr("y", d => y(d.rank))),
                update => update.call(update => update.transition().duration(tickDuration).ease(d3.easeLinear)
                    .attr("x", margin.left)
                    .attr("y", d => y(d.rank))
                    .attr("width", d => Math.max(0, x(d.value) - margin.left))),
                exit => exit.call(exit => exit.transition().duration(tickDuration).ease(d3.easeLinear)
                    .attr("width", 0)
                    .attr("y", margin.top + barSize * n)
                    .remove())
            );

            const labels = gLabels.selectAll("text.label")
                .data(frameData.entries, d => d.name);

            labels.join(
                enter => enter.append("text")
                    .attr("class", "label")
                    .attr("text-anchor", "end")
                    .attr("x", margin.left - 15)
                    .attr("y", margin.top + barSize * n + y.bandwidth() / 2 + 5)
                    .text(d => d.name)
                    .call(enter => enter.transition().duration(tickDuration).ease(d3.easeLinear)
                        .attr("y", d => y(d.rank) + y.bandwidth() / 2 + 5)),
                update => update.call(update => update.transition().duration(tickDuration).ease(d3.easeLinear)
                    .attr("y", d => y(d.rank) + y.bandwidth() / 2 + 5)),
                exit => exit.call(exit => exit.transition().duration(tickDuration).ease(d3.easeLinear)
                    .attr("y", margin.top + barSize * n + y.bandwidth() / 2 + 5)
                    .remove())
            );

            const values = gLabels.selectAll("text.value")
                .data(frameData.entries, d => d.name);

            values.join(
                enter => enter.append("text")
                    .attr("class", "value")
                    .attr("x", d => Math.max(margin.left, x(d.value)) + 12)
                    .attr("y", margin.top + barSize * n + y.bandwidth() / 2 + 5)
                    .text(d => d3.format(",.0f")(d.value))
                    .call(enter => enter.transition().duration(tickDuration).ease(d3.easeLinear)
                        .attr("y", d => y(d.rank) + y.bandwidth() / 2 + 5)),
                update => update.call(update => update.transition().duration(tickDuration).ease(d3.easeLinear)
                    .attr("x", d => Math.max(margin.left, x(d.value)) + 12)
                    .attr("y", d => y(d.rank) + y.bandwidth() / 2 + 5)
                    .tween("text", function(d) {
                        const i = d3.interpolateRound(parseInt(this.textContent.replace(/,/g, '')) || 0, d.value);
                        return function(t) {
                            this.textContent = d3.format(",.0f")(i(t));
                        };
                    })),
                exit => exit.call(exit => exit.transition().duration(tickDuration).ease(d3.easeLinear)
                    .attr("x", margin.left)
                    .attr("y", margin.top + barSize * n + y.bandwidth() / 2 + 5)
                    .remove())
            );
        }

        function step() {
            if (currentFrame >= rankedData.length - 1) {
                pause();
                // 애니메이션 종료 알림 (중복 발생 방지)
                if (!window.finishedNotified) {
                    window.finishedNotified = true;
                    setTimeout(() => alert("최근 연도까지 모든 순위추이 재생이 완료되었습니다!"), 300);
                }
                return;
            }
            currentFrame++;
            update(currentFrame);
            if (isPlaying) {
                timer = setTimeout(step, tickDuration);
            }
        }

        function play() {
            if (currentFrame >= rankedData.length - 1) {
                currentFrame = 0;
                window.finishedNotified = false;
            }
            isPlaying = true;
            document.getElementById('play-text').textContent = 'Pause';
            document.getElementById('play-icon').innerHTML = pauseIcon;
            step();
        }

        function pause() {
            isPlaying = false;
            document.getElementById('play-text').textContent = 'Play';
            document.getElementById('play-icon').innerHTML = playIcon;
            clearTimeout(timer);
        }

        document.getElementById('play-pause').addEventListener('click', () => {
            if (isPlaying) pause();
            else play();
        });

        document.getElementById('replay').addEventListener('click', () => {
            pause();
            currentFrame = 0;
            window.finishedNotified = false;
            update(currentFrame);
            play();
        });

        const speedSlider = document.getElementById('speed');
        const speedVal = document.getElementById('speed-val');
        
        speedSlider.addEventListener('input', (e) => {
            tickDuration = parseInt(e.target.value);
            speedVal.textContent = tickDuration;
        });

        update(0);

    </script>
</body>
</html>"""

    final_html = html_template.replace("'__DATA__'", json.dumps(all_data))
    
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '한국주식_순위추이.html')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
    
    msg = f"완료! {output_path} 파일이 업데이트 되었습니다.\n브라우저에서 열어보세요."
    print(msg)
    
    # 윈도우 알림 창 (메시지 박스) 띄우기
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, "모든 작업이 완료되었습니다!\n\nHTML 파일이 생성/업데이트 되었습니다.", "작업 완료 알림", 0)
    except Exception:
        pass

if __name__ == "__main__":
    create_chart()
