"""Onboarding API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from resonantia.db.session import get_db
from resonantia.dependencies import get_org_context
from resonantia.models.user_profile import UserProfile
from resonantia.schemas.user_profile import (
    OnboardingRequest,
    OnboardingResponse,
    OnboardingCheckResponse,
)

router = APIRouter()


@router.get("/check/{clerk_user_id}", response_model=OnboardingCheckResponse)
async def check_onboarding(
    clerk_user_id: str,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.clerk_user_id == clerk_user_id)
    )
    profile = result.scalar_one_or_none()
    return OnboardingCheckResponse(
        onboarding_completed=profile.onboarding_completed if profile else False
    )


@router.post("/complete", response_model=OnboardingResponse)
async def complete_onboarding(
    body: OnboardingRequest,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.clerk_user_id == body.clerk_user_id)
    )
    profile = result.scalar_one_or_none()

    if profile:
        profile.role = body.role
        profile.focus_areas = body.focus_areas
        profile.organization = body.organization
        profile.email = body.email
        profile.name = body.name
        profile.onboarding_completed = True
        profile.org_id = org_id
    else:
        profile = UserProfile(
            clerk_user_id=body.clerk_user_id,
            email=body.email,
            name=body.name,
            role=body.role,
            focus_areas=body.focus_areas,
            organization=body.organization,
            onboarding_completed=True,
            org_id=org_id,
        )
        db.add(profile)

    return OnboardingResponse(
        clerk_user_id=profile.clerk_user_id,
        role=profile.role,
        focus_areas=profile.focus_areas,
        onboarding_completed=True,
    )


@router.get("/profile/{clerk_user_id}", response_model=OnboardingResponse)
async def get_profile(
    clerk_user_id: str,
    org_id: str = Depends(get_org_context),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserProfile).where(UserProfile.clerk_user_id == clerk_user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        return OnboardingResponse(
            clerk_user_id=clerk_user_id,
            role=None,
            focus_areas=None,
            onboarding_completed=False,
        )
    return OnboardingResponse(
        clerk_user_id=profile.clerk_user_id,
        role=profile.role,
        focus_areas=profile.focus_areas,
        onboarding_completed=profile.onboarding_completed,
    )
