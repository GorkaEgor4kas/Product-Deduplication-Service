from fastapi import FastAPI
from app.api.routes import router
import logging

# ---------- Logs settings ----------
logging.basicConfig(
    level=logging.INFO,  
    format='[%(levelname)s] %(name)s: %(message)s',  
    handlers=[
        logging.StreamHandler()  
    ]
)

app = FastAPI(
    title="Product Deduplication Service",
    description="API for detecting duplicate products using embeddings and rules",
    version="1.0.0"
)

#router connection
app.include_router(router, prefix="/api/v1")

#temporary plug
@app.get("/")
async def root():
    return {
        "service": "Product Deduplication Service",
        "docs": "/docs",
        "endpoints": {
            "check": "POST /api/v1/check",
            "confirm": "POST /api/v1/webhook/confirm",
            "health": "GET /api/v1/health",
            "stats": "GET /api/v1/stats"
        }
    }



