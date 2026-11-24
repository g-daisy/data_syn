import logging
from fastapi import APIRouter, HTTPException
from src.models.inspection import WebhookResponse
from src.services import db_poller

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


@router.post("/poll/sync-results", response_model=WebhookResponse)
async def poll_sync_results():
    logger.info("收到轮询同步请求")
    try:
        result = await db_poller.run_sync_once()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"数据库查询失败: {e}")

    scanned   = result["scanned"]
    succeeded = result["succeeded"]
    failed    = result["failed"]

    if scanned == 0:
        msg = "本次无新记录需要同步"
    else:
        msg = f"本次同步完成：扫描 {scanned} 条，成功 {succeeded} 条，失败 {failed} 条"

    return WebhookResponse(success=True, message=msg, data=result)
