"""Refund calculation use cases with no-show policy consideration."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from application.dto.payment import RefundEstimateResponse
from domain.entities import (
    Booking,
    Payment,
    PaymentStatus,
    NoShowPolicy,
    BookingStatus,
    SessionStatus,
)
from domain.ports import PaymentRepositoryPort, BookingRepositoryPort


class RefundCalculationError(Exception):
    """Raised when refund calculation fails."""

    def __init__(self, message: str, code: str = "REFUND_CALCULATION_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


@dataclass
class RefundBreakdown:
    """Detailed refund breakdown."""
    total_paid: int
    total_sessions: int
    completed_sessions: int
    no_show_count: int
    billable_no_show_count: int
    remaining_sessions: int
    session_rate: int
    completed_session_cost: int
    no_show_cost: int
    refundable_sessions: int
    refund_amount: int
    platform_fee_refund: int
    pg_fee: int  # Not refundable
    final_refund: int
    policy_description: str
    breakdown_items: list[dict]


@dataclass
class CalculateRefundUseCase:
    """Calculate refund amount based on remaining sessions and no-show policy."""

    payment_repo: PaymentRepositoryPort
    booking_repo: BookingRepositoryPort

    async def execute(
        self,
        booking_id: int,
    ) -> RefundBreakdown:
        """
        Calculate refund amount for a booking.

        Formula:
        - refund_amount = (total_paid - completed_session_cost - no_show_cost)
        - completed_session_cost = completed_sessions * session_rate
        - no_show_cost = billable_no_show_count * session_rate (based on policy)

        Args:
            booking_id: Booking ID

        Returns:
            RefundBreakdown with detailed breakdown

        Raises:
            RefundCalculationError: If booking or payment not found, or not eligible for refund
        """
        # Get booking
        booking = await self.booking_repo.find_by_id(booking_id)
        if not booking:
            raise RefundCalculationError("Booking not found", "BOOKING_NOT_FOUND")

        # Get payment
        payment = await self.payment_repo.find_by_booking_id(booking_id)
        if not payment:
            raise RefundCalculationError("Payment not found", "PAYMENT_NOT_FOUND")

        if payment.status != PaymentStatus.PAID:
            raise RefundCalculationError(
                f"Payment not paid. Current status: {payment.status.value}",
                "PAYMENT_NOT_PAID",
            )

        # Get sessions to calculate attendance
        sessions = await self.booking_repo.list_sessions(booking_id)

        # Get tutor's no-show policy
        tutor = await self.booking_repo.find_tutor_by_id(booking.tutor_id)
        if not tutor:
            raise RefundCalculationError("Tutor not found", "TUTOR_NOT_FOUND")

        # Calculate breakdown
        return await self._calculate_refund_breakdown(
            booking=booking,
            payment=payment,
            sessions=sessions,
            no_show_policy=tutor.no_show_policy,
        )

    async def _calculate_refund_breakdown(
        self,
        booking: Booking,
        payment: Payment,
        sessions: list,
        no_show_policy: NoShowPolicy,
    ) -> RefundBreakdown:
        """Calculate detailed refund breakdown."""
        total_paid = payment.amount.amount_krw if payment.amount else 0
        total_sessions = booking.total_sessions or 0
        completed_sessions = booking.completed_sessions or 0

        # Count sessions by status
        no_show_count = sum(1 for s in sessions if s.status == SessionStatus.NO_SHOW)
        cancelled_count = sum(1 for s in sessions if s.status == SessionStatus.CANCELLED)

        # Calculate billable no-shows based on policy
        billable_no_show_count = await self._calculate_billable_no_shows(
            booking=booking,
            sessions=sessions,
            no_show_policy=no_show_policy,
        )

        # Calculate session rate
        session_rate = total_paid // total_sessions if total_sessions > 0 else 0

        # Calculate costs
        completed_session_cost = completed_sessions * session_rate
        no_show_cost = billable_no_show_count * session_rate

        # Calculate remaining sessions (scheduled - not yet attended)
        remaining_sessions = total_sessions - completed_sessions - no_show_count - cancelled_count

        # Refundable sessions = remaining sessions + non-billable no-shows
        non_billable_no_shows = no_show_count - billable_no_show_count
        refundable_sessions = remaining_sessions + non_billable_no_shows

        # Calculate refund amount
        refund_amount = refundable_sessions * session_rate

        # Platform fee refund (proportional)
        platform_fee_refund = int(refund_amount * payment.fee_rate)

        # PG fee is not refundable
        pg_fee = 0

        # Final refund amount
        final_refund = refund_amount

        # Build breakdown items for clear guide
        breakdown_items = self._build_breakdown_items(
            total_paid=total_paid,
            total_sessions=total_sessions,
            completed_sessions=completed_sessions,
            completed_session_cost=completed_session_cost,
            no_show_count=no_show_count,
            billable_no_show_count=billable_no_show_count,
            no_show_cost=no_show_cost,
            remaining_sessions=remaining_sessions,
            refundable_sessions=refundable_sessions,
            session_rate=session_rate,
            refund_amount=refund_amount,
            platform_fee_refund=platform_fee_refund,
            pg_fee=pg_fee,
            final_refund=final_refund,
        )

        # Policy description
        policy_description = self._get_policy_description(
            no_show_policy, billable_no_show_count, no_show_count
        )

        return RefundBreakdown(
            total_paid=total_paid,
            total_sessions=total_sessions,
            completed_sessions=completed_sessions,
            no_show_count=no_show_count,
            billable_no_show_count=billable_no_show_count,
            remaining_sessions=remaining_sessions,
            session_rate=session_rate,
            completed_session_cost=completed_session_cost,
            no_show_cost=no_show_cost,
            refundable_sessions=refundable_sessions,
            refund_amount=refund_amount,
            platform_fee_refund=platform_fee_refund,
            pg_fee=pg_fee,
            final_refund=final_refund,
            policy_description=policy_description,
            breakdown_items=breakdown_items,
        )

    async def _calculate_billable_no_shows(
        self,
        booking: Booking,
        sessions: list,
        no_show_policy: NoShowPolicy,
    ) -> int:
        """Calculate number of billable no-shows based on policy."""
        no_show_sessions = [s for s in sessions if s.status == SessionStatus.NO_SHOW]
        no_show_count = len(no_show_sessions)

        if no_show_policy == NoShowPolicy.FULL_DEDUCTION:
            # All no-shows are billable
            return no_show_count

        elif no_show_policy == NoShowPolicy.ONE_FREE:
            # First no-show of the month is free
            year_month = datetime.now().strftime("%Y-%m")
            monthly_no_show_count = await self.booking_repo.count_no_shows_in_month(
                booking.tutor_id,
                booking.student_id,
                year_month,
            )
            # If this is the first no-show, it's free
            if monthly_no_show_count <= 1:
                return max(0, no_show_count - 1)
            return no_show_count

        elif no_show_policy == NoShowPolicy.NONE:
            # No-shows are not billable
            return 0

        return no_show_count

    def _build_breakdown_items(
        self,
        total_paid: int,
        total_sessions: int,
        completed_sessions: int,
        completed_session_cost: int,
        no_show_count: int,
        billable_no_show_count: int,
        no_show_cost: int,
        remaining_sessions: int,
        refundable_sessions: int,
        session_rate: int,
        refund_amount: int,
        platform_fee_refund: int,
        pg_fee: int,
        final_refund: int,
    ) -> list[dict]:
        """Build breakdown items for clear refund guide."""
        items = [
            {
                "label": "총 결제 금액",
                "value": f"{total_paid:,}원",
                "description": f"{total_sessions}회 수업 예약",
            },
        ]

        if completed_sessions > 0:
            items.append({
                "label": "완료된 수업",
                "value": f"-{completed_session_cost:,}원",
                "description": f"{completed_sessions}회 × {session_rate:,}원",
            })

        if billable_no_show_count > 0:
            non_billable = no_show_count - billable_no_show_count
            desc = f"{billable_no_show_count}회 × {session_rate:,}원"
            if non_billable > 0:
                desc += f" (무결석 적용: {non_billable}회 무료)"
            items.append({
                "label": "결석 차감",
                "value": f"-{no_show_cost:,}원",
                "description": desc,
            })

        if refundable_sessions > 0:
            items.append({
                "label": "환불 가능 수업",
                "value": f"{refundable_sessions}회",
                "description": f"{refundable_sessions}회 × {session_rate:,}원 = {refund_amount:,}원",
            })

        items.append({
            "label": "예상 환불액",
            "value": f"{final_refund:,}원",
            "description": "환불 처리까지 영업일 3-5일 소요",
            "is_total": True,
        })

        return items

    def _get_policy_description(
        self,
        no_show_policy: NoShowPolicy,
        billable_count: int,
        total_count: int,
    ) -> str:
        """Get human-readable policy description."""
        if no_show_policy == NoShowPolicy.FULL_DEDUCTION:
            return "무단 결석 시 수업료 전액 차감"
        elif no_show_policy == NoShowPolicy.ONE_FREE:
            if total_count > 0:
                free_used = 1 if billable_count < total_count else 0
                return f"월 1회 무결석 (이번 달: {free_used}/1 사용)"
            return "월 1회 무결석 허용"
        elif no_show_policy == NoShowPolicy.NONE:
            return "결석 시 별도 협의 (수업료 차감 없음)"
        return ""

    def to_dto(self, breakdown: RefundBreakdown) -> RefundEstimateResponse:
        """Convert RefundBreakdown to RefundEstimateResponse DTO."""
        return RefundEstimateResponse(
            booking_id=str(breakdown.total_sessions),  # Will be set by caller
            total_paid=breakdown.total_paid,
            total_sessions=breakdown.total_sessions,
            completed_sessions=breakdown.completed_sessions,
            remaining_sessions=breakdown.remaining_sessions,
            session_rate=breakdown.session_rate,
            refund_amount=breakdown.final_refund,
            platform_fee=breakdown.platform_fee_refund,
            pg_fee=breakdown.pg_fee,
        )


@dataclass
class RefundGuideResponse:
    """Refund guide with detailed breakdown."""

    booking_id: int
    total_paid: int
    total_sessions: int
    completed_sessions: int
    remaining_sessions: int
    session_rate: int
    refund_amount: int
    platform_fee: int
    pg_fee: int
    policy_description: str
    breakdown_items: list[dict]
    is_eligible: bool
    reason: str | None = None
