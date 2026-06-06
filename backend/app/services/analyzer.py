"""
简历分析服务
使用 DeepSeek API 从简历文本中提取结构化信息
"""
import json
import re
import time
import logging
from typing import Any

from app.core.config import get_settings
from app.services.ai_client import call_deepseek

logger = logging.getLogger(__name__)

# ─── Prompt 设计 ─────────────────────────────────────────

SYSTEM_PROMPT = """你是一位拥有10年经验的资深简历分析师和人才顾问，覆盖技术、财务、制造、运营、设计、教育、医疗等多个行业。你擅长从各种格式的中文简历中精准提取结构化信息。

你的核心能力：
- 能从混乱、非结构化的文本中识别出所有关键信息，无论属于哪个行业
- 能识别各类专业技能、行业术语和工具（包括但不限于编程语言、财务软件、设计工具、工程软件等）
- 对缺失信息保持诚实——没有就是没有，绝不编造

你必须严格遵守以下规则：
1. 只输出一个合法的 JSON 对象，不要包含任何解释、前言、后缀
2. 不要用 ```json 代码块包裹，直接输出裸 JSON
3. 所有字段都必须存在，没有信息则用空字符串 "" 或空数组 []
4. 技能名称统一使用标准写法（如 Kubernetes 而非 k8s，React 而非 React.js）
5. 时间格式统一为 "YYYY-MM" 或 "YYYY"（如果只有年份）
6. 联系方式只提取明确写出的，不要推测
"""

USER_PROMPT_TEMPLATE = """请分析以下简历文本，提取所有结构化信息。

要求：
- 仔细阅读每一个字，不要遗漏任何技能、项目、经历
- 技能提取要全面：包括编程语言、框架、数据库、工具、平台、软技能，以及财务（会计核算/纳税申报）、机械（CATIA/ANSYS）、设计（Figma/Photoshop）、运营（用户增长/内容策划）等行业专业技能
- 工作/项目经历的 highlights 要提取具体成果（含数字指标更好）
- 如果某个字段确实没有信息，用空数组 [] 或空字符串 ""
- 一句话摘要（summary）控制在30字以内，概括核心背景

输出 JSON 必须严格按以下 schema：

{
  "name": "姓名（字符串）",
  "contact": {
    "phone": "电话（字符串或空）",
    "email": "邮箱（字符串或空）",
    "wechat": "微信（字符串或空）",
    "other": "其他联系方式（字符串或空）"
  },
  "education": [
    {
      "school": "学校名",
      "degree": "学位（本科/硕士/博士/大专等）",
      "major": "专业",
      "start_year": "开始年份",
      "end_year": "结束年份"
    }
  ],
  "skills": ["技能1", "技能2", ...],
  "experience": [
    {
      "company": "公司名",
      "role": "职位",
      "start_date": "开始时间（YYYY-MM 或 YYYY）",
      "end_date": "结束时间（YYYY-MM 或 YYYY，至今则填'至今'）",
      "highlights": ["亮点1", "亮点2", ...]
    }
  ],
  "projects": [
    {
      "name": "项目名",
      "role": "角色",
      "description": "项目描述（一句话）",
      "tech_stack": ["技术1", "技术2", ...],
      "highlights": ["亮点1", "亮点2", ...]
    }
  ],
  "certifications": ["证书1", "证书2", ...],
  "summary": "一句话概括（30字以内）"
}

以下是简历文本：
---
{content}
---"""


class ResumeAnalyzer:
    """简历分析器——接入 DeepSeek API 进行智能解析"""

    def analyze(self, content: str) -> dict[str, Any]:
        """
        分析简历文本，提取结构化信息

        Args:
            content: 简历文本内容

        Returns:
            {
                "original_content": 原始文本,
                "parsed": 解析后的结构化数据,
                "elapsed_ms": 处理耗时（毫秒）,
                "model_used": 使用的模型名
            }

        Raises:
            ValueError: API Key 未配置
            RuntimeError: DeepSeek API 调用失败
        """
        # 检查 API Key
        settings = get_settings()
        if settings.deepseek_api_key in ("", "your-deepseek-api-key-here"):
            raise ValueError(
                "DeepSeek API Key 未配置。请在 backend/.env 文件中设置 "
                "DEEPSEEK_API_KEY=你的真实Key"
            )

        if len(content.strip()) < 10:
            raise ValueError("简历内容太短，请至少输入10个字")

        start_time = time.time()

        # 通过公共模块调用 DeepSeek（带超时+重试）
        raw_output = call_deepseek(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=USER_PROMPT_TEMPLATE.replace("{content}", content),
            temperature=0.1,
            max_tokens=4096,
            label="简历解析",
        )

        elapsed_ms = int((time.time() - start_time) * 1000)

        # 调试日志：输出 DeepSeek 原始返回（前 500 字）
        logger.info(
            f"DeepSeek 返回: 长度={len(raw_output)} 字符, "
            f"前500字预览=\n{raw_output[:500]}"
        )

        # 解析 JSON
        parsed = self._parse_json(raw_output)

        return {
            "original_content": content,
            "parsed": parsed,
            "elapsed_ms": elapsed_ms,
            "model_used": settings.deepseek_model,
        }

    def _parse_json(self, raw: str) -> dict[str, Any]:
        """
        从 AI 返回的文本中提取 JSON

        处理各种可能的格式问题：
        - 纯 JSON
        - JSON 被 ```json ... ``` 包裹
        - JSON 前后有额外文字
        """
        raw = raw.strip()

        # 尝试1：直接解析
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # 尝试2：去除 markdown 代码块包裹
        fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", raw, re.DOTALL)
        if fence_match:
            try:
                return json.loads(fence_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 尝试3：找到第一个 { 和最后一个 } 之间的内容
        first_brace = raw.find("{")
        last_brace = raw.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            try:
                return json.loads(raw[first_brace : last_brace + 1])
            except json.JSONDecodeError:
                pass

        # 解析失败——返回原始文本作为兜底
        logger.warning(f"无法解析 AI 返回的 JSON，原始文本前200字: {raw[:200]}")
        return {
            "name": "",
            "contact": {"phone": "", "email": "", "wechat": "", "other": ""},
            "education": [],
            "skills": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "summary": "",
            "_parse_error": True,
            "_raw_output": raw[:500],
        }


# 全局单例
analyzer = ResumeAnalyzer()
