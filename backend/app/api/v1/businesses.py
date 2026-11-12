"""
Multi-Tenant Business and Staff Membership Management Endpoints for DukaanAI.
"""

import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_current_user, require_permission
from backend.app.application.business.service import BusinessService
from backend.app.core.security import Permissions
from backend.app.infrastructure.database.models import User
from backend.app.infrastructure.database.session import get_db_session
from backend.app.schemas.business import (
    BusinessCreate,
    BusinessMembershipResponse,
    BusinessResponse,
    BusinessUpdate,
    MemberAddRequest,
    MemberResponse,
    StoreCreate,
    StoreResponse,
    StoreUpdate,
)

router = APIRouter(prefix="/businesses", tags=["Business Management"])


@router.post(
    "",
    response_model=BusinessMembershipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register New Business",
)
def create_business(
    payload: BusinessCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> BusinessMembershipResponse:
    """
    Registers a new store business entity, provisions the initial outlet store,
    and assigns the authenticated caller as the business OWNER.
    """
    return BusinessService.create_business(db, current_user, payload)


@router.get(
    "",
    response_model=list[BusinessMembershipResponse],
    status_code=status.HTTP_200_OK,
    summary="List User Businesses",
)
def list_my_businesses(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> list[BusinessMembershipResponse]:
    """Retrieves all businesses where the authenticated user maintains active membership."""
    return BusinessService.list_user_businesses(db, current_user.id)


@router.get(
    "/{business_id}",
    response_model=BusinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Business Details",
)
def get_business(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_session),
) -> BusinessResponse:
    """Retrieves verified details of a specific business."""
    return BusinessService.get_business(db, business_id, current_user.id)


@router.patch(
    "/{business_id}",
    response_model=BusinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Business Details",
)
def update_business(
    business_id: uuid.UUID,
    payload: BusinessUpdate,
    current_user: User = Depends(get_current_user),
    _membership=Depends(require_permission(Permissions.BUSINESS_UPDATE)),
    db: Session = Depends(get_db_session),
) -> BusinessResponse:
    """Updates business metadata. Requires business.update permission."""
    return BusinessService.update_business(db, business_id, current_user.id, payload)


@router.get(
    "/{business_id}/members",
    response_model=list[MemberResponse],
    status_code=status.HTTP_200_OK,
    summary="List Business Staff Members",
)
def list_business_members(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    _membership=Depends(require_permission(Permissions.BUSINESS_READ)),
    db: Session = Depends(get_db_session),
) -> list[MemberResponse]:
    """Lists staff members belonging to the business. Requires business.read permission."""
    return BusinessService.list_members(db, business_id, current_user.id)


@router.post(
    "/{business_id}/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Staff Member",
)
def add_business_member(
    business_id: uuid.UUID,
    payload: MemberAddRequest,
    current_user: User = Depends(get_current_user),
    _membership=Depends(require_permission(Permissions.MEMBERS_MANAGE)),
    db: Session = Depends(get_db_session),
) -> MemberResponse:
    """Adds a staff member with a specific role. Requires members.manage permission."""
    return BusinessService.add_member(db, business_id, current_user.id, payload)


# ---------------------------------------------------------------------------
# Store Outlet Management Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/{business_id}/stores",
    response_model=StoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Store Outlet",
)
def create_store(
    business_id: uuid.UUID,
    payload: StoreCreate,
    current_user: User = Depends(get_current_user),
    _membership=Depends(require_permission(Permissions.BUSINESS_UPDATE)),
    db: Session = Depends(get_db_session),
) -> StoreResponse:
    """Provisions a new store outlet under the specified business."""
    return BusinessService.create_store(db, business_id, current_user.id, payload)


@router.get(
    "/{business_id}/stores",
    response_model=list[StoreResponse],
    status_code=status.HTTP_200_OK,
    summary="List Store Outlets",
)
def list_stores(
    business_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    _membership=Depends(require_permission(Permissions.BUSINESS_READ)),
    db: Session = Depends(get_db_session),
) -> list[StoreResponse]:
    """Retrieves all active stores belonging to the business."""
    return BusinessService.list_stores(db, business_id, current_user.id)


@router.get(
    "/{business_id}/stores/{store_id}",
    response_model=StoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Store Outlet Details",
)
def get_store(
    business_id: uuid.UUID,
    store_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    _membership=Depends(require_permission(Permissions.BUSINESS_READ)),
    db: Session = Depends(get_db_session),
) -> StoreResponse:
    """Retrieves details of a specific store outlet."""
    return BusinessService.get_store(db, business_id, store_id, current_user.id)


@router.patch(
    "/{business_id}/stores/{store_id}",
    response_model=StoreResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Store Outlet Details",
)
def update_store(
    business_id: uuid.UUID,
    store_id: uuid.UUID,
    payload: StoreUpdate,
    current_user: User = Depends(get_current_user),
    _membership=Depends(require_permission(Permissions.BUSINESS_UPDATE)),
    db: Session = Depends(get_db_session),
) -> StoreResponse:
    """Updates details of an existing store outlet."""
    return BusinessService.update_store(db, business_id, store_id, current_user.id, payload)
