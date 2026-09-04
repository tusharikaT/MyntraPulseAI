import os
import sys

# Add the parent directory to the path so modules can import from each other
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import overview, themes, copilot, lens, sync

app = FastAPI(
    title="Myntra Wishlist Discovery API",
    description="Backend APIs for the PM Priority Radar and Discovery Lens.",
    version="1.0.0"
)

# Allow CORS for frontend
FRONTEND_URL = os.getenv("FRONTEND_URL", "*")
allowed_origins = [FRONTEND_URL, "http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(overview.router, prefix="/api")
app.include_router(themes.router, prefix="/api")
app.include_router(copilot.router, prefix="/api")
app.include_router(lens.router, prefix="/api")
app.include_router(sync.router, prefix="/api")

@app.get("/")
def read_root():
    return {"status": "Discovery Engine API Running", "docs": "/docs"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

