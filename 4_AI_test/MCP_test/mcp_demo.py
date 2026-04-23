import asyncio
import os
import sys

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    print("mcp 라이브러리가 필요합니다. 터미널에서 아래 명령어를 실행해주세요:")
    print("pip install mcp")
    sys.exit(1)

# Enhanced HTML template with premium design
html_template = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MCP Intelligence Hub</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6366f1;
            --secondary: #4f46e5;
            --bg: #0f172a;
            --card-bg: #1e293b;
            --text: #f8fafc;
            --text-dim: #94a3b8;
            --accent: #10b981;
        }
        body { 
            font-family: 'Inter', sans-serif; 
            background-color: var(--bg); 
            color: var(--text); 
            margin: 0; 
            padding: 40px 20px;
            line-height: 1.6;
        }
        .container { 
            max-width: 1000px; 
            margin: auto; 
        }
        .header {
            text-align: center;
            margin-bottom: 50px;
            padding: 40px;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-radius: 24px;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04);
        }
        h1 { 
            font-size: 2.5rem;
            margin: 0;
            background: linear-gradient(to right, #818cf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .card {
            background: var(--card-bg);
            padding: 30px;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.05);
            margin-bottom: 30px;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        .card:hover {
            transform: translateY(-5px);
        }
        h2 { 
            color: var(--primary); 
            display: flex;
            align-items: center;
            gap: 12px;
            margin-top: 0;
        }
        h2::before {
            content: '';
            display: block;
            width: 4px;
            height: 24px;
            background: var(--primary);
            border-radius: 2px;
        }
        pre { 
            background: #000; 
            color: #a5b4fc; 
            padding: 20px; 
            border-radius: 12px; 
            overflow-x: auto; 
            font-family: 'Fira Code', monospace;
            font-size: 0.85rem;
            border: 1px solid rgba(255,255,255,0.1);
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        .note { 
            background: rgba(99, 102, 241, 0.1); 
            padding: 12px 20px; 
            border-radius: 10px; 
            margin-bottom: 20px; 
            font-size: 0.95rem;
            color: #cbd5e1;
        }
        .success-badge { 
            background: rgba(16, 185, 129, 0.1); 
            color: var(--accent);
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 15px;
            border: 1px solid rgba(16, 185, 129, 0.2);
        }
        .screenshot-container {
            margin-top: 20px;
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.1);
        }
        img {
            width: 100%;
            display: block;
        }
        .footer {
            text-align: center;
            color: var(--text-dim);
            font-size: 0.8rem;
            margin-top: 50px;
        }
        a { color: #818cf8; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 MCP Intelligence Hub</h1>
            <p style="color: var(--text-dim); margin-top: 10px;">Deep Integration with GitHub & Chrome Automation</p>
        </div>
"""

html_parts = [html_template]

async def run_github_feature():
    print("\n=== [1] GitHub MCP 활용 ===")
    html_parts.append('<div class="card">')
    html_parts.append('<h2>1. Repository Insight</h2>')
    html_parts.append('<div class="note"><b>Query:</b> <code>AI language:python</code> (Retrieving Meta-data)</div>')
    
    env = os.environ.copy()
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
        env=env
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                print("-> GitHub Search API 호출 중...")
                result = await session.call_tool(
                    "search_repositories", 
                    arguments={"query": "AI language:python", "perPage": 3}
                )
                
                if result.content and len(result.content) > 0:
                    text_result = result.content[0].text
                    html_parts.append('<div class="success-badge">API RESPONSE SUCCESS</div>')
                    html_parts.append(f'<pre><code>{text_result}</code></pre>')
                    print("-> 검색 결과를 HTML에 추가했습니다.")
                else:
                    html_parts.append('<p>결과가 없습니다.</p>')
    except Exception as e:
        html_parts.append(f'<p style="color:#ef4444">에러 발생: {e}</p>')
        print(f"에러: {e}")
    html_parts.append('</div>')

async def run_chrome_feature():
    print("\n=== [2] Chrome/Puppeteer MCP 활용 ===")
    html_parts.append('<div class="card">')
    html_parts.append('<h2>2. Browser Automation</h2>')
    
    url = "https://github.com/trending/python"
    html_parts.append(f'<div class="note"><b>Target:</b> <a href="{url}" target="_blank">{url}</a></div>')
    
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-puppeteer"],
        env=os.environ.copy()
    )
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                print(f"-> {url} 웹페이지로 이동합니다...")
                await session.call_tool("puppeteer_navigate", arguments={"url": url})
                
                # Wait for content to load
                await asyncio.sleep(3)
                
                print("-> 실시간 데이터 추출 및 스크린샷 캡처 중...")
                
                # Capture Screenshot
                screenshot_result = await session.call_tool("puppeteer_screenshot", arguments={
                    "name": "trending_python",
                    "width": 1200,
                    "height": 800,
                    "encoded": True
                })
                
                if screenshot_result.content:
                    for item in screenshot_result.content:
                        if item.type == 'text' and item.text.startswith('data:image'):
                            html_parts.append('<h3>Visual Snapshot</h3>')
                            html_parts.append(f'<div class="screenshot-container"><img src="{item.text}" alt="Trending Screenshot"></div>')
                            print("-> 스크린샷 캡처 완료.")

                # Extract Data
                script = """
                (() => {
                    const items = Array.from(document.querySelectorAll('article.Box-row'));
                    const results = items.slice(0, 5).map(row => {
                        const name = row.querySelector('h2.h3 a')?.innerText.trim() || 'N/A';
                        const stars = Array.from(row.querySelectorAll('a.Link--muted')).find(a => a.innerText.includes(','))?.innerText.trim() || '0';
                        const desc = row.querySelector('p.col-9')?.innerText.trim() || 'No description';
                        return { name, stars, desc };
                    });
                    return JSON.stringify(results, null, 2);
                })()
                """
                eval_result = await session.call_tool("puppeteer_evaluate", arguments={
                    "script": script
                })
                
                if eval_result.content:
                    raw_data = eval_result.content[0].text
                    # Extract the JSON part from the response string if necessary
                    extracted_json = raw_data
                    if "Execution result:" in raw_data:
                        try:
                            extracted_json = raw_data.split("Execution result:")[1].split("Console output:")[0].strip()
                        except:
                            pass
                    
                    html_parts.append('<div class="success-badge" style="margin-top:20px">EXTRACTED TRENDING DATA</div>')
                    html_parts.append(f'<pre><code>{extracted_json}</code></pre>')
                    print("-> 추출된 데이터를 HTML에 추가했습니다.")
                    
    except Exception as e:
        html_parts.append(f'<p style="color:#ef4444">에러 발생: {e}</p>')
        print(f"에러: {e}")
    html_parts.append('</div>')

async def main():
    await run_github_feature()
    await run_chrome_feature()
    
    # Final Footer
    html_parts.append("""
        <div class="footer">
            Generated at 2026-04-19 • MCP Protocol Demo • Powered by Antigravity
        </div>
    </div>
</body>
</html>
    """)
    
    # Save File
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, "result.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))
    
    print(f"\n[성공] 실행 결과가 저장되었습니다: {file_path}")
    print("브라우저에서 result.html을 열어 결과를 확인하세요.")

if __name__ == "__main__":
    asyncio.run(main())
