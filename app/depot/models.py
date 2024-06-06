from typing import Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column, WriteOnlyMapped, relationship
from sqlalchemy import String, Integer, Text, Uuid, ForeignKey, UUID, TEXT, UniqueConstraint, DateTime, func

from app.extensions import db
import uuid


class File(db.Model):
    __tablename__ = 'file'
    id: Mapped[int] = mapped_column(primary_key=True)
    unique: Mapped[Uuid] = mapped_column(UUID(), unique=True, default=uuid.uuid4)
    path: Mapped[str] = mapped_column(TEXT())
    name: Mapped[str] = mapped_column(String(512))
    bundle_hash: Mapped[str] = mapped_column(String(256))
    downloads: WriteOnlyMapped['Download'] = relationship(back_populates='file')
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=func.now())
    __table_args__ = (UniqueConstraint('path', 'bundle_hash', name='_path_bundle_hash'),)

    def __init__(self, name: Optional[str], path: Optional[str], bundle_hash: Optional[str]):
        if name is not None:
            self.name = name
        if path is not None:
            self.path = path
        if bundle_hash is not None:
            self.bundle_hash = bundle_hash

    def __repr__(self):
        return '<File {}>'.format(self.name)


class Download(db.Model):
    __tablename__ = 'download'
    id: Mapped[int] = mapped_column(primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey('file.id'), index=True)
    file: Mapped[File] = relationship(back_populates='downloads')
    bundle_hash: Mapped[str] = mapped_column(String(256))
    download_count: Mapped[int] = mapped_column(default=0)
    download_max: Mapped[Optional[int]] = mapped_column(nullable=True, default=None)
    last_downloaded: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        index=True,
        onupdate=func.now(),
        default=func.now()
    )
    created: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, default=func.now())

    def __repr__(self):
        return '<Download {}>'.format(self.bundle_hash)
