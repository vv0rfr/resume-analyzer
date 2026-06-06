"""
简历相关 API 路由
"""
import uuid
import time
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query

from app.models.resume import (
    ResumeSubmitRequest, AnalysisResponse, AnalyzeDetailRequest,
    AnalyzeDetailResponse, ErrorResponse,
)
from app.services.analyzer import analyzer
from app.services.matcher import matcher
from app.services.detail_service import detail_service
from app.services.file_parser import extract_text
from app.services.history import history_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resume", tags=["简历分析"])

# 用户友好的错误文案映射
FRIENDLY_ERRORS = {
    "config_error": "服务配置异常，请联系管理员",
    "ai_service_error": "分析服务暂时不可用，请稍后重试",
    "parse_error": "分析结果异常，请重新提交",
}


async def _run_analysis_pipeline(content: str) -> dict:
    """统一的简历分析流水线：解析 + 匹配"""
    total_start = time.time()

    # 阶段 1：解析
    parse_result = analyzer.analyze(content)
    parsed = parse_result["parsed"]
    model_used = parse_result["model_used"]

    # 阶段 2：匹配
    job_matches = []
    try:
        job_matches = matcher.match(parsed)
    except Exception as e:
        logger.error(f"岗位匹配失败: {e}")

    processing_time_ms = int((time.time() - total_start) * 1000)

    return {
        "parsed": parsed,
        "job_matches": job_matches,
        "processing_time_ms": processing_time_ms,
        "model_used": model_used,
    }


@router.post(
    "/submit",
    responses={
        200: {"description": "分析成功"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "AI 服务错误"},
        503: {"model": ErrorResponse, "description": "配置错误"},
    },
)
async def submit_resume(
    content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """
    提交简历（文本粘贴 或 文件上传）进行 AI 分析 + 岗位匹配

    - **content**: 粘贴的简历文本
    - **file**: 上传的简历文件（PDF 或 Word）
    - 二者选其一即可
    """
    task_id = str(uuid.uuid4())[:8]

    # ── 确定输入来源 ────────────────────────────
    if file and file.filename:
        # 文件上传
        file_bytes = await file.read()
        try:
            resume_text = extract_text(
                filename=file.filename,
                content=file_bytes,
                mime_type=file.content_type or "",
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail={"status": "error", "message": str(e), "error_type": "invalid_file"})
    elif content and content.strip():
        resume_text = content.strip()
    else:
        raise HTTPException(
            status_code=400,
            detail={"status": "error", "message": "请粘贴简历文本或上传简历文件", "error_type": "empty_input"},
        )

    if len(resume_text) < 10:
        raise HTTPException(
            status_code=400,
            detail={"status": "error", "message": "简历内容太短，请至少输入10个字", "error_type": "too_short"},
        )

    # ── 执行分析流水线 ──────────────────────────
    try:
        result = await _run_analysis_pipeline(resume_text)
    except ValueError as e:
        raise HTTPException(status_code=503, detail={"status": "error", "message": FRIENDLY_ERRORS.get("config_error", str(e)), "error_type": "config_error"})
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": FRIENDLY_ERRORS.get("ai_service_error", str(e)), "error_type": "ai_service_error"})
    except Exception as e:
        logger.exception(f"未知错误: {e}")
        raise HTTPException(status_code=500, detail={"status": "error", "message": "分析服务暂时不可用，请稍后重试", "error_type": "unknown"})

    # ── 保存历史记录 ────────────────────────────
    try:
        history_service.save(task_id, resume_text, result)
    except Exception as e:
        logger.error(f"保存历史记录失败: {e}")

    return AnalysisResponse(
        id=task_id,
        status="completed",
        parse_result=result["parsed"],
        job_matches=result["job_matches"],
        processing_time_ms=result["processing_time_ms"],
        model_used=result["model_used"],
    )


@router.post(
    "/analyze-detail",
    response_model=AnalyzeDetailResponse,
    responses={
        200: {"description": "分析成功"},
        400: {"model": ErrorResponse, "description": "请求参数错误"},
        500: {"model": ErrorResponse, "description": "AI 服务错误"},
    },
)
async def analyze_job_detail(request: AnalyzeDetailRequest):
    """针对某个具体岗位，对简历进行深度分析 + 优化建议"""
    try:
        result = detail_service.analyze_detail(
            resume_text=request.resume_text,
            parsed_resume=request.parsed_resume,
            job_title=request.job_title,
            job_matched_skills=request.job_matched_skills,
            job_missing_skills=request.job_missing_skills,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": FRIENDLY_ERRORS["ai_service_error"], "error_type": "ai_service_error"})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"status": "error", "message": "分析服务暂时不可用，请稍后重试", "error_type": "unknown"})

    return AnalyzeDetailResponse(
        job_id=request.job_id,
        job_title=request.job_title,
        analysis=result["analysis"],
        optimization=result["optimization"],
        processing_time_ms=result["processing_time_ms"],
    )


# ─── 历史记录 ────────────────────────────────────────

@router.get("/history")
async def list_history():
    """获取历史记录列表（按时间倒序）"""
    return history_service.list_all()


@router.get("/history/{record_id}")
async def get_history(record_id: int):
    """获取某条历史记录的完整详情"""
    record = history_service.get(record_id)
    if not record:
        raise HTTPException(status_code=404, detail={"status": "error", "message": "记录不存在", "error_type": "not_found"})
    return record


@router.delete("/history/{record_id}")
async def delete_history(record_id: int):
    """删除某条历史记录"""
    history_service.delete(record_id)
    return {"status": "ok", "message": "已删除"}
