from pydantic import BaseModel
from typing import Any, Optional


class IncomingInspectionRequest(BaseModel):
    orgCode: str
    supplierName: Optional[str] = None
    supplierCode: Optional[str] = None
    materialCode: str
    materialName: Optional[str] = None
    purchaseNo: Optional[str] = None
    inboundNo: Optional[str] = None
    batchNo: Optional[str] = None
    projectNo: Optional[str] = None
    reportDate: str
    steelCoilNo: Optional[str] = None
    heatNo: Optional[str] = None
    dimension: Optional[str] = None
    deliveryQty: Optional[float] = None
    urgency: Optional[str] = None
    dieNo: Optional[str] = None
    materialGrade: Optional[str] = None
    steelMill: Optional[str] = None
    dataFrom: int
    dingtalkId: str


class WebhookResponse(BaseModel):
    success: bool
    message: str
    data: Any = None
