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

import uuid

from .meta import Base


class SermonDownloadProgress(Base):
    __tablename__ = 'sermon_download_progress'

    id: Mapped[int] = mapped_column(primary_key=True)
    video_id: Mapped[str] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=True)
    description: Mapped[str] = mapped_column(String, nullable=True)
    processed: Mapped[bool] = mapped_column(Boolean, nullable=True, default=False)
    created_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    video_created_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    english_caption_uri: Mapped[str] = mapped_column(String, nullable=True)


