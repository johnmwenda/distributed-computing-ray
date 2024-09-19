import datetime

from typing import List

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    func,
    Index,
    Integer,
    select,
    String,
    text,
    Text,
    Table
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import Mapped, relationship, mapped_column, column_property
from sqlalchemy.sql import func


from .meta import Base


class PledgeCategory(Base):
    __tablename__ = 'pledge_category'

    id = Column(Integer, primary_key=True)
    name = Column(Text, nullable=False)


class User(Base):
    __tablename__ = 'users'

    def __repr__(self):
        return f'Name:{self.name} - Phone:{self.phone} - Pledge:{self.pledge_amount} - Giving Group:{self.giving_group_id}'

    # id: Mapped[str] = mapped_column(String, primary_key=True, server_default=text('uuid_generate_v4()'))
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=True)
    email: Mapped[str] = mapped_column(String, nullable=True)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    otp_hash: Mapped[str] = mapped_column(String)
    pledge_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    created_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_login: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    id_label: Mapped[int] = mapped_column(Integer, nullable=True)
    otp_counter: Mapped[int] = mapped_column(Integer, nullable=True)

    giving_group_id: Mapped[int] = mapped_column(ForeignKey('giving_groups.id'))
    giving_group: Mapped['GivingGroup'] = relationship(back_populates='users')
    payments: Mapped[List['UserPayments']] = relationship(back_populates='user')

    sms_login_otp: Mapped[int] = mapped_column(Integer, nullable=True)
    client_side_uuid: Mapped[str] = mapped_column(String, nullable=True)


    def created_after_this_date(self, _date=None):
        if self.created_date.strftime('%Y-%m-%d') > _date:
            return True
        else:
            return False
    
    def created_on_this_date(self, _date=None):
        if _date:
            if self.created_date.strftime('%Y-%m-%d') == _date:
                return True
            else:
                return False
        else:
            today = datetime.datetime.now().strftime('%Y-%m-%d')
            if self.created_date.strftime('%Y-%m-%d') == today:
                return True
            else:
                return False

    def generate_sms_otp(self, request):
        import pyotp
        totp = pyotp.TOTP(self.otp_hash)
        otp = totp.now()
        self.sms_login_otp = otp
        request.dbsession.add(self)
        return otp

    def generate_uuid(self, request):
        import uuid
        client_side_uuid = str(uuid.uuid4())
        self.client_side_uuid = client_side_uuid
        request.dbsession.add(self)
        request.dbsession.flush()
        return client_side_uuid


Index('ix_phone', User.phone, mysql_length=255)


