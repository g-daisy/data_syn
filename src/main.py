import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.v1.inspection import router as inspection_router
from src.api.v1.writeback import router as writeback_router
from src.api.v1.poll import router as poll_router
from src.core import config
from src.services import db_poller

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)

logger = logging.getLogger(__name__)
POLL_INTERVAL = 300  # 5 分钟


async def _poll_loop():
    while True:
        await asyncio.sleep(POLL_INTERVAL)
        try:
            result = await db_poller.run_sync_once()
            logger.info("定时同步完成: %s", result)
        except Exception as e:
            logger.error("定时同步失败: %s", e)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    logger.info("服务启动，内部接口地址: %s", config.INTERNAL_API_URL)
    task = asyncio.create_task(_poll_loop())
    yield
    task.cancel()


app = FastAPI(
    title="钉钉来料检验数据同步服务",
    description="接收钉钉自动化流程触发的来料检验数据，转发至内部质检系统",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(inspection_router)
app.include_router(writeback_router)
app.include_router(poll_router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=config.PORT, reload=False)
