"""
User Account and Profile Endpoints for DukaanAI.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_user
from backend.app.infrastructure.database.models import User
from backend.app.infrastructure.database.session import get_db_session
from backend.app.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["User Profile"])


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get My Profile",
)
def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Returns the profile of the currently signed-in user."""
    return UserResponse.model_validate(current_user)


@router.patch(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update My Profile",
)
def update_my_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> UserResponse:
    """Updates basic profile fields (name, email) for the signed-in user."""
    if payload.full_name is not None:
        current_user.full_name = payload.full_name.strip()
    if payload.email is not None:
        current_user.email = str(payload.email)

    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)
