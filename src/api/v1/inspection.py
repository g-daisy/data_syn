import logging
from fastapi import APIRouter
from src.core import config
from src.models.inspection import IncomingInspectionRequest, WebhookResponse
from src.services import inspection_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")


@router.post("/webhook/incoming-inspection", response_model=WebhookResponse)
async def incoming_inspection_webhook(payload: IncomingInspectionRequest):
    logger.info("收到来料检验请求: orgCode=%s, materialCode=%s", payload.orgCode, payload.materialCode)

    if payload.orgCode in config.PAUSED_ORG_CODES:
        logger.warning("orgCode=%s 同步已暂停，跳过提交（materialCode=%s）", payload.orgCode, payload.materialCode)
        return WebhookResponse(
            success=True,
            message=f"基地 {payload.orgCode} 同步已暂停，本次数据未提交",
        )

    result = await inspection_service.forward_to_internal_api(payload.model_dump())

    logger.info("内部接口调用成功")
    return WebhookResponse(success=True, message="创建成功", data=result)
