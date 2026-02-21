"""Settlement API routes for tutor payment settlements."""
from typing import Annotated, Optional

from api.v1.routes.dependencies import (
    get_current_user,
    get_current_tutor,
    get_current_admin,
    get_repository_factory,
)
from application.dto.settlement import (
    SettlementListResponse,
    SettlementResponse,
    SettlementDetailResponse,
    MarkPaidRequest,
    MarkPaidResponse,
)
from domain.entities import User
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.database import get_db
from infrastructure.persistence.repository_factory import RepositoryFactory

router = APIRouter()


@router.get("", response_model=SettlementListResponse)
async def get_settlements(
    current_user: Annotated[User, Depends(get_current_tutor)],
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
    year_month: Optional[str] = Query(None, description="Year-month filter (e.g., 2024-01)"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
) -> SettlementListResponse:
    """Get tutor's settlement history.

    Returns a list of monthly settlements for the authenticated tutor.
    Each settlement includes completed sessions, amounts, and payment status.

    Args:
        year_month: Optional filter for specific month
        offset: Pagination offset
        limit: Pagination limit (max 100)
        db: Database session
        current_user: Authenticated tutor user

    Returns:
        List of settlements

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If not a tutor
    """
    tutor_id = current_user.id

    settlement_repo = repos.settlement()

    try:
        settlements = await settlement_repo.get_monthly_settlements(
            tutor_id=tutor_id,
            year_month=year_month,
            offset=offset,
            limit=limit,
        )

        # Convert to response DTOs
        settlement_responses = [
            SettlementResponse(
                id=s.id,
                tutor_id=s.tutor_id,
                year_month=s.year_month,
                total_sessions=s.total_sessions,
                total_amount=s.total_amount.amount_krw if s.total_amount else 0,
                platform_fee=s.platform_fee.amount_krw if s.platform_fee else 0,
                pg_fee=s.pg_fee.amount_krw if s.pg_fee else 0,
                net_amount=s.net_amount.amount_krw if s.net_amount else 0,
                is_paid=s.is_paid,
                paid_at=s.paid_at,
                created_at=s.created_at,
            )
            for s in settlements
        ]

        return SettlementListResponse(
            settlements=settlement_responses,
            total=len(settlement_responses),
            offset=offset,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch settlements: {str(e)}",
        ) from e


@router.get("/{year_month}", response_model=SettlementDetailResponse)
async def get_settlement_by_month(
    year_month: str,
    current_user: Annotated[User, Depends(get_current_tutor)],
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
) -> SettlementDetailResponse:
    """Get specific month settlement details.

    Returns detailed breakdown for a specific month's settlement.

    Args:
        year_month: Year-month string (e.g., 2024-01)
        db: Database session
        current_user: Authenticated tutor user

    Returns:
        Settlement details with breakdown

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If not a tutor
        HTTPException 404: If settlement not found
    """
    tutor_id = current_user.id

    settlement_repo = repos.settlement()

    try:
        settlement = await settlement_repo.find_by_tutor_and_month(
            tutor_id=tutor_id,
            year_month=year_month,
        )

        if not settlement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Settlement not found for {year_month}",
            )

        return SettlementDetailResponse(
            id=settlement.id,
            tutor_id=settlement.tutor_id,
            year_month=settlement.year_month,
            total_sessions=settlement.total_sessions,
            total_amount=settlement.total_amount.amount_krw if settlement.total_amount else 0,
            platform_fee=settlement.platform_fee.amount_krw if settlement.platform_fee else 0,
            pg_fee=settlement.pg_fee.amount_krw if settlement.pg_fee else 0,
            net_amount=settlement.net_amount.amount_krw if settlement.net_amount else 0,
            is_paid=settlement.is_paid,
            paid_at=settlement.paid_at,
            created_at=settlement.created_at,
            breakdown_items=[
                {
                    "label": "총 수업료",
                    "value": (
                        f"{settlement.total_amount.amount_krw if settlement.total_amount else 0:,}원"
                    ),
                    "description": f"{settlement.total_sessions}회 수업",
                },
                {
                    "label": "플랫폼 수수료",
                    "value": (
                        f"-{settlement.platform_fee.amount_krw if settlement.platform_fee else 0:,}원"
                    ),
                    "description": "5%",
                },
                {
                    "label": "PG 수수료",
                    "value": (
                        f"-{settlement.pg_fee.amount_krw if settlement.pg_fee else 0:,}원"
                    ),
                    "description": "3%",
                },
                {
                    "label": "실 지급액",
                    "value": (
                        f"{settlement.net_amount.amount_krw if settlement.net_amount else 0:,}원"
                    ),
                    "description": "정산 완료 후 영업일 3-5일 내 지급",
                    "is_total": True,
                },
            ],
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch settlement: {str(e)}",
        ) from e


@router.post("/{settlement_id}/mark-paid", response_model=MarkPaidResponse)
async def mark_settlement_as_paid(
    settlement_id: int,
    request: MarkPaidRequest,
    current_admin: Annotated[User, Depends(get_current_admin)],
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
) -> MarkPaidResponse:
    """Mark settlement as paid (admin only).

    Admin endpoint to mark a settlement as paid and record payment details.

    Args:
        settlement_id: Settlement ID
        request: Mark paid request with payment details
        db: Database session
        current_admin: Authenticated admin user

    Returns:
        Updated settlement details

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If not an admin
        HTTPException 404: If settlement not found
    """
    settlement_repo = repos.settlement()

    try:
        settlement = await settlement_repo.mark_as_paid(
            settlement_id=settlement_id,
            paid_at=request.paid_at,
        )

        return MarkPaidResponse(
            id=settlement.id,
            tutor_id=settlement.tutor_id,
            year_month=settlement.year_month,
            net_amount=settlement.net_amount.amount_krw if settlement.net_amount else 0,
            is_paid=settlement.is_paid,
            paid_at=settlement.paid_at,
        )
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            ) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to mark settlement as paid: {str(e)}",
        ) from e


@router.get("/admin/pending", response_model=SettlementListResponse)
async def get_pending_settlements(
    current_admin: Annotated[User, Depends(get_current_admin)],
    repos: Annotated[RepositoryFactory, Depends(get_repository_factory)],
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
) -> SettlementListResponse:
    """Get all pending settlements (admin only).

    Returns a list of all settlements that have not been paid yet.

    Args:
        offset: Pagination offset
        limit: Pagination limit (max 100)
        db: Database session
        current_admin: Authenticated admin user

    Returns:
        List of pending settlements

    Raises:
        HTTPException 401: If not authenticated
        HTTPException 403: If not an admin
    """
    settlement_repo = repos.settlement()

    try:
        settlements = await settlement_repo.list_pending_settlements(
            offset=offset,
            limit=limit,
        )

        settlement_responses = [
            SettlementResponse(
                id=s.id,
                tutor_id=s.tutor_id,
                year_month=s.year_month,
                total_sessions=s.total_sessions,
                total_amount=s.total_amount.amount_krw if s.total_amount else 0,
                platform_fee=s.platform_fee.amount_krw if s.platform_fee else 0,
                pg_fee=s.pg_fee.amount_krw if s.pg_fee else 0,
                net_amount=s.net_amount.amount_krw if s.net_amount else 0,
                is_paid=s.is_paid,
                paid_at=s.paid_at,
                created_at=s.created_at,
            )
            for s in settlements
        ]

        return SettlementListResponse(
            settlements=settlement_responses,
            total=len(settlement_responses),
            offset=offset,
            limit=limit,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch pending settlements: {str(e)}",
        ) from e
