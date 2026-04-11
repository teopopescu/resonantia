"""Pydantic schemas for user profile / onboarding."""
from pydantic import BaseModel


class OnboardingRequest(BaseModel):
    clerk_user_id: str
    email: str | None = None
    name: str | None = None
    role: str  # scientist, lab_manager, bioinformatician, other
    focus_areas: list[str]  # plate_assays, microscopy, qpcr, sample_management
    organization: str | None = None


class OnboardingResponse(BaseModel):
    clerk_user_id: str
    role: str | None
    focus_areas: list[str] | None
    onboarding_completed: bool


class OnboardingCheckResponse(BaseModel):
    onboarding_completed: bool
