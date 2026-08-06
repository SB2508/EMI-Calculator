from pydantic import BaseModel, Field
from typing import List, Optional


class EMIRequest(BaseModel):
    principal: float = Field(..., gt=0, example=500000)
    annual_rate: float = Field(..., ge=0, example=10.5)
    tenure_months: int = Field(..., gt=0, example=24)


class EMIResponse(BaseModel):
    emi: float
    total_payment: float
    total_interest: float


class AmortizationRow(BaseModel):
    month: int
    emi: float
    principal_component: float
    interest_component: float
    balance: float


class AmortizationResponse(BaseModel):
    emi: float
    total_payment: float
    total_interest: float
    schedule: List[AmortizationRow]


class PrepaymentRequest(EMIRequest):
    prepayment_amount: float = Field(..., gt=0, example=50000)
    prepayment_month: int = Field(..., gt=0, example=6)


class PrepaymentResponse(BaseModel):
    original_tenure_months: int
    new_tenure_months: int
    original_total_interest: float
    new_total_interest: float
    interest_saved: float
    schedule: List[AmortizationRow]


class HistoryItem(BaseModel):
    id: int
    principal: float
    annual_rate: float
    tenure_months: int
    emi: float
    total_interest: float

    class Config:
        from_attributes = True
