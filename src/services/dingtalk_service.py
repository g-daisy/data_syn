import asyncio
import json
import logging
from fastapi import HTTPException
from src.core import config

logger = logging.getLogger(__name__)

FIELD_SERIAL_NAME = "序号"
FIELD_RESULT_NAME = "是否通过（必填）"

_field_cache: dict[str, dict[str, str]] = {}


async def _dws(*args: str) -> dict:
    cmd = [config.DWS_PATH] + list(args) + ["--format", "json"]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()

    if stderr:
        logger.debug("dws stderr: %s", stderr.decode("utf-8", errors="replace"))

    try:
        data = json.loads(stdout.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        err_text = stderr.decode("utf-8", errors="replace").strip() if stderr else "(无输出)"
        logger.error("dws 输出解析失败: %s | stderr: %s", e, err_text)
        raise HTTPException(status_code=502, detail=f"钉钉接口返回格式异常: {err_text}")

    if data.get("success") is False:
        msg = data.get("error", {}).get("message", str(data))
        logger.error("dws 调用失败: %s", msg)
        raise HTTPException(status_code=502, detail=f"钉钉接口错误: {msg}")

    return data


async def _resolve_field_id(field_name: str, base_id: str, table_id: str) -> str:
    cache_key = f"{base_id}/{table_id}"
    if cache_key in _field_cache and field_name in _field_cache[cache_key]:
        return _field_cache[cache_key][field_name]

    logger.info("查询字段列表以解析 fieldId（base=%s, table=%s）", base_id, table_id)
    result = await _dws("aitable", "field", "list", "--base-id", base_id, "--table-id", table_id)
    table_fields: dict[str, str] = {}
    for f in result.get("data", {}).get("fields", []):
        table_fields[f["fieldName"]] = f["fieldId"]
    _field_cache[cache_key] = table_fields
    logger.info("已缓存 %d 个字段（base=%s, table=%s）", len(table_fields), base_id, table_id)

    if field_name not in table_fields:
        raise HTTPException(status_code=500, detail=f"找不到字段：{field_name}（base={base_id}, table={table_id}）")
    return table_fields[field_name]


async def write_back_inspection_result(
    dingtalk_id: int | str,
    inspection_result: str,
    org_code: str,
) -> dict:
    table_cfg = config.DINGTALK_TABLES.get(org_code)
    if not table_cfg:
        raise HTTPException(status_code=500, detail=f"未配置 org_code={org_code} 对应的钉钉表格")

    base_id = table_cfg["base_id"]
    table_id = table_cfg["table_id"]

    field_serial, field_result = await asyncio.gather(
        _resolve_field_id(FIELD_SERIAL_NAME, base_id, table_id),
        _resolve_field_id(FIELD_RESULT_NAME, base_id, table_id),
    )

    filters = json.dumps({
        "operator": "and",
        "operands": [
            {"operator": "eq", "operands": [field_serial, int(dingtalk_id)]},
        ],
    })

    result = await _dws(
        "aitable", "record", "list",
        "--base-id", base_id,
        "--table-id", table_id,
        "--filters", filters,
        "--field-ids", field_serial,
        "--all",
    )

    records: list = result.get("data", {}).get("records") or []
    logger.info("按序号 %s 查到 %d 条记录（org_code=%s）", dingtalk_id, len(records), org_code)

    if not records:
        logger.warning("未找到序号为 %s 的钉钉记录（org_code=%s）", dingtalk_id, org_code)
        return {"matched": 0, "updated": 0}

    record_ids = ",".join(r["recordId"] for r in records)
    await _dws(
        "aitable", "record", "batch-update",
        "--base-id", base_id,
        "--table-id", table_id,
        "--record-ids", record_ids,
        "--cells", json.dumps({field_result: inspection_result}),
    )

    logger.info("已更新序号 %s 的「是否通过」为: %s（org_code=%s）", dingtalk_id, inspection_result, org_code)
    return {"matched": len(records), "updated": len(records)}
