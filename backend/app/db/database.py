"""数据库连接和表初始化"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone, timedelta

from app.core.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 北京时间
CST = timezone(timedelta(hours=8))


class HistoryRecord(Base):
    """分析历史记录表"""
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(32), index=True, nullable=False)
    candidate_name = Column(String(128), default="")
    summary_text = Column(Text, default="")
    full_result = Column(Text, nullable=False)  # JSON 字符串
    created_at = Column(DateTime, default=lambda: datetime.now(CST))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "task_id": self.task_id,
            "candidate_name": self.candidate_name,
            "summary_text": self.summary_text,
            "full_result": self.full_result,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }


def init_db():
    """创建所有表（如果不存在）"""
    Base.metadata.create_all(bind=engine)
