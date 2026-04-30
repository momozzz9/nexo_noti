from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import database
import uvicorn

app = FastAPI()

# Jinja2 템플릿 설정
templates = Jinja2Templates(directory="templates")

# DB 세션 가져오기
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.on_event("startup")
def startup():
    # DB 초기화
    database.init_db()

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    """
    메인 페이지를 렌더링합니다.
    """
    return templates.TemplateResponse(request, "index.html", {"request": request})

@app.get("/subscribers")
async def get_subscribers(db: Session = Depends(get_db)):
    """현재 구독자 목록을 반환합니다."""
    subs = db.query(database.Subscriber).filter(database.Subscriber.is_active == True).all()
    return [{"email": s.email, "days": s.preferred_days, "time": s.preferred_time} for s in subs]

@app.post("/unsubscribe")
async def unsubscribe(
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    """구독자를 삭제(비활성화)합니다."""
    sub = db.query(database.Subscriber).filter(database.Subscriber.email == email).first()
    if sub:
        db.delete(sub)
        db.commit()
        return {"message": "구독 해지 완료"}
    raise HTTPException(status_code=404, detail="구독자를 찾을 수 없습니다.")

@app.post("/subscribe")
async def subscribe(
    email: str = Form(...), 
    days: str = Form("Mon,Tue,Wed,Thu,Fri,Sat,Sun"), 
    time: str = Form("07:00"), 
    db: Session = Depends(get_db)
):
    """
    새로운 구독자를 DB에 등록하거나 기존 설정을 업데이트합니다.
    """
    existing = db.query(database.Subscriber).filter(database.Subscriber.email == email).first()
    if existing:
        existing.is_active = True
        existing.preferred_days = days
        existing.preferred_time = time
        db.commit()
        return {"message": "설정이 업데이트되었습니다."}
    
    # 새 구독자 추가
    new_sub = database.Subscriber(email=email, preferred_days=days, preferred_time=time)
    db.add(new_sub)
    db.commit()
    return {"message": "구독 성공!"}

if __name__ == "__main__":
    # 포트 8000번에서 서버 실행
    uvicorn.run(app, host="0.0.0.0", port=8000)
