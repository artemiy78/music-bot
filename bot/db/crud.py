from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from bot.db.models import User, ConnectRequest


async def get_user_by_telegram_id(
    session: AsyncSession, telegram_id: int
) -> User | None:
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    return result.scalar_one_or_none()


async def create_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None,
    name: str,
    group_name: str | None,
    artists: str,
    about: str | None,
) -> User:
    user = User(
        telegram_id=telegram_id,
        username=username,
        name=name,
        group_name=group_name,
        artists=artists,
        about=about,
        is_registered=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user(session: AsyncSession, user: User, **kwargs) -> User:
    for key, value in kwargs.items():
        setattr(user, key, value)
    await session.commit()
    await session.refresh(user)
    return user


async def search_users_by_artist(
    session: AsyncSession,
    artist: str,
    exclude_telegram_id: int,
) -> list[User]:
    result = await session.execute(
        select(User).where(
            User.is_registered == True,
            User.telegram_id != exclude_telegram_id,
        )
    )
    all_users = result.scalars().all()
    artist_lower = artist.strip().lower()
    return [u for u in all_users if artist_lower in u.artists.lower()]


async def get_connect_request(
    session: AsyncSession, sender_id: int, receiver_id: int
) -> ConnectRequest | None:
    result = await session.execute(
        select(ConnectRequest).where(
            ConnectRequest.sender_id == sender_id,
            ConnectRequest.receiver_id == receiver_id,
        )
    )
    return result.scalar_one_or_none()


async def create_connect_request(
    session: AsyncSession, sender_id: int, receiver_id: int
) -> ConnectRequest:
    req = ConnectRequest(sender_id=sender_id, receiver_id=receiver_id)
    session.add(req)
    await session.commit()
    await session.refresh(req)
    return req


async def get_pending_requests_for_user(
    session: AsyncSession, user_id: int
) -> list[ConnectRequest]:
    result = await session.execute(
        select(ConnectRequest)
        .options(
            selectinload(ConnectRequest.sender), selectinload(ConnectRequest.receiver)
        )
        .where(
            ConnectRequest.receiver_id == user_id,
            ConnectRequest.status == "pending",
        )
    )
    return result.scalars().all()


async def update_request_status(
    session: AsyncSession, request: ConnectRequest, status: str
) -> ConnectRequest:
    request.status = status
    await session.commit()
    return request


async def get_accepted_connects(
    session: AsyncSession, user_id: int
) -> list[ConnectRequest]:
    result = await session.execute(
        select(ConnectRequest)
        .options(
            selectinload(ConnectRequest.sender), selectinload(ConnectRequest.receiver)
        )
        .where(
            or_(
                ConnectRequest.sender_id == user_id,
                ConnectRequest.receiver_id == user_id,
            ),
            ConnectRequest.status == "accepted",
        )
    )
    return result.scalars().all()
