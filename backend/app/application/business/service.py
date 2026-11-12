"""
Business Management and Tenant Membership Application Service for DukaanAI.
Handles business provisioning, multi-store hierarchy, staff role assignment,
and authorization checks.
"""

import uuid
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    BusinessAccessDenied,
    BusinessNotFound,
    InsufficientPermissions,
    ResourceConflict,
    StoreNotFound,
)
from backend.app.core.security import (
    Permissions,
    check_permission,
    generate_secure_token,
    get_role_permissions,
    hash_password,
)
from backend.app.infrastructure.database.models import Business, BusinessUser, Store, User
from backend.app.infrastructure.otp.service import normalize_phone_number
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


class BusinessService:
    """Manages multi-tenant business creation, membership, and staff permissions."""

    @staticmethod
    def create_business(db: Session, current_user: User, data: BusinessCreate) -> BusinessMembershipResponse:
        """
        Creates a new tenant business entity, creates the default retail store,
        and assigns the creator as an active OWNER.
        """
        # Validate GSTIN uniqueness if provided
        if data.gstin:
            existing = db.scalar(select(Business).where(Business.gstin == data.gstin.strip()))
            if existing:
                raise ResourceConflict("A business with this GSTIN is already registered.")

        # 1. Create Business
        settings = {}
        if data.business_type:
            settings["business_type"] = data.business_type
        if data.owner_name:
            settings["owner_name"] = data.owner_name

        lang = data.preferred_language or data.primary_language
        business = Business(
            name=data.name.strip(),
            legal_name=data.legal_name.strip() if data.legal_name else data.name.strip(),
            gstin=data.gstin.strip() if data.gstin else None,
            currency=data.currency,
            timezone=data.timezone,
            primary_language=lang,
            settings=settings,
            is_active=True,
        )
        db.add(business)
        db.flush()

        # 2. Assign Creator as OWNER
        membership = BusinessUser(
            business_id=business.id,
            user_id=current_user.id,
            role="OWNER",
            is_active=True,
        )
        db.add(membership)

        # 3. Create Default Counter Store
        store_name = data.initial_store_name.strip() if data.initial_store_name else f"{business.name} Main Store"
        default_store = Store(
            business_id=business.id,
            name=store_name,
            code="MAIN",
            address_line1="Main Market",
            city="Mumbai",
            state="Maharashtra",
            pincode="400001",
            phone_number=current_user.phone_number,
            is_primary=True,
            timezone=data.timezone,
            is_active=True,
        )
        db.add(default_store)

        db.commit()
        db.refresh(business)
        db.refresh(membership)

        return BusinessMembershipResponse(
            business=BusinessResponse.model_validate(business),
            role=membership.role,
            is_active=membership.is_active,
            permissions=sorted(list(get_role_permissions(membership.role))),
        )

    @staticmethod
    def list_user_businesses(db: Session, user_id: uuid.UUID) -> list[BusinessMembershipResponse]:
        """Lists all businesses where the user maintains an active membership."""
        stmt = (
            select(BusinessUser, Business)
            .join(Business, BusinessUser.business_id == Business.id)
            .where(
                BusinessUser.user_id == user_id,
                BusinessUser.is_active == True,  # noqa: E712
                Business.is_active == True,  # noqa: E712
            )
            .order_by(Business.created_at.desc())
        )
        results = db.execute(stmt).all()

        memberships = []
        for membership, business in results:
            memberships.append(
                BusinessMembershipResponse(
                    business=BusinessResponse.model_validate(business),
                    role=membership.role,
                    is_active=membership.is_active,
                    permissions=sorted(list(get_role_permissions(membership.role))),
                )
            )
        return memberships

    @staticmethod
    def get_user_membership(db: Session, business_id: uuid.UUID, user_id: uuid.UUID) -> BusinessUser:
        """
        Authoritatively validates that a user belongs to a specific business.
        Raises BusinessAccessDenied if no active membership exists.
        """
        stmt = select(BusinessUser).where(
            BusinessUser.business_id == business_id,
            BusinessUser.user_id == user_id,
            BusinessUser.is_active == True,  # noqa: E712
        )
        membership = db.scalar(stmt)
        if not membership:
            raise BusinessAccessDenied("You do not have active access to this business.")
        return membership

    @staticmethod
    def get_business(db: Session, business_id: uuid.UUID, user_id: uuid.UUID) -> BusinessResponse:
        """Retrieves verified business details."""
        BusinessService.get_user_membership(db, business_id, user_id)
        business = db.get(Business, business_id)
        if not business or not business.is_active:
            raise BusinessNotFound("Business not found.")
        return BusinessResponse.model_validate(business)

    @staticmethod
    def update_business(
        db: Session, business_id: uuid.UUID, user_id: uuid.UUID, data: BusinessUpdate
    ) -> BusinessResponse:
        """Updates business metadata. Requires business.update permission."""
        membership = BusinessService.get_user_membership(db, business_id, user_id)
        if not check_permission(membership.role, Permissions.BUSINESS_UPDATE):
            raise InsufficientPermissions(Permissions.BUSINESS_UPDATE)

        business = db.get(Business, business_id)
        if not business or not business.is_active:
            raise BusinessNotFound("Business not found.")

        if data.name is not None:
            business.name = data.name.strip()
        if data.legal_name is not None:
            business.legal_name = data.legal_name.strip()
        if data.gstin is not None:
            business.gstin = data.gstin.strip() if data.gstin.strip() else None
        if data.primary_language is not None:
            business.primary_language = data.primary_language.strip()
        if data.timezone is not None:
            business.timezone = data.timezone.strip()

        settings = dict(business.settings or {})
        changed_settings = False
        if data.business_type is not None:
            settings["business_type"] = data.business_type
            changed_settings = True
        if data.owner_name is not None:
            settings["owner_name"] = data.owner_name
            changed_settings = True
        if changed_settings:
            business.settings = settings

        db.commit()
        db.refresh(business)
        return BusinessResponse.model_validate(business)

    @staticmethod
    def list_members(db: Session, business_id: uuid.UUID, user_id: uuid.UUID) -> list[MemberResponse]:
        """Lists staff members for a business. Requires business.read permission."""
        membership = BusinessService.get_user_membership(db, business_id, user_id)
        if not check_permission(membership.role, Permissions.BUSINESS_READ):
            raise InsufficientPermissions(Permissions.BUSINESS_READ)

        stmt = (
            select(BusinessUser, User)
            .join(User, BusinessUser.user_id == User.id)
            .where(BusinessUser.business_id == business_id)
            .order_by(BusinessUser.created_at.asc())
        )
        records = db.execute(stmt).all()

        members = []
        for bu, u in records:
            members.append(
                MemberResponse(
                    id=bu.id,
                    user_id=u.id,
                    phone_number=u.phone_number,
                    full_name=u.full_name,
                    role=bu.role,
                    is_active=bu.is_active,
                    created_at=bu.created_at,
                )
            )
        return members

    @staticmethod
    def add_member(
        db: Session, business_id: uuid.UUID, user_id: uuid.UUID, data: MemberAddRequest
    ) -> MemberResponse:
        """Adds or invites a staff member to the business. Requires members.manage permission."""
        caller_membership = BusinessService.get_user_membership(db, business_id, user_id)
        if not check_permission(caller_membership.role, Permissions.MEMBERS_MANAGE):
            raise InsufficientPermissions(Permissions.MEMBERS_MANAGE)

        phone = normalize_phone_number(data.phone_number)

        # Lookup or provision User
        stmt = select(User).where(User.phone_number == phone)
        target_user = db.scalar(stmt)
        if not target_user:
            target_user = User(
                phone_number=phone,
                full_name=data.full_name.strip(),
                password_hash=hash_password(generate_secure_token(16)),
                is_active=True,
            )
            db.add(target_user)
            db.flush()

        # Check existing membership
        existing_mem_stmt = select(BusinessUser).where(
            BusinessUser.business_id == business_id,
            BusinessUser.user_id == target_user.id,
        )
        existing_mem = db.scalar(existing_mem_stmt)

        if existing_mem:
            if existing_mem.is_active:
                raise ResourceConflict("This user is already an active member of this business.")
            # Reactivate
            existing_mem.is_active = True
            existing_mem.role = data.role
            membership = existing_mem
        else:
            membership = BusinessUser(
                business_id=business_id,
                user_id=target_user.id,
                role=data.role,
                is_active=True,
            )
            db.add(membership)

        db.commit()
        db.refresh(membership)
        db.refresh(target_user)

        return MemberResponse(
            id=membership.id,
            user_id=target_user.id,
            phone_number=target_user.phone_number,
            full_name=target_user.full_name,
            role=membership.role,
            is_active=membership.is_active,
            created_at=membership.created_at,
        )

    @staticmethod
    def create_store(
        db: Session, business_id: uuid.UUID, user_id: uuid.UUID, data: StoreCreate
    ) -> StoreResponse:
        """Creates a new store outlet. Requires business.update permission."""
        membership = BusinessService.get_user_membership(db, business_id, user_id)
        if not check_permission(membership.role, Permissions.BUSINESS_UPDATE):
            raise InsufficientPermissions(Permissions.BUSINESS_UPDATE)

        if data.is_primary:
            db.execute(
                update(Store)
                .where(Store.business_id == business_id, Store.is_primary == True)
                .values(is_primary=False)
            )

        store = Store(
            business_id=business_id,
            name=data.name.strip(),
            code=data.code.strip() if data.code else None,
            address_line1=data.address_line1.strip(),
            address_line2=data.address_line2.strip() if data.address_line2 else None,
            city=data.city.strip(),
            state=data.state.strip(),
            pincode=data.pincode.strip(),
            phone_number=data.phone_number.strip() if data.phone_number else None,
            is_primary=data.is_primary,
            timezone=data.timezone,
            is_active=True,
        )
        db.add(store)
        db.commit()
        db.refresh(store)
        return StoreResponse.model_validate(store)

    @staticmethod
    def list_stores(
        db: Session, business_id: uuid.UUID, user_id: uuid.UUID
    ) -> list[StoreResponse]:
        """Lists active stores belonging to a business. Requires business.read permission."""
        membership = BusinessService.get_user_membership(db, business_id, user_id)
        if not check_permission(membership.role, Permissions.BUSINESS_READ):
            raise InsufficientPermissions(Permissions.BUSINESS_READ)

        stmt = (
            select(Store)
            .where(Store.business_id == business_id, Store.is_active == True)
            .order_by(Store.is_primary.desc(), Store.created_at.asc())
        )
        stores = db.scalars(stmt).all()
        return [StoreResponse.model_validate(s) for s in stores]

    @staticmethod
    def get_store(
        db: Session, business_id: uuid.UUID, store_id: uuid.UUID, user_id: uuid.UUID
    ) -> StoreResponse:
        """Retrieves verified details of a specific store."""
        membership = BusinessService.get_user_membership(db, business_id, user_id)
        if not check_permission(membership.role, Permissions.BUSINESS_READ):
            raise InsufficientPermissions(Permissions.BUSINESS_READ)

        stmt = select(Store).where(
            Store.id == store_id,
            Store.business_id == business_id,
            Store.is_active == True,
        )
        store = db.scalar(stmt)
        if not store:
            raise StoreNotFound("Store not found or access denied.")
        return StoreResponse.model_validate(store)

    @staticmethod
    def update_store(
        db: Session, business_id: uuid.UUID, store_id: uuid.UUID, user_id: uuid.UUID, data: StoreUpdate
    ) -> StoreResponse:
        """Updates store details. Requires business.update permission."""
        membership = BusinessService.get_user_membership(db, business_id, user_id)
        if not check_permission(membership.role, Permissions.BUSINESS_UPDATE):
            raise InsufficientPermissions(Permissions.BUSINESS_UPDATE)

        stmt = select(Store).where(
            Store.id == store_id,
            Store.business_id == business_id,
        )
        store = db.scalar(stmt)
        if not store:
            raise StoreNotFound("Store not found.")

        if data.is_primary is True and not store.is_primary:
            db.execute(
                update(Store)
                .where(Store.business_id == business_id, Store.is_primary == True)
                .values(is_primary=False)
            )
            store.is_primary = True
        elif data.is_primary is False:
            store.is_primary = False

        if data.name is not None:
            store.name = data.name.strip()
        if data.code is not None:
            store.code = data.code.strip() if data.code else None
        if data.address_line1 is not None:
            store.address_line1 = data.address_line1.strip()
        if data.address_line2 is not None:
            store.address_line2 = data.address_line2.strip() if data.address_line2 else None
        if data.city is not None:
            store.city = data.city.strip()
        if data.state is not None:
            store.state = data.state.strip()
        if data.pincode is not None:
            store.pincode = data.pincode.strip()
        if data.phone_number is not None:
            store.phone_number = data.phone_number.strip() if data.phone_number else None
        if data.timezone is not None:
            store.timezone = data.timezone
        if data.is_active is not None:
            store.is_active = data.is_active

        db.commit()
        db.refresh(store)
        return StoreResponse.model_validate(store)
