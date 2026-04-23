# -*- coding: utf-8 -*-


import os  # 파일명 기반으로 HTML 파일명을 결정하기 위해 os 모듈을 사용합니다.

html_content = """<!DOCTYPE html>
<html lang=\"ko\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>테트리스 게임</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #000; font-family: Arial, sans-serif; }
        .game-container { position: relative; width: 300px; height: 600px; background-color: #111; border: 2px solid #333; overflow: hidden; }
        .game-board { position: relative; width: 100%; height: 100%; }
        .cell { position: absolute; width: 30px; height: 30px; border: 1px solid #333; }
        .stats { position: absolute; top: 10px; right: 10px; color: white; text-align: right; }
        .stats div { margin: 5px 0; }
        .controls { position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%); text-align: center; color: white; }
        .controls div { margin: 5px 0; }
    </style>
</head>
<body>
    <div class="game-container">
        <div class="game-board" id="gameBoard"></div>
        <div class="stats">
            <div>점수: <span id="score">0</span></div>
            <div>레벨: <span id="level">1</span></div>
            <div>줄: <span id="lines">0</span></div>
        </div>
        <div class="controls">
            <div>조작법:</div>
            <div>← → : 이동</div>
            <div>↑ : 회전</div>
            <div>↓ : 부드럽게 떨어뜨리기</div>
            <div>Space : 바로 떨어뜨리기</div>
        <button id="startBtn" onclick="init()">시작</button>
        <button id="pauseBtn" onclick="pauseGame()">중단</button>
        <button id="typeBtn">종류</button>
        </div>
    </div>
    <script>
        const canvas = document.getElementById('gameBoard');
        const scoreElement = document.getElementById('score');
        const levelElement = document.getElementById('level');
        const linesElement = document.getElementById('lines');
        const ROWS = 20, COLS = 10, CELL_SIZE = 30;
        // 게임 상태 변수들
        let board = [], score = 0, level = 1, lines = 0, currentPiece, currentX, currentY, gameInterval, isGameOver = false;
        const colors = [null,'#00f0f0','#0000f0','#f0a000','#00f000','#f000f0','#f00000','#f0f000'];
        const pieces = [
            [[1,1,1,1]],
            [[2,0,0],[2,2,2]],
            [[0,0,3],[3,3,3]],
            [[4,4],[4,4]],
            [[0,5,5],[5,5,0]],
            [[0,6,0],[6,6,6]],
            [[7,7,0],[0,7,7]]
        ];
        function updateScore() {
            scoreElement.innerText = score;
            levelElement.innerText = level;
            linesElement.innerText = lines;
        }
        function init(){
            // 보드 초기화 및 게임 변수 리셋
            board = Array.from({length:ROWS},()=>Array(COLS).fill(0));
            score = 0;
            level = 1;
            lines = 0;
            updateScore();
            spawnPiece();
            clearInterval(gameInterval);
            gameInterval = setInterval(update, 500);
            isGameOver = false;
            draw();
        }
        function spawnPiece(){ const idx=Math.floor(Math.random()*pieces.length); currentPiece=pieces[idx]; currentX=Math.floor(COLS/2)-Math.floor(currentPiece[0].length/2); currentY=0; if(collides(currentPiece,currentX,currentY)) gameOver(); }
        function collides(p,x,y){ for(let r=0;r<p.length;r++) for(let c=0;c<p[r].length;c++) if(p[r][c]!==0){ const bx=x+c, by=y+r; if(bx<0||bx>=COLS||by>=ROWS||board[by][bx]!==0) return true; } return false; }
 function rotate(m){
     // 비정사각형 매트릭스도 회전하도록 구현
     const rows = m.length;
     const cols = m[0].length;
     const rotated = [];
     for(let c = 0; c < cols; c++){
         const newRow = [];
         for(let r = rows - 1; r >= 0; r--){
             newRow.push(m[r][c]);
         }
         rotated.push(newRow);
     }
     return rotated;
 }
        function freeze(){ for(let r=0;r<currentPiece.length;r++) for(let c=0;c<currentPiece[r].length;c++) if(currentPiece[r][c]!==0) board[currentY+r][currentX+c]=currentPiece[r][c]; let cleared=0; for(let r=ROWS-1;r>=0;r--) if(board[r].every(v=>v!==0)){ board.splice(r,1); board.unshift(Array(COLS).fill(0)); cleared++; r++; } if(cleared){ lines+=cleared; score+=cleared*100*level; level=Math.floor(lines/10)+1; updateScore(); } spawnPiece(); }
        function draw(){ canvas.innerHTML=''; for(let r=0;r<ROWS;r++) for(let c=0;c<COLS;c++) if(board[r][c]!==0){ const cell=document.createElement('div'); cell.className='cell'; cell.style.left=`${c*CELL_SIZE}px`; cell.style.top=`${r*CELL_SIZE}px`; cell.style.backgroundColor=colors[board[r][c]]; canvas.appendChild(cell); } for(let r=0;r<currentPiece.length;r++) for(let c=0;c<currentPiece[r].length;c++) if(currentPiece[r][c]!==0){ const cell=document.createElement('div'); cell.className='cell'; cell.style.left=`${(currentX+c)*CELL_SIZE}px`; cell.style.top=`${(currentY+r)*CELL_SIZE}px`; cell.style.backgroundColor=colors[currentPiece[r][c]]; canvas.appendChild(cell); } }
        // 아래로 이동 (키보드와 자동 업데이트 모두 사용)
        function move(dx){ if(!collides(currentPiece,currentX+dx,currentY)){ currentX+=dx; draw(); } }
        function moveDown(){ if(!collides(currentPiece,currentX,currentY+1)) currentY++; else freeze(); draw(); }
        function rotatePiece(){ const r=rotate(currentPiece); if(!collides(r,currentX,currentY)) { currentPiece=r; draw(); } }
        function drop(){ while(!collides(currentPiece,currentX,currentY+1)) currentY++; freeze(); draw(); }
        function gameOver(){ isGameOver=true; clearInterval(gameInterval); alert(`게임 오버! 점수: ${score}`); }
        // 게임 루프 업데이트 함수 (자동 하강 및 그리기)
        function update(){
            if (!isGameOver) {
                if (!collides(currentPiece, currentX, currentY + 1)) {
                    currentY++;
                } else {
                    freeze();
                }
                draw();
            }
        }
         document.addEventListener('keydown',e=>{ if(isGameOver) return; switch(e.key){ case 'ArrowLeft': move(-1); break; case 'ArrowRight': move(1); break; case 'ArrowDown': moveDown(); break; case 'ArrowUp': rotatePiece(); break; case ' ': drop(); break; } });
        // 중단 버튼 기능을 위한 함수 (전역 정의)
        function pauseGame(){
            clearInterval(gameInterval);
            gameInterval = undefined;
            isGameOver = true;
        }
        // 종류 버튼 이벤트 핸들러
        const typeBtn = document.getElementById('typeBtn');
        typeBtn.addEventListener('click', () => {
            let typeIdx = -1;
            for(let i=0;i<pieces.length;i++){
                if(JSON.stringify(pieces[i])===JSON.stringify(currentPiece)){
                    typeIdx = i+1;
                    break;
                }
            }
            alert('현재 조각 종류: ' + (typeIdx>0 ? typeIdx : '알 수 없음'));
        });
    </script>
</body>
</html>"""

def main():
    # 현재 스크립트 파일이 위치한 디렉토리 경로를 가져옵니다.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # HTML 결과 파일을 스크립트와 같은 폴더에 '테트리스.html'로 명시하여 저장합니다.
    html_filename = os.path.join(script_dir, "테트리스.html")
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f'{html_filename} 파일이 생성되었습니다.')

if __name__ == '__main__':
    main()
