"""Review API routes."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from application.dto.review import (
    ReviewCreateRequest,
    ReviewUpdateRequest,
    ReviewReplyRequest,
    ReviewReportRequest,
    ReviewResponse,
    ReviewListFilters,
    TutorReviewsResponse,
)
from application.use_cases.review import ReviewUseCases
from infrastructure.persistence.repositories.review_repository import ReviewRepository
from infrastructure.database import get_db


router = APIRouter(prefix="/reviews", tags=["reviews"])


def get_review_use_cases(db: AsyncSession = Depends(get_db)) -> ReviewUseCases:
    """Get review use cases with dependencies injected."""
    return ReviewUseCases(
        review_repo=ReviewRepository(db),
    )


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    request: ReviewCreateRequest,
    current_user_id: int = Query(..., description="Current user ID from JWT"),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new review.

    Requirements:
    - Verified payment only (payment_status == PAID)
    - At least 1 completed session
    - One review per booking
    - Content moderation applied

    Raises:
        HTTPException 400: If validation fails
    """
    use_cases = get_review_use_cases(db)

    try:
        review = await use_cases.create_review(
            booking_id=request.booking_id,
            tutor_id=current_user_id,  # TODO: Get from booking
            student_id=current_user_id,
            overall_rating=request.overall_rating,
            kindness_rating=request.kindness_rating,
            preparation_rating=request.preparation_rating,
            improvement_rating=request.improvement_rating,
            punctuality_rating=request.punctuality_rating,
            content=request.content,
            is_anonymous=request.is_anonymous,
        )
        return ReviewResponse(**review.__dict__)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("", response_model=list[ReviewResponse])
async def list_reviews(
    filters: ReviewListFilters = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    List reviews with optional filters.

    Filters:
    - tutor_id: Filter by tutor ID
    - min_rating: Minimum overall rating
    - has_photo: Filter by photo reviews (future feature)
    - offset: Pagination offset
    - limit: Max results (default 20, max 100)
    """
    use_cases = get_review_use_cases(db)

    if filters.tutor_id:
        reviews, stats = await use_cases.get_tutor_reviews(
            tutor_id=filters.tutor_id,
            min_rating=filters.min_rating,
            offset=filters.offset,
            limit=filters.limit,
        )
        return [ReviewResponse(**r.__dict__) for r in reviews]

    # TODO: Implement global review listing with filters
    return []


@router.get("/{review_id}", response_model=ReviewResponse)
async def get_review(
    review_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific review by ID."""
    use_cases = get_review_use_cases(db)
    review = await use_cases.review_repo.find_by_id(review_id)

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="리뷰를 찾을 수 없습니다.",
        )

    return ReviewResponse(**review.__dict__)


@router.patch("/{review_id}", response_model=ReviewResponse)
async def update_review(
    review_id: int,
    request: ReviewUpdateRequest,
    current_user_id: int = Query(..., description="Current user ID from JWT"),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a review.

    Can only update within 7 days of creation.
    Only the review author can update.

    Raises:
        HTTPException 400: If validation fails
        HTTPException 403: If not the author
    """
    use_cases = get_review_use_cases(db)

    try:
        review = await use_cases.update_review(
            review_id=review_id,
            student_id=current_user_id,
            overall_rating=request.overall_rating,
            kindness_rating=request.kindness_rating,
            preparation_rating=request.preparation_rating,
            improvement_rating=request.improvement_rating,
            punctuality_rating=request.punctuality_rating,
            content=request.content,
            is_anonymous=request.is_anonymous,
        )
        return ReviewResponse(**review.__dict__)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(
    review_id: int,
    current_user_id: int = Query(..., description="Current user ID from JWT"),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a review.

    Can only delete within 7 days of creation.
    Only the review author can delete.

    Raises:
        HTTPException 400: If validation fails
        HTTPException 403: If not the author
    """
    use_cases = get_review_use_cases(db)

    try:
        await use_cases.delete_review(review_id, current_user_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{review_id}/reply", response_model=ReviewResponse)
async def add_tutor_reply(
    review_id: int,
    request: ReviewReplyRequest,
    current_user_id: int = Query(..., description="Current user ID from JWT"),
    db: AsyncSession = Depends(get_db),
):
    """
    Add tutor reply to review.

    Only the tutor being reviewed can reply.

    Raises:
        HTTPException 400: If validation fails
        HTTPException 403: If not the tutor
    """
    use_cases = get_review_use_cases(db)

    try:
        review = await use_cases.add_tutor_reply(
            review_id=review_id,
            tutor_id=current_user_id,
            reply=request.reply,
        )
        return ReviewResponse(**review.__dict__)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/{review_id}/report", status_code=status.HTTP_201_CREATED)
async def report_review(
    review_id: int,
    request: ReviewReportRequest,
    current_user_id: int = Query(..., description="Current user ID from JWT"),
    db: AsyncSession = Depends(get_db),
):
    """
    Report a review for moderation.

    Reasons: spam, abuse, false_info

    Raises:
        HTTPException 400: If validation fails
    """
    use_cases = get_review_use_cases(db)

    try:
        await use_cases.report_review(
            review_id=review_id,
            reporter_id=current_user_id,
            reason=request.reason,
            description=request.description,
        )
        return {"message": "리뷰 신고가 접수되었습니다."}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/tutors/{tutor_id}/reviews", response_model=TutorReviewsResponse)
async def get_tutor_reviews(
    tutor_id: int,
    min_rating: float | None = Query(None, ge=1, le=5, description="Minimum rating filter"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all reviews for a specific tutor with badge information.

    Includes:
    - Review list
    - Total count
    - Average rating
    - Total reviews
    - Badges (Popular Tutor, Best Tutor, Response King)
    """
    use_cases = get_review_use_cases(db)

    reviews, stats = await use_cases.get_tutor_reviews(
        tutor_id=tutor_id,
        min_rating=min_rating,
        offset=offset,
        limit=limit,
    )

    return TutorReviewsResponse(
        reviews=[ReviewResponse(**r.__dict__) for r in reviews],
        total_count=stats["total_count"],
        avg_rating=stats["avg_rating"],
        total_reviews=stats["total_reviews"],
        badges=stats["badges"],
    )
