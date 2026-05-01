"""Central API router that aggregates all sub-routers."""

from fastapi import APIRouter

from resonantia.api import chat, eln, evals, experiments, files, integrations, microscopy, onboarding, plates, processing, protocols, samples, tools, voice

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(plates.router, prefix="/plates", tags=["plates"])
api_router.include_router(samples.router, prefix="/samples", tags=["samples"])
api_router.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
api_router.include_router(microscopy.router, prefix="/microscopy", tags=["microscopy"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(processing.router, prefix="/processing", tags=["processing"])
api_router.include_router(tools.router, prefix="/tools", tags=["tools"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
api_router.include_router(evals.router, prefix="/evals", tags=["evals"])
api_router.include_router(onboarding.router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(eln.router, prefix="/eln", tags=["eln"])
api_router.include_router(protocols.router, prefix="/protocols", tags=["protocols"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
