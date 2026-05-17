"""
认证端点：注册与登录。
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from core.security import create_access_token, get_password_hash, verify_password
from models.user import User, UserRole

router = APIRouter()


class RegisterRequest(BaseModel):
    """注册请求体。"""
    username: str = Field(..., min_length=1, max_length=64, description="账号 / 工号")
    password: str = Field(..., min_length=1, description="密码")
    full_name: str = Field(..., min_length=1, max_length=64, description="真实姓名")
    role: str = Field(..., pattern="^(doctor|patient)$", description="角色")
    employee_id: str | None = Field(None, max_length=64, description="工号（医生必填）")
    department: str | None = Field(None, max_length=64, description="科室（医生必填）")


class UserResponse(BaseModel):
    """登录响应中的用户信息。"""
    username: str
    role: str
    full_name: str

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """登录成功响应。"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """注册新用户。"""
    # 检查 username 是否已存在
    result = await db.execute(select(User).where(User.username == req.username))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=400, detail="账号已存在")

    # 创建用户
    user = User(
        username=req.username,
        hashed_password=get_password_hash(req.password),
        role=UserRole(req.role),
        full_name=req.full_name,
        employee_id=req.employee_id if req.role == "doctor" else None,
        department=req.department if req.role == "doctor" else None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"message": "注册成功", "username": user.username, "role": user.role.value}


@router.post("/login", response_model=LoginResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """用户登录，返回 JWT token。"""
    result = await db.execute(select(User).where(User.username == form.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="账号或密码错误")

    access_token = create_access_token(subject=user.username)
    return LoginResponse(
        access_token=access_token,
        user=UserResponse(
            username=user.username,
            role=user.role.value,
            full_name=user.full_name,
        ),
    )
