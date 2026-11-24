import json
import logging
import httpx
from fastapi import HTTPException
from src.core import config

logger = logging.getLogger(__name__)


async def forward_to_internal_api(payload: dict) -> dict:
    logger.info("转发 payload: %s", json.dumps(payload, ensure_ascii=False, default=str))
    try:
        async with httpx.AsyncClient(timeout=config.REQUEST_TIMEOUT) as client:
            response = await client.post(config.INTERNAL_API_URL, json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        logger.error("调用内部接口超时: %s", config.INTERNAL_API_URL)
        raise HTTPException(status_code=504, detail="内部接口请求超时")
    except httpx.ConnectError:
        logger.error("无法连接内部接口: %s", config.INTERNAL_API_URL)
        raise HTTPException(status_code=502, detail="无法连接内部接口")
    except httpx.HTTPStatusError as e:
        logger.error("内部接口返回错误状态 %s: %s", e.response.status_code, e.response.text)
        raise HTTPException(
            status_code=502,
            detail=f"内部接口错误 [{e.response.status_code}]: {e.response.text}",
        )
