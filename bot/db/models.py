from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, relationship
from datetime import datetime


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)
    name = Column(String, nullable=False)
    group_name = Column(String, nullable=True)
    artists = Column(String, nullable=False)
    about = Column(String, nullable=True)
    is_registered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sent_requests = relationship(
        "ConnectRequest",
        foreign_keys="ConnectRequest.sender_id",
        back_populates="sender",
    )
    received_requests = relationship(
        "ConnectRequest",
        foreign_keys="ConnectRequest.receiver_id",
        back_populates="receiver",
    )

    def display_profile(self, show_contacts: bool = False) -> str:
        lines = [
            f"👤 *{self.name}*",
            f"🎓 Группа: {self.group_name or 'не указана'}",
            f"🎵 Исполнители: {self.artists}",
        ]
        if self.about:
            lines.append(f"📝 О себе: {self.about}")
        if show_contacts:
            lines.append(
                f"✉️ Telegram: @{self.username}"
                if self.username
                else "✉️ username скрыт"
            )
        else:
            lines.append("🔒 Контакт скрыт до принятия запроса")
        return "\n".join(lines)


class ConnectRequest(Base):
    __tablename__ = "connect_requests"

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship(
        "User", foreign_keys=[sender_id], back_populates="sent_requests"
    )
    receiver = relationship(
        "User", foreign_keys=[receiver_id], back_populates="received_requests"
    )
