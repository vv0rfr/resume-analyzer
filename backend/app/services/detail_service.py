"""
岗位详情分析服务
实现深度分析（优势/短板/关键词/STAR/综合评价）+ 优化建议（改写/补充/面试/关键词）
两次 AI 调用并行执行，总耗时取两者中较慢的那个。
"""
import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from app.services.ai_client import call_deepseek

logger = logging.getLogger(__name__)


# ─── Prompt：深度分析 ────────────────────────────────────

ANALYSIS_SYSTEM_PROMPT = """你是一位拥有10年软件行业经验的资深技术猎头顾问。你每天为字节、阿里、腾讯等一线互联网公司推荐人才，深谙技术岗位的用人标准和简历评估方法。

你的能力：
- 精准识别候选人的技术优势和经验深度
- 犀利但不刻薄地指出能力短板
- 能从STAR法则视角评估经历质量
- 对技术关键词敏感，知道什么是该岗位真正的硬通货

你必须严格遵守：
1. 只输出一个合法的 JSON 对象，不要用 ```json 包裹，不要任何解释文字
2. strengths 至少3条，每条必须有简历中的具体证据，不能泛泛而谈
3. weaknesses 的 severity 必须准确：高=岗位核心能力缺失，中=有一定基础但深度不够，低=加分项缺失
4. keyword_analysis 要具体到技术名词级别
5. experience_assessment 用STAR法则（Situation-Task-Action-Result）视角评估
6. overall 要有明确结论，措辞符合猎头推荐语风格"""


def build_analysis_prompt(
    resume_text: str, parsed: dict, job_title: str,
    matched_skills: list[str], missing_skills: list[str],
) -> str:
    return f"""请对以下候选人进行「{job_title}」岗位的深度分析。

【原始简历】
{resume_text[:3000]}

【AI 已解析的结构化数据】
{json.dumps(parsed, ensure_ascii=False, indent=2)}

【匹配信息】
- 已匹配技能: {json.dumps(matched_skills, ensure_ascii=False)}
- 缺失技能: {json.dumps(missing_skills, ensure_ascii=False)}

请从以下维度分析：

1. strengths（核心优势）：从简历中找具体证据，说明为什么候选人适合这个岗位
2. weaknesses（能力短板）：对照岗位核心要求，诚实地指出不足
3. keyword_analysis（关键词分析）：技术关键词级别的逐项匹配
4. experience_assessment（经历评估）：用STAR法则视角看经历描述的质量
5. overall（综合评价）：猎头推荐语风格，150字以内，给出明确结论

返回 JSON（严格遵守此 schema）：
{{
  "strengths": [
    {{ "point": "优势点", "evidence": "简历中的具体依据", "impact": "对目标岗位的价值" }}
  ],
  "weaknesses": [
    {{ "point": "短板", "evidence": "具体表现", "severity": "高/中/低" }}
  ],
  "keyword_analysis": {{
    "matched": ["匹配的关键词"],
    "missing": ["缺失的关键词"],
    "suggestion": "关键词层面的整体建议（50字以内）"
  }},
  "experience_assessment": "用STAR法则视角评估，100字以内",
  "overall": "综合评价，猎头推荐语风格，150字以内"
}}"""


# ─── Prompt：优化建议 ────────────────────────────────────

OPTIMIZATION_SYSTEM_PROMPT = """你是一位资深的简历优化专家，曾帮助上千名技术人员优化简历并成功拿到offer。你熟悉国内互联网公司技术简历的写作规范和常见套路。

你的能力：
- 精准改写技术经历，使其从"做了什么"变为"创造了什么价值"
- 用STAR法则重构项目描述，突出量化数据
- 预判面试官会从简历的哪个薄弱点切入提问
- 知道每个技术岗位的关键词权重和ATS筛选逻辑

你必须严格遵守：
1. 只输出一个合法的 JSON 对象，不要用 ```json 包裹
2. rewrite_suggestions 至少3条，改写前后的对比要明显
3. 改写措辞要符合国内技术简历习惯（简洁、数据化、结果导向）
4. missing_items 要具体可操作，不能是"建议提升能力"这种空话
5. interview_questions 至少5个，覆盖技术深度、项目细节、架构决策
6. keyword_optimization 要说明放在简历的具体位置"""


def build_optimization_prompt(
    resume_text: str, job_title: str,
    matched_skills: list[str], missing_skills: list[str],
    weaknesses: list[dict],
) -> str:
    return f"""请针对「{job_title}」岗位，为以下候选人提供简历优化建议。

【原始简历】
{resume_text[:3000]}

【已知信息】
- 已匹配技能: {json.dumps(matched_skills, ensure_ascii=False)}
- 缺失技能: {json.dumps(missing_skills, ensure_ascii=False)}
- 短板: {json.dumps(weaknesses, ensure_ascii=False)}

请提供以下优化建议：

1. rewrite_suggestions（改写建议）：至少3条，每条要有原文对比
2. missing_items（补充项）：具体说明补充什么、放哪里、怎么写
3. structure_suggestions（结构建议）：简历整体结构怎么调整
4. interview_questions（面试问题）：至少5个，覆盖技术深度、项目细节、架构决策、团队协作
5. keyword_optimization（关键词优化）：建议加入什么关键词、放哪里

返回 JSON：
{{
  "rewrite_suggestions": [
    {{ "original": "原文", "improved": "优化后", "reason": "改写原因", "where": "位置说明" }}
  ],
  "missing_items": [
    {{ "item": "补充内容", "where": "放哪里", "example": "示例写法" }}
  ],
  "structure_suggestions": ["建议1", "建议2"],
  "interview_questions": [
    {{ "question": "面试问题", "reason": "为什么问（基于简历哪个点）", "suggestion": "建议回答方向" }}
  ],
  "keyword_optimization": {{
    "add_keywords": ["关键词"],
    "placement": "放在哪里"
  }}
}}"""


# ─── 服务类 ──────────────────────────────────────────────

class DetailService:
    """岗位详情分析服务——深度分析 + 优化建议并行执行"""

    def analyze_detail(self, **kwargs) -> dict[str, Any]:
        """
        并行执行深度分析 + 优化建议，返回合并结果。

        Returns:
            {"analysis": {...}, "optimization": {...}, "processing_time_ms": ...}
        """
        resume_text = kwargs.get("resume_text", "")
        parsed = kwargs.get("parsed_resume", {})
        job_title = kwargs.get("job_title", "")
        matched = kwargs.get("job_matched_skills", [])
        missing = kwargs.get("job_missing_skills", [])

        start = time.time()

        # ── 并行发起两次 AI 调用 ──────────────────────
        with ThreadPoolExecutor(max_workers=2) as executor:
            future_analysis = executor.submit(
                self._call_analysis,
                resume_text, parsed, job_title, matched, missing,
            )
            future_optimization = executor.submit(
                self._call_optimization,
                resume_text, job_title, matched, missing, [],
            )

            # 等待两个任务都完成，每个独立处理错误
            analysis = _safe_result(future_analysis, "深度分析")
            optimization = _safe_result(future_optimization, "优化建议")

        # 如果深度分析成功拿到短板信息，可以不用它来优化（优化已并行完成）
        # optimization 内部再次使用了 weaknesses，但第一次调用时传了空列表，
        # 这是合理的——优化 prompt 本身就覆盖了缺失技能信息

        elapsed = int((time.time() - start) * 1000)

        return {
            "analysis": analysis,
            "optimization": optimization,
            "processing_time_ms": elapsed,
        }

    def _call_analysis(
        self, resume_text: str, parsed: dict, job_title: str,
        matched: list[str], missing: list[str],
    ) -> dict[str, Any]:
        """调用 DeepSeek 进行深度分析"""
        prompt = build_analysis_prompt(resume_text, parsed, job_title, matched, missing)
        raw = call_deepseek(
            system_prompt=ANALYSIS_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.3,
            max_tokens=4096,
            label="深度分析",
        )
        return self._parse_json(raw, "深度分析")

    def _call_optimization(
        self, resume_text: str, job_title: str,
        matched: list[str], missing: list[str], weaknesses: list[dict],
    ) -> dict[str, Any]:
        """调用 DeepSeek 生成优化建议"""
        prompt = build_optimization_prompt(
            resume_text, job_title, matched, missing, weaknesses
        )
        raw = call_deepseek(
            system_prompt=OPTIMIZATION_SYSTEM_PROMPT,
            user_prompt=prompt,
            temperature=0.3,
            max_tokens=4096,
            label="优化建议",
        )
        return self._parse_json(raw, "优化建议")

    def _parse_json(self, raw: str, label: str) -> dict[str, Any]:
        """解析 AI 返回的 JSON，三层容错"""
        raw = raw.strip()

        for strategy in [
            lambda s: json.loads(s),
            lambda s: json.loads(
                re.search(r"```(?:json)?\s*\n?(.*?)\n?```", s, re.DOTALL).group(1).strip()
            ),
            lambda s: json.loads(s[s.find("{") : s.rfind("}") + 1]),
        ]:
            try:
                result = strategy(raw)
                if isinstance(result, dict):
                    return result
            except (json.JSONDecodeError, AttributeError, IndexError):
                continue

        logger.warning(f"[{label}] JSON 解析失败，原始: {raw[:300]}")
        return {}


def _safe_result(future, label: str) -> dict[str, Any]:
    """安全获取 Future 结果，失败时返回空字典"""
    try:
        return future.result()
    except Exception as e:
        logger.error(f"[{label}] 并行调用失败: {e}")
        return {}


# 全局单例
detail_service = DetailService()
