/**
 * 岗位详情 Modal
 * Tab 1: 深度分析（优势/短板/关键词/STAR/综合评价）
 * Tab 2: 优化建议（改写/补充/面试/关键词优化）
 *
 * 内置结果缓存：同一 job_id 的分析结果只请求一次，
 * 关闭 Modal 后再次点击同一卡片秒开。
 */
import { useState, useEffect } from "react";
import type { JobMatch, ParsedResume, AnalyzeDetailResponse } from "../types/resume";
import { analyzeJobDetail } from "../services/api";

// ── 分析结果缓存（模块级，跨 Modal 开关持久化）─────────
const detailCache = new Map<string, AnalyzeDetailResponse>();

/** 清空所有缓存的详情分析结果（切换简历时调用） */
export function clearJobDetailCache() {
  detailCache.clear();
}

interface Props {
  job: JobMatch;
  resumeText: string;
  parsedResume: ParsedResume;
  onClose: () => void;
}

type Tab = "analysis" | "optimization";

export default function JobDetail({ job, resumeText, parsedResume, onClose }: Props) {
  const [tab, setTab] = useState<Tab>("analysis");
  const [data, setData] = useState<AnalyzeDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    // 1. 先查缓存
    const cached = detailCache.get(job.job_id);
    if (cached) {
      setData(cached);
      setLoading(false);
      setError(null);
      return;
    }

    // 2. 缓存未命中，调接口
    setLoading(true);
    setError(null);

    analyzeJobDetail({
      resume_text: resumeText,
      parsed_resume: parsedResume as unknown as Record<string, unknown>,
      job_id: job.job_id,
      job_title: job.title,
      job_category: job.category,
      job_score: job.score,
      job_matched_skills: job.matched_skills,
      job_missing_skills: job.missing_skills,
    })
      .then((res) => {
        if (!cancelled) {
          detailCache.set(job.job_id, res);  // 3. 写入缓存
          setData(res);
        }
      })
      .catch((e) => { if (!cancelled) setError(e instanceof Error ? e.message : "加载失败"); })
      .finally(() => { if (!cancelled) setLoading(false); });

    return () => { cancelled = true; };
  }, [job.job_id]);

  const scoreColor = job.score >= 80 ? "s-green" : job.score >= 60 ? "s-blue" : "s-orange";

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-container" onClick={(e) => e.stopPropagation()}>
        {/* 头部 */}
        <div className="modal-header">
          <button className="modal-back" onClick={onClose}>← 返回</button>
          <div className="modal-title-row">
            <h2>{job.title}</h2>
            <span className={`modal-score ${scoreColor}`}>{job.score}分</span>
            <span className="modal-level">{job.level_recommendation}</span>
          </div>
          <p className="modal-category">{job.category} · {job.summary}</p>
        </div>

        {/* Tab 切换 */}
        <div className="modal-tabs">
          <button className={`tab-btn ${tab === "analysis" ? "active" : ""}`} onClick={() => setTab("analysis")}>
            🔍 深度分析
          </button>
          <button className={`tab-btn ${tab === "optimization" ? "active" : ""}`} onClick={() => setTab("optimization")}>
            ✏️ 优化建议
          </button>
        </div>

        {/* 内容区 */}
        <div className="modal-body">
          {loading && (
            <div className="modal-loading">
              <div className="spinner" />
              <p>AI 正在分析中，预计 5~10 秒...</p>
            </div>
          )}

          {error && (
            <div className="modal-error">
              <p>❌ {error}</p>
              <button onClick={onClose}>关闭</button>
            </div>
          )}

          {data && tab === "analysis" && <AnalysisTab data={data} />}
          {data && tab === "optimization" && <OptimizationTab data={data} />}
        </div>

        {/* 底部 */}
        {data && (
          <div className="modal-footer">
            处理耗时: {(data.processing_time_ms / 1000).toFixed(1)}s
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Tab 1：深度分析 ─────────────────────────────────

function AnalysisTab({ data }: { data: AnalyzeDetailResponse }) {
  const a = data.analysis;
  return (
    <div className="analysis-tab">
      {/* 优势 */}
      <section className="detail-section">
        <h3>✅ 核心优势 ({a.strengths.length})</h3>
        {a.strengths.map((s, i) => (
          <div key={i} className="strength-card">
            <div className="strength-point">{s.point}</div>
            <div className="strength-evidence">📎 证据: {s.evidence}</div>
            <div className="strength-impact">💡 价值: {s.impact}</div>
          </div>
        ))}
      </section>

      {/* 短板 */}
      <section className="detail-section">
        <h3>⚠️ 能力短板 ({a.weaknesses.length})</h3>
        {a.weaknesses.map((w, i) => (
          <div key={i} className={`weakness-card sev-${w.severity}`}>
            <div className="weakness-header">
              <span className="weakness-point">{w.point}</span>
              <span className={`severity-badge sev-${w.severity}`}>{w.severity}</span>
            </div>
            <div className="weakness-evidence">{w.evidence}</div>
          </div>
        ))}
      </section>

      {/* 关键词分析 */}
      {a.keyword_analysis && (
        <section className="detail-section">
          <h3>🔑 关键词匹配</h3>
          <div className="kw-compare">
            <div className="kw-col matched-col">
              <div className="kw-col-title">已匹配</div>
              {(a.keyword_analysis.matched || []).map((k, i) => (
                <span key={i} className="kw-tag matched">{k}</span>
              ))}
            </div>
            <div className="kw-divider" />
            <div className="kw-col missing-col">
              <div className="kw-col-title">待补充</div>
              {(a.keyword_analysis.missing || []).map((k, i) => (
                <span key={i} className="kw-tag missing">{k}</span>
              ))}
            </div>
          </div>
          {a.keyword_analysis.suggestion && (
            <p className="kw-suggestion">💬 {a.keyword_analysis.suggestion}</p>
          )}
        </section>
      )}

      {/* STAR 评估 */}
      {a.experience_assessment && (
        <section className="detail-section">
          <h3>⭐ STAR 法则评估</h3>
          <p className="star-text">{a.experience_assessment}</p>
        </section>
      )}

      {/* 综合评价 */}
      {a.overall && (
        <section className="detail-section overall-section">
          <h3>📊 综合评价</h3>
          <p className="overall-text">{a.overall}</p>
        </section>
      )}
    </div>
  );
}

// ─── Tab 2：优化建议 ─────────────────────────────────

function OptimizationTab({ data }: { data: AnalyzeDetailResponse }) {
  const o = data.optimization;

  return (
    <div className="optimization-tab">
      {/* 改写建议 */}
      {o.rewrite_suggestions.length > 0 && (
        <section className="detail-section">
          <h3>📝 改写建议</h3>
          {o.rewrite_suggestions.map((r, i) => (
            <div key={i} className="rewrite-card">
              <div className="rewrite-where">{r.where}</div>
              <div className="rewrite-compare">
                <div className="rewrite-original">
                  <span className="rewrite-label">原文</span>
                  <p>{r.original}</p>
                </div>
                <span className="rewrite-arrow">→</span>
                <div className="rewrite-improved">
                  <span className="rewrite-label">优化</span>
                  <p>{r.improved}</p>
                </div>
              </div>
              <div className="rewrite-reason">💡 {r.reason}</div>
            </div>
          ))}
        </section>
      )}

      {/* 补充项 */}
      {o.missing_items.length > 0 && (
        <section className="detail-section">
          <h3>➕ 建议补充</h3>
          {o.missing_items.map((m, i) => (
            <div key={i} className="missing-card">
              <div className="missing-item">{m.item}</div>
              <div className="missing-where">📍 位置: {m.where}</div>
              <div className="missing-example">📎 示例: {m.example}</div>
            </div>
          ))}
        </section>
      )}

      {/* 结构建议 */}
      {o.structure_suggestions.length > 0 && (
        <section className="detail-section">
          <h3>🏗 结构建议</h3>
          <ul className="structure-list">
            {o.structure_suggestions.map((s, i) => <li key={i}>{s}</li>)}
          </ul>
        </section>
      )}

      {/* 面试问题 */}
      {o.interview_questions.length > 0 && (
        <section className="detail-section">
          <h3>🎤 面试准备 ({o.interview_questions.length})</h3>
          {o.interview_questions.map((q, i) => (
            <InterviewCard key={i} question={q} index={i} />
          ))}
        </section>
      )}

      {/* 关键词优化 */}
      {o.keyword_optimization && (
        <section className="detail-section">
          <h3>🏷 关键词优化</h3>
          <div className="kw-opt-tags">
            {(o.keyword_optimization.add_keywords || []).map((k, i) => (
              <span key={i} className="kw-opt-tag">{k}</span>
            ))}
          </div>
          {o.keyword_optimization.placement && (
            <p className="kw-opt-placement">📍 {o.keyword_optimization.placement}</p>
          )}
        </section>
      )}
    </div>
  );
}

// ─── 面试问题卡片（折叠/展开） ────────────────────────

function InterviewCard({ question, index }: { question: { question: string; reason: string; suggestion: string }; index: number }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="interview-card" onClick={() => setOpen(!open)}>
      <div className="interview-q">
        <span className="q-num">Q{index + 1}</span>
        <span className="q-text">{question.question}</span>
        <span className="q-toggle">{open ? "▾" : "▸"}</span>
      </div>
      {open && (
        <div className="interview-a">
          <div className="qa-row"><span className="qa-label">为什么问:</span> {question.reason}</div>
          <div className="qa-row"><span className="qa-label">建议方向:</span> {question.suggestion}</div>
        </div>
      )}
    </div>
  );
}
