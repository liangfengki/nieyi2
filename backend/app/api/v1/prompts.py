from fastapi import APIRouter
from app.prompts.service import get_available_strategies

router = APIRouter()


@router.get("/strategies")
async def list_strategies():
    """返回所有可用的拍摄类型、模特设定、文字等级"""
    return get_available_strategies()
