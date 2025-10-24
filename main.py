import asyncio
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from _13hebei import fetch_hebei_news
from _14sanxi import fetch_shnxi_news
from _15neimenggu import fetch_neimenggu_news
from _21liaoning import fetch_liaoning_news
from _22jilin import fetch_jilin_news
from _23heilongjiang import fetch_heilongjiang_news
from _32jiangsu import fetch_jiangsu_news
from _33zhejiang import fetch_zhejiang_news
from _35fujian import fetch_fujian_news
from _41henan import fetch_henan_news
from _44guangdong import fetch_guangdong_news
from _46hainan import fetch_hainan_news
from _50chongqing import fetch_chongqing_news
from _52guizhou import fetch_guizhou_news
from _53yunan import fetch_yunnan_news
from _54xizang import fetch_xizang_news
from _61shanxi import fetch_shanxi_news
from _63qinghai import fetch_qinghai_news
from _64ningxia import fetch_ningxia_news
from _65xinjiang import fetch_xinjiang_news


# === FastAPI 应用生命周期 ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("应用启动中...")
    yield
    print("应用关闭中...")


# === 初始化 FastAPI 应用 ===
app = FastAPI(lifespan=lifespan)
config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_level="info")
server = uvicorn.Server(config)

# === CORS 设置 ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# === 请求日志中间件 ===
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"收到请求：{request.method} {request.url}")
    response = await call_next(request)
    return response


# === 路由示例 ===
@app.get("/")
async def read_root():
    return JSONResponse({"message": "Hello, World!"})


# === 关闭 FastAPI 服务 ===
async def shutdown_server():
    print("🔻正在关闭 FastAPI 服务...")
    await server.shutdown()
    print("✅ FastAPI 服务已关闭。")


# === 返回爬虫数据 ===
def safe_fetch(fetch_func, retries=3, delay=2):
    for i in range(retries):
        try:
            result = fetch_func()
            if result is not None:
                return result
        except Exception as e:
            print(f"⚠️ 第 {i+1} 次调用 {fetch_func.__name__} 失败：{e}")
            time.sleep(delay)
    print(f"❌ 跳过：{fetch_func.__name__}")
    return []


@app.get("/query_news_list")
def query_news_list():
    hebei_news_list = safe_fetch(fetch_hebei_news)
    sanxi_news_list = safe_fetch(fetch_shnxi_news)
    neimenggu_news_list = safe_fetch(fetch_neimenggu_news)
    liaoning_news_list = safe_fetch(fetch_liaoning_news)
    jilin_news_list = safe_fetch(fetch_jilin_news)
    heilongjiang_news_list = safe_fetch(fetch_heilongjiang_news)
    jiangsu_news_list = safe_fetch(fetch_jiangsu_news)
    zhejiang_news_list = safe_fetch(fetch_zhejiang_news)
    fujian_news_texts = safe_fetch(fetch_fujian_news)
    henan_news_list = safe_fetch(fetch_henan_news)
    guangdong_news_list = safe_fetch(fetch_guangdong_news)
    hainan_news_list = safe_fetch(fetch_hainan_news)
    chongqing_news_list = safe_fetch(fetch_chongqing_news)
    guizhou_news_list = safe_fetch(fetch_guizhou_news)
    yunnan_news_list = safe_fetch(fetch_yunnan_news)
    xizang_news_list = safe_fetch(fetch_xizang_news)
    shanxi_news_list = safe_fetch(fetch_shanxi_news)
    qinghai_news_list = safe_fetch(fetch_qinghai_news)
    ningxia_news_list = safe_fetch(fetch_ningxia_news)
    xinjiang_news_list = safe_fetch(fetch_xinjiang_news)

    result = [
        *hebei_news_list,
        *sanxi_news_list,
        *neimenggu_news_list,
        *liaoning_news_list,
        *jilin_news_list,
        *heilongjiang_news_list,
        *jiangsu_news_list,
        *zhejiang_news_list,
        *fujian_news_texts,
        *henan_news_list,
        *guangdong_news_list,
        *hainan_news_list,
        *chongqing_news_list,
        *guizhou_news_list,
        *yunnan_news_list,
        *xizang_news_list,
        *shanxi_news_list,
        *qinghai_news_list,
        *ningxia_news_list,
        *xinjiang_news_list,
    ]
    print("result", result)

    return result


if __name__ == "__main__":
    asyncio.run(server.serve())
