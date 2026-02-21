"""Payment Data Transfer Objects."""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class PaymentMethod(str, Enum):
    """Payment method types."""

    CARD = "card"
    TRANSFER = "transfer"
    VIRTUAL_ACCOUNT = "virtual_account"


class PaymentStatus(str, Enum):
    """Payment status types."""

    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    CANCELLED = "cancelled"


class PreparePaymentRequest(BaseModel):
    """Request to prepare payment."""

    booking_id: str = Field(..., description="Booking ID")
    amount: int = Field(..., gt=0, description="Payment amount in KRW")
    order_name: str = Field(..., min_length=1, max_length=100, description="Order name")


class PreparePaymentResponse(BaseModel):
    """Response from payment preparation."""

    payment_key: str = Field(..., description="Unique payment key")
    order_id: str = Field(..., description="Order ID")
    amount: int = Field(..., description="Payment amount in KRW")
    customer_key: str = Field(..., description="Customer key")


class ConfirmPaymentRequest(BaseModel):
    """Request to confirm payment."""

    payment_key: str = Field(..., description="Payment key from Toss")
    order_id: str = Field(..., description="Order ID")
    amount: int = Field(..., gt=0, description="Expected payment amount in KRW")


class ConfirmPaymentResponse(BaseModel):
    """Response from payment confirmation."""

    payment_id: str
    booking_id: str
    payment_key: str
    order_id: str
    amount: int
    fee_rate: float
    fee_amount: int
    net_amount: int
    status: PaymentStatus
    payment_method: Optional[str] = None
    paid_at: Optional[datetime] = None


class CancelPaymentRequest(BaseModel):
    """Request to cancel payment."""

    cancel_reason: str = Field(
        ..., min_length=1, max_length=200, description="Reason for cancellation"
    )


class CancelPaymentResponse(BaseModel):
    """Response from payment cancellation."""

    payment_id: str
    payment_key: str
    cancel_reason: str
    refund_amount: int
    cancelled_at: datetime
    status: PaymentStatus


class RefundEstimateResponse(BaseModel):
    """Refund estimate response."""

    booking_id: str
    total_paid: int = Field(..., description="Total amount paid")
    total_sessions: int = Field(..., description="Total number of sessions")
    completed_sessions: int = Field(..., description="Number of completed sessions")
    remaining_sessions: int = Field(..., description="Number of remaining sessions")
    session_rate: int = Field(..., description="Rate per session")
    refund_amount: int = Field(..., description="Calculated refund amount")
    platform_fee: int = Field(..., description="Platform fee to be refunded")
    pg_fee: int = Field(..., description="PG fee (may not be refundable)")


class RefundBreakdownItem(BaseModel):
    """Single item in refund breakdown."""

    label: str = Field(..., description="Label for the item (e.g., '완료된 수업')")
    value: str = Field(..., description="Formatted value (e.g., '-50,000원')")
    description: str = Field(..., description="Additional description")
    is_total: bool = Field(default=False, description="Whether this is the total line")


class RefundGuideResponse(BaseModel):
    """Refund guide with detailed breakdown."""

    booking_id: int
    total_paid: int = Field(..., description="Total amount paid")
    total_sessions: int = Field(..., description="Total number of sessions")
    completed_sessions: int = Field(..., description="Number of completed sessions")
    remaining_sessions: int = Field(..., description="Number of remaining sessions")
    session_rate: int = Field(..., description="Rate per session")
    refund_amount: int = Field(..., description="Calculated refund amount")
    platform_fee: int = Field(..., description="Platform fee to be refunded")
    pg_fee: int = Field(..., description="PG fee (may not be refundable)")
    policy_description: str = Field(..., description="No-show policy description")
    breakdown_items: list[RefundBreakdownItem] = Field(..., description="Detailed breakdown items")
    is_eligible: bool = Field(..., description="Whether refund is eligible")
    reason: str | None = Field(None, description="Reason if not eligible")


class PaymentStatusResponse(BaseModel):
    """Payment status response."""

    id: int
    booking_id: int
    amount: int
    fee_rate: float
    fee_amount: int
    net_amount: int
    pg_payment_key: Optional[str]
    pg_provider: str
    status: PaymentStatus
    paid_at: Optional[datetime]
    refunded_at: Optional[datetime]
    refund_reason: Optional[str]
    created_at: datetime
    updated_at: datetime
    method: Optional[str] = None
    receipt_url: Optional[str] = None


class WebhookPaymentData(BaseModel):
    """Webhook payment data from Toss."""

    payment_key: str
    status: str
    order_id: str
    amount: int
    requested_at: datetime
    approved_at: Optional[datetime] = None
    method: str


class TossWebhookRequest(BaseModel):
    """Toss webhook request."""

    payment_key: str
    status: str
    order_id: str
    amount: int
    requested_at: datetime
    approved_at: Optional[datetime] = None
    method: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate payment status."""
        allowed_statuses = {
            "READY",
            "IN_PROGRESS",
            "WAITING_FOR_DEPOSIT",
            "DONE",
            "CANCELED",
            "FAILED",
            "EXPIRED",
        }
        if v not in allowed_statuses:
            raise ValueError(f"Invalid status: {v}")
        return v
