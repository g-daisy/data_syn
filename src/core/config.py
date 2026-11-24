import os
from dotenv import load_dotenv

load_dotenv()

INTERNAL_API_URL: str = os.getenv(
    "INTERNAL_API_URL",
    "http://172.25.2.135:8080/api/quality/incoming-inspection/api/create",
)
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "30"))
PORT: int = int(os.getenv("PORT", "8000"))

DWS_PATH: str = os.getenv("DWS_PATH", r"C:\Users\vhst-250042\.workbuddy\binaries\node\cli-connector-packages\dws.cmd")


def _load_dingtalk_tables() -> dict:
    tables = {}
    for key, val in os.environ.items():
        if key.startswith("DINGTALK_") and key.endswith("_BASE_ID") and val:
            org_code = key[len("DINGTALK_"):-len("_BASE_ID")]
            table_id = os.getenv(f"DINGTALK_{org_code}_TABLE_ID", "")
            if table_id:
                tables[org_code] = {"base_id": val, "table_id": table_id}
    return tables


DINGTALK_TABLES: dict = _load_dingtalk_tables()

# 暂停同步的基地编码（逗号分隔），暂停后：webhook 不再转发 QMS，轮询不再回写钉钉
PAUSED_ORG_CODES: set = {
    c.strip() for c in os.getenv("PAUSED_ORG_CODES", "").split(",") if c.strip()
}

DB_HOST: str       = os.getenv("DB_HOST", "172.25.2.135")
DB_PORT: int       = int(os.getenv("DB_PORT", "3306"))
DB_NAME: str       = os.getenv("DB_NAME", "")
DB_USER: str       = os.getenv("DB_USER", "")
DB_PASSWORD: str   = os.getenv("DB_PASSWORD", "")
PROCESSED_IDS_FILE: str = os.getenv("PROCESSED_IDS_FILE", "processed_ids.json")
