import logging
from fastapi import APIRouter
from src.models.writeback import WriteBackRequest
from src.models.inspection import WebhookResponse
from src.services import dingtalk_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


@router.post("/webhook/write-back-result", response_model=WebhookResponse)
async def write_back_result(payload: WriteBackRequest):
    logger.info(
        "收到回写请求: dingtalk_id=%s, inspection_result=%s",
        payload.dingtalk_id, payload.inspection_result,
    )

    result = await dingtalk_service.write_back_inspection_result(
        dingtalk_id=payload.dingtalk_id,
        inspection_result=payload.inspection_result,
    )

    matched = result["matched"]
    updated = result["updated"]
    msg = f"回写完成：匹配 {matched} 条，更新 {updated} 条" if matched else "未找到匹配记录，无需更新"
    return WebhookResponse(success=True, message=msg, data=result)
