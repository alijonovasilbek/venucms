from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, insert, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from schemes.schemes_users import DailyMetricsResponse,TodayCustomerInfo
from models.user_models import user
from schemes.schemes_users import (
    UserCreateRequest, UserUpdateRequest, UserResponse, UserListResponse, UserToggleResponse,
   DashboardResponse,CreateResponse,CreateResponse,SuccessResponse,DashboardStatistics
)
from auth_utils.auth_func import get_current_active_user, get_password_hash
from database import get_async_session
from  models.admin_models import customer,CustomerStatus


router = APIRouter(prefix="/superuser", tags=['Superuser Dashboard'])


# --- DECORATOR: CEO huquqini tekshirish ---
def require_ceo_access(current_user=Depends(get_current_active_user)):
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat Superuser ushbu amalni bajara oladi"
        )
    return current_user


# --- 1. CEO DASHBOARD - Barcha userlar ro'yxati ---
@router.get("/dashboard", response_model=DashboardResponse, summary="Superuser Dashboard - barcha userlar")
async def ceo_dashboard(
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_ceo_access),
):
    # Barcha userlarni olish (dict-like rows)
    result = await session.execute(select(user))
    rows = result.mappings().all()

    # Statistika
    user_count = len(rows)
    active_user_count = sum(1 for r in rows if r.get("is_active"))
    inactive_user_count = user_count - active_user_count

    # Ro‘yxatga yig‘ish
    users_list = []
    for r in rows:
        users_list.append({
            "id": r["id"],
            "email": r["email"],
            "name": r["name"],
            "surname": r["surname"],
            "is_active": r["is_active"],
        })

    return DashboardResponse(
        users=users_list,
        statistics=DashboardStatistics(
            user_count=user_count,
            active_user_count=active_user_count,
            inactive_user_count=inactive_user_count
        ),
    )


@router.get("/metrics/today", response_model=DailyMetricsResponse,
            summary="Bugungi metrikalar: customers, need_to_call count, total balance, due payments today")
async def get_today_metrics(

session: AsyncSession = Depends(get_async_session),
        current_user=Depends(require_ceo_access)

):

    today = datetime.now().date()

    today_cust_res = await session.execute(
        select(
            customer.c.id,
            customer.c.full_name,
            customer.c.platform,
            customer.c.username,
            customer.c.phone_number,
            customer.c.status,
            customer.c.assistant_name,
            customer.c.created_at,
        ).where(func.date(customer.c.created_at) == today)
         .order_by(customer.c.created_at.desc())
    )
    today_customers_rows = today_cust_res.fetchall()

    today_customers: list[TodayCustomerInfo] = []
    for row in today_customers_rows:
        today_customers.append(
            TodayCustomerInfo(
                id=row.id,
                full_name=row.full_name,
                platform=row.platform,
                username=row.username,
                phone_number=row.phone_number,
                status=row.status.value if hasattr(row.status, "value") else str(row.status),
                assistant_name=row.assistant_name,
                created_at=row.created_at.isoformat() if row.created_at else None,
            )
        )


    need_to_call_res = await session.execute(
        select(func.count()).where(customer.c.status == CustomerStatus.need_to_call)
    )
    need_to_call_count = int(need_to_call_res.scalar() or 0)


    return DailyMetricsResponse(
        today_customers=today_customers,
        need_to_call_count=need_to_call_count,

    )


# --- 2. USER YARATISH ---
@router.post("/users", response_model=CreateResponse, summary="Yangi user yaratish")
async def create_user(
        user_data: UserCreateRequest,
        session: AsyncSession = Depends(get_async_session),
        current_user=Depends(require_ceo_access)
):
    """
    Yangi foydalanuvchi yaratish (faqat CEO)
    """
    # Email mavjudligini tekshirish
    existing_user_result = await session.execute(
        select(user).where(user.c.email == user_data.email)
    )
    if existing_user_result.fetchone():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bu email allaqachon mavjud"
        )

    # Parolni hash qilish
    hashed_password = get_password_hash(user_data.password)

    # Yangi user yaratish
    user_dict = {
        "email": user_data.email,
        "name": user_data.name,
        "surname": user_data.surname,
        "password": hashed_password,
        "is_active": user_data.is_active
    }

    result = await session.execute(insert(user).values(**user_dict))
    await session.commit()

    return CreateResponse(
        message="Foydalanuvchi muvaffaqiyatli yaratildi",
        id=result.inserted_primary_key[0]
    )


# --- 3. USER YANGILASH ---
@router.put("/users/{user_id}", response_model=SuccessResponse, summary="User ma'lumotlarini yangilash")
async def update_user(
        user_id: int,
        user_data: UserUpdateRequest,
        session: AsyncSession = Depends(get_async_session),
        current_user=Depends(require_ceo_access)
):
    """
    Mavjud foydalanuvchi ma'lumotlarini yangilash
    """
    # User mavjudligini tekshirish
    existing_user_result = await session.execute(
        select(user).where(user.c.id == user_id)
    )
    existing_user = existing_user_result.fetchone()

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )

    # Yangilanadigan ma'lumotlarni tayyorlash
    update_data = {}
    for field, value in user_data.dict(exclude_unset=True).items():
        if field == "password" and value:
            update_data[field] = get_password_hash(value)
        elif value is not None:
            update_data[field] = value

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yangilanadigan ma'lumot topilmadi"
        )

    # Ma'lumotlarni yangilash
    await session.execute(
        update(user).where(user.c.id == user_id).values(**update_data)
    )
    await session.commit()

    return SuccessResponse(message="Foydalanuvchi muvaffaqiyatli yangilandi")

# --- 3.1 USER QISMAN YANGILASH (PATCH) ---
@router.patch("/users/{user_id}", response_model=SuccessResponse, summary="User qisman yangilash (PATCH)")
async def patch_user(
    user_id: int,
    user_data: UserUpdateRequest,  # barcha maydonlar ixtiyoriy
    session: AsyncSession = Depends(get_async_session),
    current_user=Depends(require_ceo_access)
):
    """
    Mavjud foydalanuvchini qisman yangilash (faqat yuborilgan maydonlar)
    """
    # Mavjud user bormi?
    existing_user_result = await session.execute(
        select(user).where(user.c.id == user_id)
    )
    existing = existing_user_result.mappings().first()
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )

    update_data = {}

    # email o'zgarayotgan bo'lsa — unikal ekanini tekshiramiz
    if user_data.email is not None and user_data.email != existing["email"]:
        dup = await session.execute(
            select(user.c.id).where(user.c.email == user_data.email, user.c.id != user_id)
        )
        if dup.scalar():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Bu email allaqachon mavjud"
            )
        update_data["email"] = user_data.email

    # name / surname
    if user_data.name is not None:
        update_data["name"] = user_data.name
    if user_data.surname is not None:
        update_data["surname"] = user_data.surname

    # password (hashlab saqlaymiz)
    if user_data.password:
        update_data["password"] = get_password_hash(user_data.password)

    # is_active
    if user_data.is_active is not None:
        update_data["is_active"] = user_data.is_active

    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Yangilanadigan ma'lumot topilmadi"
        )

    await session.execute(
        update(user).where(user.c.id == user_id).values(**update_data)
    )
    await session.commit()

    return SuccessResponse(message="Foydalanuvchi qisman yangilandi")


# --- 4. USER O'CHIRISH ---
@router.delete("/users/{user_id}", response_model=SuccessResponse, summary="User o'chirish")
async def delete_user(
        user_id: int,
        session: AsyncSession = Depends(get_async_session),
        current_user=Depends(require_ceo_access)
):

    # User mavjudligini tekshirish
    existing_user_result = await session.execute(
        select(user).where(user.c.id == user_id)
    )
    existing_user = existing_user_result.fetchone()

    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )

    # User o'chirish
    await session.execute(delete(user).where(user.c.id == user_id))
    await session.commit()

    return SuccessResponse(message=f"Foydalanuvchi {existing_user.email} muvaffaqiyatli o'chirildi")


# --- 5. USER ACTIVE/INACTIVE TOGGLE ---
@router.patch("/users/{user_id}/toggle-active", response_model=UserToggleResponse,
              summary="User active/inactive toggle")
async def toggle_user_active(
        user_id: int,
        session: AsyncSession = Depends(get_async_session),
        current_user=Depends(require_ceo_access)
):
    """
    Foydalanuvchining active holatini o'zgartirish
    """
    # User topish
    user_result = await session.execute(
        select(user).where(user.c.id == user_id)
    )
    user_data = user_result.fetchone()

    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Foydalanuvchi topilmadi"
        )

    # Active holatini o'zgartirish
    new_active_status = not user_data.is_active
    await session.execute(
        update(user).where(user.c.id == user_id).values(is_active=new_active_status)
    )
    await session.commit()

    # Yangi statistikalarni hisoblash
    active_count_result = await session.execute(
        select(func.count(user.c.id)).where(user.c.is_active == True)
    )
    inactive_count_result = await session.execute(
        select(func.count(user.c.id)).where(user.c.is_active == False)
    )

    active_user_count = active_count_result.scalar()
    inactive_user_count = inactive_count_result.scalar()

    return UserToggleResponse(
        is_active=new_active_status,
        active_user_count=active_user_count,
        inactive_user_count=inactive_user_count
    )

