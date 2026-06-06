/**
 * 分析结果展示
 * 主体：岗位推荐卡片列表
 * 底部：简历解析详情（可折叠）
 */
import { useState } from "react";
import type { AnalysisResponse, JobMatch } from "../types/resume";
import JobCard from "./JobCard";
import JobDetail from "./JobDetail";

interface ResultCardProps {
  result: AnalysisResponse;
  resumeText: string;
  onReset: () => void;
}

export default function ResultCard({ result, resumeText, onReset }: ResultCardProps) {
  const [showDetail, setShowDetail] = useState(false);
  const [selectedJob, setSelectedJob] = useState<JobMatch | null>(null);
  const { parse_result, job_matches, processing_time_ms, model_used } = result;
  const p = parse_result;

  const handleExport = () => {
    const name = p.name || "未知";
    const prevTitle = document.title;
    document.title = `${name}_简历分析报告`;

    // 先展开折叠区，用 rAF 双缓冲保证 React 渲染完成后再打印
    setShowDetail(true);
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        window.print();
        // 打印完成后恢复原标题
        window.addEventListener("afterprint", () => {
          document.title = prevTitle;
        }, { once: true });
      });
    });
  };

  const today = new Date().toISOString().slice(0, 10); // 如 2026-06-05

  return (
    <div className="result-container" data-date={today}>
      {/* ── 头部 ──────────────────────────── */}
      <div className="result-header">
        <h2>🎯 分析完成</h2>
        <div className="result-meta">
          <span>姓名: {p.name || "未知"}</span>
          {p.summary && <span>📝 {p.summary}</span>}
          <span>耗时: {(processing_time_ms / 1000).toFixed(1)}s</span>
          <span>模型: {model_used}</span>
        </div>
      </div>

      {/* ── 岗位推荐（主体） ──────────────── */}
      <section className="result-section">
        <div className="section-header-row">
          <h3>
            推荐岗位 ({job_matches.length})
            {job_matches.length > 0 && (
              <span className="section-hint"> — 点击卡片查看详情分析</span>
            )}
          </h3>
          {job_matches.length > 0 && (
            <button className="btn-export" onClick={handleExport}>
              📄 导出报告
            </button>
          )}
        </div>

        {job_matches.length === 0 ? (
          <div className="empty-state">
            <p>😕 岗位匹配未生成，可能是 AI 服务暂时异常。</p>
            <p className="empty-hint">请检查后端日志或稍后重试。</p>
          </div>
        ) : (
          <div className="job-cards-grid">
            {job_matches.map((job, i) => (
              <JobCard key={job.job_id} job={job} rank={i + 1} onClick={() => setSelectedJob(job)} />
            ))}
          </div>
        )}
      </section>

      {/* ── 简历解析详情（可折叠） ─────────── */}
      <div className="detail-toggle no-print" onClick={() => setShowDetail(!showDetail)}>
        <span>{showDetail ? "🔽 收起" : "📋 展开"} 简历解析详情</span>
      </div>

      <div className={showDetail ? "" : "collapsible-hidden"}>
          {/* 基本信息 */}
          <section className="result-section">
            <h3>👤 基本信息</h3>
            <div className="basic-info">
              {p.name && (
                <div className="info-item name-item">
                  <span className="info-label">姓名</span>
                  <span className="info-value name-value">{p.name}</span>
                </div>
              )}
              <ContactDisplay contact={p.contact} />
            </div>
          </section>

          {/* 技能标签 */}
          {p.skills.length > 0 && (
            <section className="result-section">
              <h3>🛠 技能标签 ({p.skills.length})</h3>
              <div className="skills-cloud">
                {p.skills.map((skill, i) => (
                  <span key={i} className="skill-tag">{skill}</span>
                ))}
              </div>
            </section>
          )}

          {/* 工作经历 */}
          {p.experience.length > 0 && (
            <section className="result-section">
              <h3>💼 工作经历</h3>
              <div className="timeline">
                {p.experience.map((exp, i) => (
                  <div key={i} className="timeline-item">
                    <div className="timeline-dot" />
                    <div className="timeline-content">
                      <div className="exp-header">
                        <span className="exp-company">{exp.company}</span>
                        <span className="exp-role">{exp.role}</span>
                        <span className="exp-date">{exp.start_date} ~ {exp.end_date}</span>
                      </div>
                      {exp.highlights.length > 0 && (
                        <ul className="highlights-list">
                          {exp.highlights.map((h, j) => <li key={j}>{h}</li>)}
                        </ul>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* 项目经历 */}
          {p.projects.length > 0 && (
            <section className="result-section">
              <h3>🚀 项目经历</h3>
              <div className="projects-grid">
                {p.projects.map((proj, i) => (
                  <div key={i} className="project-card">
                    <div className="project-header">
                      <span className="project-name">{proj.name}</span>
                      {proj.role && <span className="project-role">{proj.role}</span>}
                    </div>
                    {proj.description && <p className="project-desc">{proj.description}</p>}
                    {proj.tech_stack.length > 0 && (
                      <div className="project-tech">
                        {proj.tech_stack.map((tech, j) => (
                          <span key={j} className="tech-tag">{tech}</span>
                        ))}
                      </div>
                    )}
                    {proj.highlights.length > 0 && (
                      <ul className="highlights-list">
                        {proj.highlights.map((h, j) => <li key={j}>{h}</li>)}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* 教育经历 */}
          {p.education.length > 0 && (
            <section className="result-section">
              <h3>🎓 教育经历</h3>
              <div className="education-list">
                {p.education.map((edu, i) => (
                  <div key={i} className="edu-item">
                    <span className="edu-school">{edu.school}</span>
                    <span className="edu-info">
                      {edu.degree} · {edu.major}
                      {(edu.start_year || edu.end_year) && <> · {edu.start_year} ~ {edu.end_year}</>}
                    </span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {/* 证书 */}
          {p.certifications.length > 0 && (
            <section className="result-section">
              <h3>📜 证书 / 资质</h3>
              <div className="cert-list">
                {p.certifications.map((cert, i) => (
                  <span key={i} className="cert-badge">{cert}</span>
                ))}
              </div>
            </section>
          )}
      </div>

      {/* ── 底部操作 ──────────────────────── */}
      <div className="result-actions">
        <button onClick={onReset} className="btn-outline">
          🔄 分析新的简历
        </button>
      </div>

      {/* ── 岗位详情 Modal ──────────────────── */}
      {selectedJob && (
        <JobDetail
          job={selectedJob}
          resumeText={resumeText}
          parsedResume={p}
          onClose={() => setSelectedJob(null)}
        />
      )}
    </div>
  );
}

/** 联系方式子组件 */
function ContactDisplay({ contact }: { contact: AnalysisResponse["parse_result"]["contact"] }) {
  const items = [
    { label: "📞", value: contact.phone },
    { label: "📧", value: contact.email },
    { label: "💬", value: contact.wechat },
    { label: "🔗", value: contact.other },
  ].filter((item) => item.value);

  if (items.length === 0) return null;

  return (
    <div className="contact-list">
      {items.map((item, i) => (
        <div key={i} className="contact-item">
          <span className="contact-icon">{item.label}</span>
          <span className="contact-value">{item.value}</span>
        </div>
      ))}
    </div>
  );
}
