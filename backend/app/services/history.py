"""历史记录服务"""
import json
import logging
from datetime import datetime, timezone, timedelta

from app.db.database import SessionLocal, HistoryRecord
from app.db.database import init_db

logger = logging.getLogger(__name__)

# 启动时自动建表
init_db()

CST = timezone(timedelta(hours=8))


class HistoryService:
    def save(self, task_id: str, resume_text: str, result: dict) -> int:
        """保存一条分析记录"""
        parsed = result.get("parsed", {})
        job_matches = result.get("job_matches", [])

        candidate_name = parsed.get("name", "未知")
        summary_text = resume_text[:100].replace("\n", " ")

        full_data = {
            "parse_result": parsed,
            "job_matches": job_matches,
            "original_text": resume_text,
        }

        db = SessionLocal()
        try:
            record = HistoryRecord(
                task_id=task_id,
                candidate_name=candidate_name,
                summary_text=summary_text,
                full_result=json.dumps(full_data, ensure_ascii=False),
            )
            db.add(record)
            db.commit()
            db.refresh(record)
            return record.id
        finally:
            db.close()

    def list_all(self) -> list[dict]:
        """获取历史列表（按时间倒序），不返回完整数据"""
        db = SessionLocal()
        try:
            records = (
                db.query(HistoryRecord)
                .order_by(HistoryRecord.created_at.desc())
                .limit(50)
                .all()
            )
            result = []
            for r in records:
                # 尝试读取岗位匹配数量
                job_count = 0
                try:
                    data = json.loads(r.full_result)
                    job_count = len(data.get("job_matches", []))
                except Exception:
                    pass

                result.append({
                    "id": r.id,
                    "task_id": r.task_id,
                    "candidate_name": r.candidate_name,
                    "summary_text": r.summary_text,
                    "job_count": job_count,
                    "created_at": r.created_at.isoformat() if r.created_at else "",
                })
            return result
        finally:
            db.close()

    def get(self, record_id: int) -> dict | None:
        """获取完整记录"""
        db = SessionLocal()
        try:
            record = db.query(HistoryRecord).filter(HistoryRecord.id == record_id).first()
            if not record:
                return None

            full_result = json.loads(record.full_result)
            return {
                "id": record.id,
                "task_id": record.task_id,
                "candidate_name": record.candidate_name,
                "summary_text": record.summary_text,
                "parse_result": full_result.get("parse_result", {}),
                "job_matches": full_result.get("job_matches", []),
                "original_text": full_result.get("original_text", ""),
                "created_at": record.created_at.isoformat() if record.created_at else "",
            }
        finally:
            db.close()

    def delete(self, record_id: int):
        """删除一条记录"""
        db = SessionLocal()
        try:
            db.query(HistoryRecord).filter(HistoryRecord.id == record_id).delete()
            db.commit()
        finally:
            db.close()


history_service = HistoryService()
