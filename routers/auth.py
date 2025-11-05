from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from schemes.schemes_auth import *
from auth_utils.auth_func import *
from auth_utils.email_service import email_service

from config import VERIFICATION_CODE_EXPIRE_MINUTES, PASSWORD_RESET_EXPIRE_MINUTES
from sqlalchemy import func
router = APIRouter(prefix="/auth",tags=['Autentifikatsiya'])
from auth_utils.db_code_storage import db_code_storage

from schemes.schemes_auth import TokenPair, RefreshIn

ACCESS_EXPIRES_SEC = 60 * ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_EXPIRES_SEC = 60 * 60 * 24 * REFRESH_TOKEN_EXPIRE_DAYS

@router.post("/register", response_model=SuccessResponse, summary="Ro'yxatdan o'tish")
async def register(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
):
    # Email mavjudligini tekshirish
    result = await session.execute(select(user).where(user.c.email == user_data.email))
    existing_user = result.fetchone()
    print(existing_user)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu email allaqachon ro'yxatdan o'tgan",
        )

    # Database'dagi foydalanuvchilar soni
    users_count_result = await session.execute(select(func.count(user.c.id)))
    users_count = users_count_result.scalar()
    is_first_user = users_count == 0

    # Birinchi user CEO bo‘ladi
    if is_first_user:
        is_admin = True
        is_staff = True
        is_superuser = True
        print(f"🚀 Birinchi user yaratilmoqda: {user_data.email} - Superuser sifatida")
    else:

        is_admin = False
        is_staff = False
        is_superuser = False

    # Parolni xeshlash
    hashed_password = get_password_hash(user_data.password)

    user_dict = {
        "email": user_data.email,
        "name": user_data.name,
        "surname": user_data.surname,
        "password": hashed_password,
        "is_active": False,
        "is_admin": is_admin,
        "is_staff": is_staff,
        "is_superuser": is_superuser,
    }

    result = await session.execute(insert(user).values(**user_dict))
    user_id = result.inserted_primary_key[0]

    await session.commit()

    # Email verification code
    code = email_service.generate_verification_code()
    await db_code_storage.set_code(session, user_id, code, "verify_email")

    background_tasks.add_task(email_service.send_verification_email, user_data.email, code)

    msg = (
        f"🎉 Birinchi Superuser yaratildi! {user_data.email} ga tasdiqlash kodi yuborildi."
        if is_first_user
        else f"Ro'yxatdan o'tish muvaffaqiyatli! {user_data.email} ga tasdiqlash kodi yuborildi."
    )

    return SuccessResponse(message=msg)


# 2. EMAIL TASDIQLASH
@router.post("/verify-email", response_model=TokenPair, summary="Email tasdiqlash")
async def verify_email(
    verification: EmailVerificationConfirm,
    session: AsyncSession = Depends(get_async_session)
):
    # 1) Foydalanuvchi ID sini topish
    result = await session.execute(
        select(user.c.id, user.c.is_active).where(user.c.email == verification.email)
    )
    row = result.mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    user_id = row["id"]

    # 2) Kodni tekshirish
    saved_code = await db_code_storage.get_code(session, user_id, "verify_email")
    if not saved_code or saved_code != verification.code:
        raise HTTPException(status_code=400, detail="Tasdiqlash kodi noto‘g‘ri yoki topilmadi")

    # 3) Foydalanuvchini faollashtirish
    await session.execute(update(user).where(user.c.id == user_id).values(is_active=True))
    await session.commit()

    # 4) Kodni bekor qilish
    await db_code_storage.invalidate_code(session, user_id, "verify_email")

    # 5) Tokenlar (DICTIONARY payload!)
    payload = {"sub": verification.email, "uid": user_id}

    access  = create_access_token(payload)          # type="access" ichida qo‘shiladi
    refresh = create_refresh_token(payload)         # type="refresh" ichida qo‘shiladi

    return TokenPair(
        access_token=access,
        refresh_token=refresh,
        token_type="bearer",
        expires_in=ACCESS_EXPIRES_SEC,
        refresh_expires_in=REFRESH_EXPIRES_SEC,
    )



# 3. VERIFICATION KODNI QAYTA YUBORISH
@router.post("/resend-verification", response_model=SuccessResponse)
async def resend_verification_code(
    request: EmailVerificationRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(user).where(user.c.email == request.email))
    user_data = result.fetchone()

    if not user_data:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    if user_data.is_active:
        raise HTTPException(status_code=400, detail="Email allaqachon tasdiqlangan")

    # user_id olish
    result_id = await session.execute(select(user.c.id).where(user.c.email == request.email))
    user_id = result_id.scalar()

    code = email_service.generate_verification_code()
    await db_code_storage.set_code(session, user_id, code, "verify_email")

    background_tasks.add_task(email_service.send_verification_email, request.email, code)

    return SuccessResponse(message="Yangi tasdiqlash kodi yuborildi")


# 4. LOGIN
# routers/auth.py — LOGIN (eski util bilan)

@router.post("/login", response_model=TokenPair, summary="Tizimga kirish (access+refresh)")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(user).where(user.c.email == form_data.username))
    row = result.mappings().first()  # RowMapping (dict-like) — tavsiya
    if not row:
        raise HTTPException(status_code=401, detail="Email yoki parol noto‘g‘ri")

    hashed = row.get("password") or row.get("password_hash")
    if not hashed or not verify_password(form_data.password, hashed):
        raise HTTPException(status_code=401, detail="Email yoki parol noto‘g‘ri")

    if not row.get("is_active", True):
        raise HTTPException(status_code=400, detail="Akkaunt faol emas. Email tasdiqlang.")

    # ACCESS — eski util: data=..., expires_delta=...
    access_payload = {"sub": row["email"], "type": "access", "uid": row["id"]}
    access_token = create_access_token(
        data=access_payload,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    # REFRESH — eski utilga mos alohida funksiya yozib qo‘ying:
    # create_refresh_token(data: dict, expires_delta: Optional[timedelta])
    refresh_payload = {"sub": row["email"], "type": "refresh", "uid": row["id"]}
    refresh_token = create_refresh_token(
        data=refresh_payload,
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_expires_in=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )


# 5. PAROLNI UNUTISH
@router.post("/forgot-password", response_model=SuccessResponse)
async def forgot_password(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(user.c.id).where(user.c.email == request.email))
    user_id = result.scalar()
    print(user_id)

    if user_id:
        code = email_service.generate_verification_code()
        print(code)
        await db_code_storage.set_code(session, user_id, code, "reset_password")

        background_tasks.add_task(email_service.send_password_reset_email, request.email, code)

    return SuccessResponse(message="Agar email mavjud bo'lsa, parol tiklash kodi yuborildi")


# 6. PAROLNI TIKLASH
@router.post("/reset-password", response_model=SuccessResponse)
async def reset_password(
    reset_data: PasswordResetConfirm,
    session: AsyncSession = Depends(get_async_session),
):
    result = await session.execute(select(user.c.id).where(user.c.email == reset_data.email))
    user_id = result.scalar()

    if not user_id:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    saved_code = await db_code_storage.get_code(session, user_id, "reset_password")

    if not saved_code or saved_code != reset_data.code:
        raise HTTPException(status_code=400, detail="Kod noto‘g‘ri yoki topilmadi")

    # Parolni yangilash
    hashed_password = get_password_hash(reset_data.new_password)
    await session.execute(update(user).where(user.c.id == user_id).values(password=hashed_password))
    await session.commit()

    # Kodni 0 ga o‘zgartirish
    await db_code_storage.invalidate_code(session, user_id, "reset_password")

    return SuccessResponse(message="Parol muvaffaqiyatli yangilandi")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user=Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    """
    Joriy foydalanuvchi ma'lumotlari va sahifa ruxsatlari
    """

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        surname=current_user.surname,
        is_active=current_user.is_active,
    )

@router.post("/refresh", response_model=TokenPair, summary="Refresh → yangi access(+refresh)")
async def refresh_tokens(
    payload: RefreshIn,
    session: AsyncSession = Depends(get_async_session),
):
    data = decode_refresh(payload.refresh_token)  # REFRESH_SECRET_KEY bilan tekshiradi

    if data.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Token turi noto‘g‘ri")

    email = data.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Refresh token noto‘g‘ri (sub yo‘q)")

    # Foydalanuvchi faolmi?
    res = await session.execute(select(user).where(user.c.email == email))
    row = res.mappings().first()
    if not row or not row.get("is_active", True):
        raise HTTPException(status_code=401, detail="Foydalanuvchi faol emas yoki topilmadi")

    # Rotatsiya (yangi juftlik)
    new_access = create_access_token(
        data={"sub": email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    new_refresh = create_refresh_token(
        data={"sub": email},
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    return TokenPair(
        access_token=new_access,
        refresh_token=new_refresh,
        token_type="bearer",
        expires_in=ACCESS_EXPIRES_SEC,
        refresh_expires_in=REFRESH_EXPIRES_SEC,
    )
