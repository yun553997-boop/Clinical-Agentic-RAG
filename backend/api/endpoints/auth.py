"""
认证端点：注册与登录。
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
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
    security_question: str | None = Field(None, max_length=256, description="密保问题（选填）")
    security_answer: str | None = Field(None, max_length=128, description="密保答案（选填）")


class UserResponse(BaseModel):
    """登录响应中的用户信息。"""
    id: int
    username: str
    role: str
    full_name: str
    avatar_url: str | None = None

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
        security_question=req.security_question,
        security_answer_hashed=get_password_hash(req.security_answer) if req.security_answer else None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"message": "注册成功", "username": user.username, "role": user.role.value}


@router.post("/login", response_model=LoginResponse)
async def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
    remember_me: bool = Query(False, description="是否延长 Token 有效期"),
):
    """用户登录，返回 JWT token。"""
    result = await db.execute(select(User).where(User.username == form.username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="账号或密码错误")

    expires_delta = (
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES_REMEMBER)
        if remember_me
        else None
    )
    access_token = create_access_token(subject=user.username, expires_delta=expires_delta)
    return LoginResponse(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            username=user.username,
            role=user.role.value,
            full_name=user.full_name,
            avatar_url=user.avatar_url,
        ),
    )


# ── 忘记密码相关端点 ──

class ForgotPasswordQuestionRequest(BaseModel):
    username: str = Field(..., description="用户名")


class ForgotPasswordVerifyRequest(BaseModel):
    username: str = Field(..., description="用户名")
    answer: str = Field(..., description="密保答案")


class ForgotPasswordResetRequest(BaseModel):
    reset_token: str = Field(..., description="验证通过的临时令牌")
    new_password: str = Field(..., min_length=1, description="新密码")


@router.post("/forgot-password/question")
async def get_security_question(req: ForgotPasswordQuestionRequest, db: AsyncSession = Depends(get_db)):
    """获取用户的密保问题。"""
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if user is None or user.security_question is None:
        raise HTTPException(status_code=404, detail="该账号未设置密保问题，请联系管理员")
    return {"username": user.username, "security_question": user.security_question}


@router.post("/forgot-password/verify")
async def verify_security_answer(req: ForgotPasswordVerifyRequest, db: AsyncSession = Depends(get_db)):
    """验证密保答案，返回临时重置令牌。"""
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.security_answer_hashed is None:
        raise HTTPException(status_code=400, detail="该账号未设置密保问题")
    if not verify_password(req.answer, user.security_answer_hashed):
        raise HTTPException(status_code=400, detail="密保答案错误")

    reset_token = create_access_token(
        subject=f"reset:{user.username}",
        expires_delta=timedelta(minutes=5),
    )
    return {"reset_token": reset_token, "message": "验证通过，请在5分钟内重置密码"}


@router.post("/forgot-password/reset")
async def reset_password(req: ForgotPasswordResetRequest, db: AsyncSession = Depends(get_db)):
    """使用重置令牌设置新密码。"""
    try:
        payload = jwt.decode(req.reset_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        sub = payload.get("sub", "")
        if not sub.startswith("reset:"):
            raise HTTPException(status_code=400, detail="无效的重置令牌")
        username = sub.split("reset:", 1)[1]
    except JWTError:
        raise HTTPException(status_code=400, detail="重置令牌已过期或无效")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.hashed_password = get_password_hash(req.new_password)
    await db.commit()
    return {"message": "密码重置成功，请返回登录"}
