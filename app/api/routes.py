''''
endpoints /check, /webhook/confirm
'''
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import logging

from app.services.deduplication_service import Deduplication

#set logging
logger = logging.getLogger(__name__)

#creating router
router = APIRouter()

#initializing dedpulication service
dedup_service = Deduplication()


#------------------- Pydantic models for requests and responces validation -------------------

class CheckRequest(BaseModel):
    '''
    Product check request
    '''
    product_name: str = Field(..., min_length=1, description="Product's name")

    class Config:
        json_schema_extra = {
            "example": {
                "product_name": "RTX 5070 Ti"
            }
        }

class CheckResponce(BaseModel):
    '''
    Product check responce
    '''
    is_duplicate: bool
    duplicate_id: Optional[str] = None
    similarity_score: Optional[float] = None
    matched_name: Optional[str] = None
    candidates_count: int

    class Config:
        json_schema_extra = {
            "example": {
                "is_duplicate": True,
                "duplicate_id": "prod_123",
                "similarity_score": 0.94,
                "matched_name": "NVIDIA RTX 5070 Ti",
                "candidates_count": 5
            }
        }

class ConfirmRequest(BaseModel):
    '''
    New product adding request (webhook)
    '''
    product_id: str = Field(..., min_length=1, description="Product's ID in client's DB")
    product_name: str = Field(..., min_length=1, description="Product's name in client's DB")
    metadata: Optional[Dict] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "prod_123",
                "product_name": "NVIDIA RTX 5070 Ti",
                "metadata": None
            }
        }

class ConfirmResponce(BaseModel):
    '''
    Adding responce
    '''
    status: str
    message: str


class healthResponce(BaseModel):
    '''
    Healthcheck responce
    '''
    status: str
    total_products: int
    threshold: float

#------------------- Endpoints -------------------
@router.post("/check", response_model=CheckResponce)
async def check_duplicate(request: CheckRequest):
    '''
    Checks if new product duplicate or not
    
    If the product is duplicate:
        returns 'duplicate_id' and 'similarity_score'
    If the product is unique:
        returns 'is_duplicate' = False
    '''
    logger.info(f'Check product: {request.product_name}')
    try:
        result = await dedup_service.check(request.product_name)
        logger.info(f"Check status: {result['is_duplicate']}")
        return CheckResponce(**result)
    except Exception as e:
        logger.error(f"Check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@router.post("/webhook/confirm", response_model=ConfirmResponce)
async def confirm_product(request: ConfirmRequest):
    '''
    Adds a new unique product to the vector database.
    Selected by the main server AFTER the product is saved to its database.
    '''
    logger.info(f"Adding product with id: {request.product_id} to database")
    try:
        await dedup_service.add_new_product(
            product_id=request.product_id,
            product_name=request.product_name,
            metadata=request.metadata
        )
        logger.info(f"Product with id: {request.product_id} successfully added")
        return ConfirmResponce(
            status="ok",
            message= f"product {request.product_id} was added"
        )
    except Exception as e:
        logger.error(f"Adding product with id: {request.product_id} failed")
        raise HTTPException(status_code=500, detail=f"Failed to add product: {str(e)}")
    
@router.get("/health", response_model=healthResponce)
async def health_check():
    '''
    Service health check.
    Used for monitoring and Docker healthcheck.
    '''
    logger.info(f"Check server's health")
    try:
        check = await dedup_service.stats()
        logger.info("Health check is successful")
        return healthResponce(
            status="alive",
            total_products=check["total_products"],
            threshold=check["similarity_threshold"]
        )
    except Exception as e:
        logger.error("Can't check server's health")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
