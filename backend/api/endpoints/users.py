"""
用户查询端点：获取医生列表、当前用户个人信息等。
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_current_user
from core.database import get_db
from models.user import User, UserRole

router = APIRouter()


class DoctorResponse(BaseModel):
    """医生列表项。"""
    id: int
    full_name: str
    department: str | None
    title: str | None = None
    specialty: str | None = None
    avatar_url: str | None = None
    bio: str | None = None

    model_config = {"from_attributes": True}


class UserProfileResponse(BaseModel):
    """当前用户完整个人信息。"""
    id: int
    username: str
    role: str
    full_name: str
    employee_id: str | None = None
    department: str | None = None
    title: str | None = None
    specialty: str | None = None
    bio: str | None = None
    phone: str | None = None
    email: str | None = None
    gender: str | None = None
    avatar_url: str | None = None
    security_question: str | None = None

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    """可编辑的个人信息字段。"""
    full_name: str | None = None
    title: str | None = None
    specialty: str | None = None
    bio: str | None = None
    phone: str | None = None
    email: str | None = None
    gender: str | None = None
    avatar_url: str | None = None


@router.get("/doctors", response_model=list[DoctorResponse])
async def get_doctors(
    department: str | None = Query(None, description="按科室筛选"),
    db: AsyncSession = Depends(get_db),
):
    """获取医生列表，可按科室筛选。"""
    stmt = select(User).where(User.role == UserRole.doctor)
    if department:
        stmt = stmt.where(User.department == department)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """获取当前登录用户的完整个人信息。"""
    return current_user


@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    update: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """部分更新当前登录用户的个人信息。"""
    user = await db.get(User, current_user.id)
    update_data = update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user
