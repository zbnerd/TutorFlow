"""Settlement Data Transfer Objects."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class SettlementResponse(BaseModel):
    """Basic settlement response."""

    id: int
    tutor_id: int
    year_month: str = Field(..., description="Year-month (e.g., 2024-01)")
    total_sessions: int = Field(..., description="Total number of sessions")
    total_amount: int = Field(..., description="Total amount before fees (KRW)")
    platform_fee: int = Field(..., description="Platform fee amount (KRW)")
    pg_fee: int = Field(..., description="Payment gateway fee amount (KRW)")
    net_amount: int = Field(..., description="Net amount after fees (KRW)")
    is_paid: bool = Field(..., description="Whether settlement has been paid")
    paid_at: Optional[datetime] = Field(None, description="Payment timestamp")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")

    class Config:
        from_attributes = True


class SettlementBreakdownItem(BaseModel):
    """Single item in settlement breakdown."""

    label: str = Field(..., description="Label for the item")
    value: str = Field(..., description="Formatted value (e.g., '500,000원')")
    description: str = Field(..., description="Additional description")
    is_total: bool = Field(default=False, description="Whether this is the total line")


class SettlementDetailResponse(BaseModel):
    """Detailed settlement response with breakdown."""

    id: int
    tutor_id: int
    year_month: str
    total_sessions: int
    total_amount: int
    platform_fee: int
    pg_fee: int
    net_amount: int
    is_paid: bool
    paid_at: Optional[datetime]
    created_at: Optional[datetime]
    breakdown_items: List[SettlementBreakdownItem] = Field(
        ..., description="Detailed breakdown items"
    )


class SettlementListResponse(BaseModel):
    """Settlement list response."""

    settlements: List[SettlementResponse]
    total: int = Field(..., description="Total number of settlements")
    offset: int = Field(..., description="Pagination offset")
    limit: int = Field(..., description="Pagination limit")


class MarkPaidRequest(BaseModel):
    """Request to mark settlement as paid."""

    paid_at: Optional[datetime] = Field(
        None, description="Payment timestamp (defaults to now if not provided)"
    )


class MarkPaidResponse(BaseModel):
    """Response for marking settlement as paid."""

    id: int
    tutor_id: int
    year_month: str
    net_amount: int
    is_paid: bool
    paid_at: Optional[datetime]
