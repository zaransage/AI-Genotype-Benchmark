import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from pydantic import BaseModel

from database import Base


# ---------------------------------------------------------------------------
# ORM models
# ---------------------------------------------------------------------------

class JobORM(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    command = Column(String, nullable=False)
    cron_expression = Column(String, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    runs = relationship(
        "JobRunORM", back_populates="job", cascade="all, delete-orphan"
    )


class JobRunORM(Base):
    __tablename__ = "job_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    exit_code = Column(Integer, nullable=True)
    stdout = Column(Text, default="", nullable=False)
    stderr = Column(Text, default="", nullable=False)
    triggered_manually = Column(Boolean, default=False, nullable=False)

    job = relationship("JobORM", back_populates="runs")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class JobCreate(BaseModel):
    name: str
    command: str
    cron_expression: str


class JobResponse(BaseModel):
    id: str
    name: str
    command: str
    cron_expression: str
    enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class JobRunResponse(BaseModel):
    id: str
    job_id: str
    started_at: datetime
    finished_at: Optional[datetime]
    exit_code: Optional[int]
    stdout: str
    stderr: str
    triggered_manually: bool

    model_config = {"from_attributes": True}
