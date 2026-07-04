"""小学生英语口语对练 Agent — FastAPI 主入口"""
import sys
import os

# 确保 backend 目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.connection import init_db
from routers import courses, practice, progress

app = FastAPI(
    title="Kids English Speaking Agent",
    description="小学生英语口语对练 AI Agent",
    version="0.1.0",
)

# CORS 允许前端跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(courses.router)
app.include_router(practice.router)
app.include_router(progress.router)


@app.on_event("startup")
def on_startup():
    """启动时初始化数据库表"""
    init_db()
    print("✅ Database tables initialized")


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "kids-english-agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
