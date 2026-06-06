"""
简历相关数据模型
使用 Pydantic 定义请求/响应的数据结构
"""
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


# ─── 请求模型 ─────────────────────────────────────────

class ResumeSubmitRequest(BaseModel):
    """简历提交请求"""
    content: str = Field(
        ...,
        min_length=10,
        max_length=50000,
        description="简历文本内容",
        examples=["张三，3年Java开发经验，熟练掌握Spring Boot..."],
    )


class AnalyzeDetailRequest(BaseModel):
    """岗位详情分析请求"""
    resume_text: str = Field(..., description="原始简历文本")
    parsed_resume: dict[str, Any] = Field(..., description="AI 解析后的结构化数据")
    job_id: str = Field(..., description="岗位ID")
    job_title: str = Field(..., description="岗位名称")
    job_category: str = Field(default="", description="岗位分类")
    job_score: int = Field(default=0, description="匹配度评分")
    job_matched_skills: list[str] = Field(default_factory=list, description="已匹配技能")
    job_missing_skills: list[str] = Field(default_factory=list, description="缺失技能")


# ─── 解析结果子模型 ───────────────────────────────────

class ContactInfo(BaseModel):
    """联系方式"""
    phone: str = ""
    email: str = ""
    wechat: str = ""
    other: str = ""


class EducationItem(BaseModel):
    """教育经历"""
    school: str = ""
    degree: str = ""
    major: str = ""
    start_year: str = ""
    end_year: str = ""


class ExperienceItem(BaseModel):
    """工作经历"""
    company: str = ""
    role: str = ""
    start_date: str = ""
    end_date: str = ""
    highlights: list[str] = []


class ProjectItem(BaseModel):
    """项目经历"""
    name: str = ""
    role: str = ""
    description: str = ""
    tech_stack: list[str] = []
    highlights: list[str] = []


class ParsedResume(BaseModel):
    """AI 解析后的结构化简历"""
    name: str = ""
    contact: ContactInfo = Field(default_factory=ContactInfo)
    education: list[EducationItem] = []
    skills: list[str] = []
    experience: list[ExperienceItem] = []
    projects: list[ProjectItem] = []
    certifications: list[str] = []
    summary: str = ""


# ─── 岗位匹配子模型 ───────────────────────────────────

class JobMatch(BaseModel):
    """岗位匹配推荐"""
    job_id: str = ""
    title: str = ""
    category: str = ""
    score: int = 0
    summary: str = ""
    level_recommendation: str = ""
    matched_skills: list[str] = []
    missing_skills: list[str] = []


# ─── 响应模型 ─────────────────────────────────────────

class AnalysisResponse(BaseModel):
    """简历分析完整响应"""
    id: str = Field(..., description="分析任务ID")
    status: str = "completed"
    parse_result: ParsedResume = Field(..., description="AI 解析的结构化数据")
    job_matches: list[JobMatch] = Field(default_factory=list, description="岗位匹配推荐列表")
    processing_time_ms: int = Field(0, description="总处理耗时（毫秒）")
    model_used: str = Field("", description="使用的 AI 模型")
    created_at: datetime = Field(default_factory=datetime.now)


# ─── 深度分析子模型 ───────────────────────────────────

class StrengthPoint(BaseModel):
    """优势点"""
    point: str = ""
    evidence: str = ""
    impact: str = ""


class WeaknessPoint(BaseModel):
    """短板"""
    point: str = ""
    evidence: str = ""
    severity: str = "中"  # 高/中/低


class KeywordAnalysis(BaseModel):
    """关键词分析"""
    matched: list[str] = []
    missing: list[str] = []
    suggestion: str = ""


class JobAnalysis(BaseModel):
    """岗位深度分析"""
    strengths: list[StrengthPoint] = []
    weaknesses: list[WeaknessPoint] = []
    keyword_analysis: KeywordAnalysis = Field(default_factory=KeywordAnalysis)
    experience_assessment: str = ""
    overall: str = ""


# ─── 优化建议子模型 ──────────────────────────────────

class RewriteSuggestion(BaseModel):
    """改写建议"""
    original: str = ""
    improved: str = ""
    reason: str = ""
    where: str = ""


class MissingItem(BaseModel):
    """建议补充的内容"""
    item: str = ""
    where: str = ""
    example: str = ""


class InterviewQuestion(BaseModel):
    """面试问题"""
    question: str = ""
    reason: str = ""
    suggestion: str = ""


class KeywordOptimization(BaseModel):
    """关键词优化"""
    add_keywords: list[str] = []
    placement: str = ""


class OptimizationAdvice(BaseModel):
    """优化建议"""
    rewrite_suggestions: list[RewriteSuggestion] = []
    missing_items: list[MissingItem] = []
    structure_suggestions: list[str] = []
    interview_questions: list[InterviewQuestion] = []
    keyword_optimization: KeywordOptimization = Field(default_factory=KeywordOptimization)


# ─── 详情分析响应 ────────────────────────────────────

class AnalyzeDetailResponse(BaseModel):
    """岗位详情分析响应"""
    job_id: str = ""
    job_title: str = ""
    analysis: JobAnalysis = Field(default_factory=JobAnalysis)
    optimization: OptimizationAdvice = Field(default_factory=OptimizationAdvice)
    processing_time_ms: int = 0


class ErrorResponse(BaseModel):
    """错误响应"""
    status: str = "error"
    message: str = Field(..., description="错误信息")
    error_type: str = Field("unknown", description="错误类型")
