"""Convenience entry point: ``python main.py`` to start the dev server."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "resonantia.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
