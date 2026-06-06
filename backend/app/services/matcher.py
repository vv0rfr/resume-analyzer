"""
岗位匹配与打分服务
两步走策略：
1. 知识库匹配：将简历与 64 个知识库岗位对比打分
2. 自主推荐：不依赖知识库，AI 根据简历内容自主推荐精准岗位
两次结果合并排序输出
"""
import json
import logging
import time
import re
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.services.ai_client import call_deepseek

logger = logging.getLogger(__name__)

# ─── 加载岗位知识库 ────────────────────────────────────

JOBS_PATH = Path(__file__).parent.parent / "data" / "jobs.json"

with open(JOBS_PATH, "r", encoding="utf-8") as f:
    JOBS_KNOWLEDGE_BASE = json.load(f)

logger.info(f"加载岗位知识库: {len(JOBS_KNOWLEDGE_BASE)} 个岗位（分类: {len(set(j['category'] for j in JOBS_KNOWLEDGE_BASE))} 个行业）")


# ─── Prompt 设计 ─────────────────────────────────────────

MATCH_SYSTEM_PROMPT = """你是一位拥有15年跨行业招聘经验的资深综合招聘专家，覆盖技术、财务、制造、运营、设计、销售、教育、法律、医疗等多个行业。你擅长：
- 精准评估候选人与岗位的匹配度，区分行业类型
- 从技能、经验、成长潜力三个维度综合打分
- 识别候选人技能与岗位要求的交集和差距
- 不同行业用不同的核心技能匹配标准

你的评分标准（适用于所有行业）：
- 85~100分：高度匹配，核心技能全覆盖，项目经验直接对应，强烈推荐面试
- 65~84分：较好匹配，核心技能大部分覆盖，稍加学习即可胜任，值得关注
- 40~64分：部分匹配，有一定基础但存在明显技能缺口，可考虑培养
- 40分以下：不推荐，背景与该岗位关联度很低，不做推荐

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  【核心原则 1：行业隔离 —— 优先级最高，必须严格执行】       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

候选人属于哪个行业，就优先推荐哪个行业的岗位。禁止将非技术背景的候选人硬套技术岗位。

**技术岗位**（后端开发、前端开发、移动端、数据开发、AI/算法、运维、测试、DevOps、架构师、安全、嵌入式等）：
- 仅推荐给具有编程/开发/系统相关核心技能的候选人
- 如果候选人简历中完全没有技术技能（如纯会计、纯机械设计、纯市场营销），不要推荐任何技术岗位
- SQL/Excel/Python简单使用不计入"技术开发能力"

**财务/会计岗位**（会计、审计、税务、财务分析、成本会计、出纳）：
- 仅推荐给有财务、会计、审计背景的候选人
- 要求核心技能：会计核算、财务报表、审计实务、税务申报、财务分析等

**机械/制造岗位**（机械设计、汽车零部件、CAE仿真、工艺、质量、电气电子）：
- 仅推荐给有机械、汽车、制造工程背景的候选人
- 要求核心技能：CATIA/SolidWorks/AutoCAD/ANSYS/电路设计等

**运营/营销岗位**（用户运营、新媒体、品牌营销、市场推广）：
- 仅推荐给有运营、营销、内容背景的候选人
- 要求核心技能：用户增长、内容策划、品牌策略、数据分析等

**设计岗位**（UI、UX、平面、工业设计）：
- 仅推荐给有设计背景的候选人
- 要求核心技能：Figma/Photoshop/Illustrator/Rhino等

**其他行业同理**（人力资源、行政、销售、教育、法律、医疗）

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  【核心原则 2：区分"工具使用"与"岗位核心能力"】      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
很多技术岗位会共享相同的工具链（如 Docker、K8s、Linux、Git），但这不意味着候选人的核心能力匹配该岗位。
- 后端开发用 Docker 部署服务 → 工具使用，不是 DevOps/SRE 核心能力
- 运维工程师搭建 CI/CD、管理 K8s 集群、制定 SLO → 这才是 DevOps/SRE 核心能力
- 开发岗接触数据库 → 不是 DBA；简历聚焦数据库架构与优化才算
- 会计用 Excel → 工具使用，不是数据分析师核心能力
- 机械工程师用 Python 做数据处理 → 工具使用，不是软件开发能力

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  【硬性评分上限规则 —— 技术岗位专用】                  ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

【规则 1：核心职责判定】
如果候选人的工作经历和项目描述中，核心职责是「开发/编码/业务系统开发」
而非「运维/部署/监控/基础设施维护」，则以下硬性上限生效：

   岗位类型              | 硬性上限
  ───────────────────────┼──────────
   运维/SRE 工程师        | ≤ 55 分
   DevOps 工程师           | ≤ 55 分
   云原生工程师            | ≤ 50 分
   网络工程师              | ≤ 45 分
   数据库工程师(DBA)       | ≤ 55 分

【规则 2：核心职责判断方法】
看候选人每天 80% 以上的工作时间在做什么。写代码做业务功能是主业 → 算"开发"。
即使用了 Docker/K8s/数据库/网络工具，只要主职是编码，就按开发算。

【规则 3：高分解锁条件】
只有当候选人的工作经历中明确出现以下关键词时，才可给运维/DevOps/云原生岗位超过 65 分：
  - 「负责 CI/CD 流水线建设」或「搭建持续集成/持续部署」
  - 「负责 K8s 集群管理」或「Kubernetes 集群运维」
  - 「负责监控告警体系」或「可观测性平台」
  - 「SRE」或「可用性保障」作为核心职责
  - 「基础设施即代码(IaC)」或「Terraform/Pulumi」
  - 「负责容灾/高可用架构的日常运维」

你必须严格遵守以下规则：
1. 只输出一个合法的 JSON 数组，不要包含任何解释、前言、后缀
2. 不要用 ```json 代码块包裹，直接输出裸 JSON 数组
3. 最少推荐 3 个岗位，最多推荐 8 个，按 score 从高到低排序
4. 如果候选人背景非常单一，推荐数量可以少于 3 个但必须是真正匹配的，不要硬凑
5. matched_skills 必须是从简历中真实匹配到的技能，不要编造
6. missing_skills 是该岗位核心要求但候选人简历中缺失的技能
7. summary 控制在 20 字以内，精准概括匹配理由
8. 评分要有区分度，不要所有岗位都挤在 70-80 分
9. 不允许出现 0 分的推荐项——不匹配的岗位不推荐即可，不要放到结果里"""

# ─── 自主推荐 Prompt（不依赖知识库）────────────────────

CUSTOM_SYSTEM_PROMPT = """你是一位资深综合招聘专家，覆盖所有行业（包括酒店/旅游/餐饮等服务业）。

你的任务是根据候选人背景，推荐最合适的岗位方向。

必须遵守：
1. 使用市场上的真实岗位名称，要具体（如"酒店前厅经理"而不是"服务行业从业者"）
2. 只推荐候选人真正适合的方向，不要硬凑
3. 岗位名称要规范，源自真实招聘市场
4. 输出 JSON 中必须包含 "is_custom": true 这个字段"""


def _parse_json_result(raw: str) -> list[dict[str, Any]]:
    """通用的 AI 返回 JSON 数组解析器"""
    raw = raw.strip()

    strategies = [
        # 策略1：直接解析
        lambda s: json.loads(s),
        # 策略2：去除 markdown 代码块
        lambda s: json.loads(
            re.search(r"```(?:json)?\s*\n?(.*?)\n?```", s, re.DOTALL).group(1).strip()
        ),
        # 策略3：找到第一个 [ 和最后一个 ]
        lambda s: json.loads(s[s.find("[") : s.rfind("]") + 1]),
    ]

    for strategy in strategies:
        try:
            result = strategy(raw)
            if isinstance(result, list):
                valid = [
                    item for item in result
                    if isinstance(item, dict) and isinstance(item.get("score"), (int, float))
                ]
                if valid:
                    return valid
        except (json.JSONDecodeError, AttributeError, IndexError):
            continue

    logger.warning(f"无法解析 JSON，原始文本前300字: {raw[:300]}")
    return []


def build_match_prompt(parsed: dict) -> str:
    """构建匹配打分 prompt"""
    jobs_summary = []
    for job in JOBS_KNOWLEDGE_BASE:
        jobs_summary.append({
            "job_id": job["job_id"],
            "title": job["title"],
            "category": job["category"],
            "core_skills": job["core_skills"],
            "nice_to_have": job["nice_to_have"],
            "description": job["description"],
        })

    jobs_json = json.dumps(jobs_summary, ensure_ascii=False, indent=2)
    resume_json = json.dumps(parsed, ensure_ascii=False, indent=2)

    return f"""请评估以下候选人与 {len(JOBS_KNOWLEDGE_BASE)} 个岗位的匹配度。

【候选人简历】
{resume_json}

【岗位知识库】
{jobs_json}

请从技能匹配度、经验匹配度、成长潜力三个维度综合评估，为每个岗位打分。

返回格式（JSON数组）：
[
  {{
    "job_id": "岗位ID",
    "title": "岗位名称",
    "category": "岗位分类",
    "score": 85,
    "summary": "一句话评语（20字以内）",
    "level_recommendation": "初级/中级/高级",
    "matched_skills": ["匹配的技能"],
    "missing_skills": ["缺失的核心技能"]
  }}
]

记住：
- 只返回真正匹配的岗位（score >= 40），不匹配的不要
- 分数要有区分度，优秀匹配给 85+
- summary 说明匹配亮点或差距"""


def build_custom_prompt(parsed: dict) -> str:
    """构建自主推荐 prompt（不依赖知识库）"""
    return f"""请根据候选人的教育背景、技能、工作经历和项目经验，推荐 2~3 个最合适的岗位方向。

候选人背景：
- 教育：{json.dumps(parsed.get('education', []), ensure_ascii=False)}
- 技能：{json.dumps(parsed.get('skills', []), ensure_ascii=False)}
- 工作经历：{json.dumps(parsed.get('experience', []), ensure_ascii=False)}
- 项目经历：{json.dumps(parsed.get('projects', []), ensure_ascii=False)}

输出 JSON 数组（**必须严格**包含 is_custom 字段，且 is_custom 必须为 true）：
[
  {{
    "job_id": "ai_custom_1",
    "title": "岗位名称（使用市场真实名称，如'酒店前厅经理'、'短视频编导'）",
    "category": "行业分类",
    "score": 0-100的匹配分数,
    "summary": "一句话推荐理由",
    "level_recommendation": "初级/中级/高级",
    "matched_skills": ["从简历中匹配到的适合该岗位的技能"],
    "missing_skills": ["该岗位通常要求但简历缺失的技能"],
    "is_custom": true
  }}
]

**重要：is_custom 必须是 true，不要省略这个字段！**

注意：
- 岗位名称必须使用市场上真实的招聘名称
- 如果候选人背景非常清晰（如就是酒店经理），直接推荐精准岗位
- 分数要有区分度：高度匹配给 85+，一般匹配 65-84
- 如果候选人完全没有该岗位相关背景，不要硬凑"""


# ─── 去重工具 ────────────────────────────────────────────


def _same_direction(title1: str, title2: str) -> bool:
    """判断两个岗位名称是否属于同一方向。

    规则：
    1. 完全相同 → 同方向
    2. 共享技术栈关键词（Go/Java/Python 等）→ 同方向
    3. 双方都有技术栈但不共享 → 不同方向（如 Go后端 vs Java后端）
    4. 至少一方无技术栈 → 比对归一化中文
    """
    t1, t2 = title1.lower().strip(), title2.lower().strip()
    if t1 == t2:
        return True

    tech1 = set(re.findall(r'[a-z+#]+', t1))
    tech2 = set(re.findall(r'[a-z+#]+', t2))

    # 共享技术栈 → 同方向
    if tech1 and tech2 and (tech1 & tech2):
        return True

    # 双方都有技术栈但不重叠 → 不同方向（Go ≠ Java）
    if tech1 and tech2:
        return False

    # 至少一方无技术栈 → 比对归一化中文部分
    def _norm_cn(t: str) -> str:
        t = re.sub(r'^(高级|资深|初级|助理|见习)\s*', '', t)
        t = re.sub(r'[a-z+#\d\s]+', '', t)  # 去掉英文/数字/空格
        for w in ['开发工程师', '工程师', '技术专家', '经理',
                   '设计师', '专员', '顾问', '代表', '分析师']:
            t = t.replace(w, '')
        return t.strip()

    n1, n2 = _norm_cn(t1), _norm_cn(t2)
    return bool(n1 and n2 and n1 == n2)


def _deduplicate_matches(matches: list[dict]) -> list[dict]:
    """同一方向只保留最优项：KB 优先，同类型取分数高者。"""
    if len(matches) <= 1:
        return matches

    # KB 排前（is_custom=False=0 < True=1），同类型分数高者排前
    matches = sorted(
        matches,
        key=lambda x: (bool(x.get("is_custom")), -x.get("score", 0)),
    )

    deduped: list[dict] = []
    for m in matches:
        is_dup = False
        for existing in deduped:
            if _same_direction(m.get("title", ""), existing.get("title", "")):
                if m.get("is_custom") and not existing.get("is_custom"):
                    logger.info(
                        f"去重: AI推荐'{m['title']}'({m['score']}分) 与 "
                        f"知识库'{existing['title']}'({existing['score']}分)同方向, 删除AI推荐"
                    )
                else:
                    logger.info(
                        f"去重: '{m['title']}'({m['score']}分) 与 "
                        f"'{existing['title']}'({existing['score']}分)同方向, 保留分高者"
                    )
                is_dup = True
                break
        if not is_dup:
            deduped.append(m)

    return deduped


class JobMatcher:
    """岗位匹配器"""

    def match(self, parsed_resume: dict) -> list[dict[str, Any]]:
        """
        两步式岗位匹配：知识库匹配 + 自主推荐

        Args:
            parsed_resume: AI 解析后的结构化简历数据

        Returns:
            推荐的岗位列表，按分数降序，最多 8 个
        """
        # ── 第一步：知识库匹配 ──────────────────────────
        kb_matches = self._kb_match(parsed_resume)

        # ── 第二步：自主推荐 ─────────────────────────
        custom_matches = self._autonomous_recommend(parsed_resume)

        # ── 合并 + 去重 ──────────────────────────────
        all_matches = _deduplicate_matches(kb_matches + custom_matches)
        all_matches.sort(key=lambda x: x.get("score", 0), reverse=True)
        all_matches = all_matches[:8]

        # DEBUG：确认 is_custom 字段
        for m in all_matches:
            if m.get("is_custom"):
                print(f"[DEBUG] 合并结果中包含 AI推荐: {m['title']} ({m['score']}分) is_custom={m.get('is_custom')}")

        logger.info(
            f"岗位匹配完成: {len(kb_matches)}个知识库 + {len(custom_matches)}个自主推荐 "
            f"→ 去重后 {len(all_matches)}个"
        )
        return all_matches

    def _kb_match(self, parsed_resume: dict) -> list[dict[str, Any]]:
        """第一步：知识库匹配"""
        start_time = time.time()
        user_prompt = build_match_prompt(parsed_resume)

        raw_output = call_deepseek(
            system_prompt=MATCH_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=0.2,
            max_tokens=4096,
            label="知识库匹配",
        )

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"知识库匹配返回: 长度={len(raw_output)} 字符, 耗时={elapsed_ms}ms, "
            f"预览=\n{raw_output[:300]}"
        )

        matches = _parse_json_result(raw_output)
        for m in matches:
            m.setdefault("is_custom", False)

        return matches

    def _autonomous_recommend(self, parsed_resume: dict) -> list[dict[str, Any]]:
        """第二步：不依赖知识库，AI 自主推荐岗位方向"""
        start_time = time.time()
        user_prompt = build_custom_prompt(parsed_resume)

        try:
            raw_output = call_deepseek(
                system_prompt=CUSTOM_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                temperature=0.3,
                max_tokens=2048,
                label="自主推荐",
            )
        except RuntimeError as e:
            logger.warning(f"自主推荐调用失败: {e}，跳过")
            return []

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"自主推荐返回: 长度={len(raw_output)} 字符, 耗时={elapsed_ms}ms, "
            f"预览=\n{raw_output[:300]}"
        )

        matches = _parse_json_result(raw_output)
        for i, m in enumerate(matches):
            # 统一设置 job_id 和 is_custom（强制覆盖，以防 AI 没写）
            m["is_custom"] = True
            if not m.get("job_id") or "ai_custom" not in str(m.get("job_id", "")):
                m["job_id"] = f"ai_custom_{i + 1}"

        # DEBUG 日志：打印自主推荐结果
        print(f"[DEBUG] autonomous_recommend 返回了 {len(matches)} 个结果: {matches}")
        logger.info(f"[DEBUG] autonomous_recommend 返回了 {len(matches)} 个结果")

        return matches


# 全局单例
matcher = JobMatcher()
