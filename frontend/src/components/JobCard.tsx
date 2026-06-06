/**
 * 岗位推荐卡片
 * 展示匹配分数、技能对比、一句话评语
 */
import type { JobMatch } from "../types/resume";

interface JobCardProps {
  job: JobMatch;
  rank: number;
  onClick: () => void;
}

/** 根据分数返回颜色 */
function scoreColor(score: number): string {
  if (score >= 80) return "score-green";
  if (score >= 60) return "score-blue";
  return "score-orange";
}

function scoreLabel(score: number): string {
  if (score >= 85) return "强烈推荐";
  if (score >= 70) return "推荐";
  if (score >= 55) return "可考虑";
  return "待观察";
}

export default function JobCard({ job, rank, onClick }: JobCardProps) {
  return (
    <div className="job-card" onClick={onClick} style={{ cursor: "pointer" }}>
      {/* 排名角标 */}
      <span className="job-rank">#{rank}</span>

      {/* 分数区 */}
      <div className="job-score-area">
        <div className={`job-score-ring ${scoreColor(job.score)}`}>
          <span className="job-score-num">{job.score}</span>
          <span className="job-score-unit">分</span>
        </div>
        <span className={`job-score-label ${scoreColor(job.score)}`}>
          {scoreLabel(job.score)}
        </span>
      </div>

      {/* 信息区 */}
      <div className="job-info">
        <div className="job-header">
          <h3 className="job-title">{job.title}</h3>
          <div className="job-tags">
            {job.is_custom && <span className="job-custom-badge">AI推荐</span>}
            <span className="job-category">{job.category}</span>
            <span className="job-level">{job.level_recommendation}</span>
          </div>
        </div>

        <p className="job-summary">{job.summary}</p>

        {/* 技能对比 */}
        <div className="job-skills">
          {job.matched_skills.length > 0 && (
            <div className="skill-row">
              <span className="skill-label matched-label">已匹配</span>
              <div className="skill-tags">
                {job.matched_skills.map((s, i) => (
                  <span key={i} className="skill-tag-small matched">{s}</span>
                ))}
              </div>
            </div>
          )}
          {job.missing_skills.length > 0 && (
            <div className="skill-row">
              <span className="skill-label missing-label">待补充</span>
              <div className="skill-tags">
                {job.missing_skills.map((s, i) => (
                  <span key={i} className="skill-tag-small missing">{s}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
