import uuid
from datetime import datetime
from typing import Optional

from croniter import croniter
from pydantic import BaseModel, field_validator
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False, unique=True)
    command = Column(String, nullable=False)
    cron_expression = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    runs = relationship("RunHistory", back_populates="job", cascade="all, delete-orphan")


class RunHistory(Base):
    __tablename__ = "run_history"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    started_at = Column(DateTime, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    exit_code = Column(Integer, nullable=True)
    stdout = Column(Text, default="")
    stderr = Column(Text, default="")
    triggered_manually = Column(Boolean, default=False)

    job = relationship("Job", back_populates="runs")


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class JobCreate(BaseModel):
    name: str
    command: str
    cron_expression: str

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        if not croniter.is_valid(v):
            raise ValueError(f"Invalid cron expression: {v!r}")
        return v


class JobResponse(BaseModel):
    id: str
    name: str
    command: str
    cron_expression: str
    created_at: datetime
    is_active: bool

    model_config = {"from_attributes": True}


class RunHistoryResponse(BaseModel):
    id: str
    job_id: str
    started_at: datetime
    finished_at: Optional[datetime]
    exit_code: Optional[int]
    stdout: str
    stderr: str
    triggered_manually: bool

    model_config = {"from_attributes": True}
