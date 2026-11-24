import json
import logging
import os
import aiomysql
from src.core import config
from src.services.dingtalk_service import write_back_inspection_result

logger = logging.getLogger(__name__)

_RESULT_MAP = {"qualified": "OK", "rejected": "NG"}


def _load_processed_ids() -> set:
    if not os.path.exists(config.PROCESSED_IDS_FILE):
        return set()
    try:
        with open(config.PROCESSED_IDS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("ids", []))
    except Exception:
        logger.warning("读取 processed_ids.json 失败，视为空集合")
        return set()


def _save_processed_ids(ids: set) -> None:
    try:
        with open(config.PROCESSED_IDS_FILE, "w", encoding="utf-8") as f:
            json.dump({"ids": sorted(ids)}, f)
    except Exception:
        logger.error("写入 processed_ids.json 失败")


async def _query_pending_rows() -> list:
    conn = await aiomysql.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        db=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """
                SELECT id, dingtalk_id, inspection_result, org_code
                FROM qms_incoming_inspection
                WHERE inspection_result IS NOT NULL AND inspection_result != ''
                  AND data_from = 10
                  AND dingtalk_id IS NOT NULL
                """
            )
            rows = await cur.fetchall()
        return list(rows)
    finally:
        conn.close()


async def run_sync_once() -> dict:
    processed = _load_processed_ids()

    try:
        rows = await _query_pending_rows()
    except Exception as e:
        logger.error("查询数据库失败: %s", e)
        raise

    pending = [r for r in rows if r["id"] not in processed]
    if config.PAUSED_ORG_CODES:
        active = [r for r in pending if str(r.get("org_code") or "") not in config.PAUSED_ORG_CODES]
        paused_cnt = len(pending) - len(active)
        if paused_cnt:
            logger.info("跳过已暂停基地记录 %d 条（PAUSED_ORG_CODES=%s）", paused_cnt, ",".join(sorted(config.PAUSED_ORG_CODES)))
        pending = active
    logger.info("本次扫描：共 %d 条有结果记录，其中 %d 条待同步", len(rows), len(pending))

    succeeded, failed, failed_ids = 0, 0, []

    for row in pending:
        org_code = str(row.get("org_code") or "")
        if org_code not in config.DINGTALK_TABLES:
            logger.warning("记录 id=%s 的 org_code=%r 未配置对应钉钉表格，跳过", row["id"], org_code)
            continue
        try:
            raw = str(row["inspection_result"])
            mapped = _RESULT_MAP.get(raw, raw)
            await write_back_inspection_result(
                dingtalk_id=row["dingtalk_id"],
                inspection_result=mapped,
                org_code=org_code,
            )
            processed.add(row["id"])
            succeeded += 1
            logger.info("记录 id=%s 回写钉钉成功", row["id"])
        except Exception as e:
            failed += 1
            failed_ids.append(row["id"])
            logger.error("记录 id=%s 回写失败: %s", row["id"], e)

    if succeeded:
        _save_processed_ids(processed)

    return {
        "scanned": len(pending),
        "succeeded": succeeded,
        "failed": failed,
        "failed_ids": failed_ids,
    }
