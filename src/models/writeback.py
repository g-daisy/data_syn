from typing import Literal
from pydantic import BaseModel


class WriteBackRequest(BaseModel):
    dingtalk_id: int
    inspection_result: Literal["OK", "NG"]
