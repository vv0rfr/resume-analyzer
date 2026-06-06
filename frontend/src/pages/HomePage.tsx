/**
 * 首页——简历智能分析工具
 */
import { useState, useEffect, useCallback } from "react";
import ResumeInput from "../components/ResumeInput";
import ResultCard from "../components/ResultCard";
import HistoryList from "../components/HistoryList";
import { clearJobDetailCache } from "../components/JobDetail";
import { submitResumeText, submitResumeFile, getHistoryList } from "../services/api";
import type { AnalysisResponse, ParsedResume, JobMatch } from "../types/resume";
import type { HistoryDetail } from "../services/api";

type Stage = "idle" | "parsing" | "matching" | "done";
type View = "input" | "result" | "history" | "history-detail";

export default function HomePage() {
  const [result, setResult] = useState<AnalysisResponse | null>(null);
  const [resumeText, setResumeText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [stage, setStage] = useState<Stage>("idle");
  const [error, setError] = useState<string | null>(null);
  const [view, setView] = useState<View>("input");
  const [historyCount, setHistoryCount] = useState(0);

  // 加载历史记录数量
  useEffect(() => {
    getHistoryList().then(list => setHistoryCount(list.length)).catch(() => {});
  }, [result]);

  const handleSubmit = async (content: string, file?: File) => {
    setIsLoading(true);
    setError(null);
    setResumeText(content);
    setStage("parsing");

    try {
      const response = file
        ? await submitResumeFile(file)
        : await submitResumeText(content);

      setStage("done");
      setResult(response);
      setView("result");
    } catch (err) {
      setError(err instanceof Error ? err.message : "分析服务暂时不可用，请稍后重试");
      setStage("idle");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setResult(null);
    setResumeText("");
    setError(null);
    setStage("idle");
    setView("input");
    clearJobDetailCache();
  };

  const handleViewHistory = () => setView("history");
  const handleBackToInput = () => {
    setResult(null);
    setError(null);
    setView("input");
    clearJobDetailCache();
  };
  const handleHistorySelect = useCallback((detail: HistoryDetail) => {
    setResult({
      id: detail.task_id,
      status: "completed",
      parse_result: detail.parse_result as ParsedResume,
      job_matches: detail.job_matches as JobMatch[],
      processing_time_ms: 0,
      model_used: "",
      created_at: detail.created_at,
    });
    setResumeText(detail.original_text || "");
    setView("result");
  }, []);

  const stageLabels: Record<Stage, string> = {
    idle: "",
    parsing: "正在解析简历结构...",
    matching: "正在匹配推荐岗位...",
    done: "",
  };

  return (
    <div className="home-page">
      <header>
        <h1>🎯 简历智能分析</h1>
        <p>粘贴或上传简历，AI 自动解析、推荐岗位、给出优化建议</p>
        <nav className="top-nav">
          <button className={`nav-btn ${view === "input" ? "active" : ""}`} onClick={handleBackToInput}>
            📝 分析
          </button>
          <button className={`nav-btn ${view === "history" ? "active" : ""}`} onClick={handleViewHistory}>
            📋 历史 {historyCount > 0 && <span className="nav-badge">{historyCount}</span>}
          </button>
        </nav>
      </header>

      <main>
        {/* 错误提示 */}
        {error && (
          <div className="error-banner">
            <div className="error-content"><span className="error-icon">❌</span><span>{error}</span></div>
            <button onClick={() => setError(null)} className="error-dismiss">✕</button>
          </div>
        )}

        {/* Loading 进度 */}
        {isLoading && (
          <div className="progress-bar-container">
            <div className="progress-bar">
              <div className={`progress-fill ${stage === "parsing" ? "p50" : stage === "matching" ? "p80" : ""}`} />
            </div>
            <p className="progress-label">{stageLabels[stage]}</p>
          </div>
        )}

        {/* 主内容区 */}
        {view === "history" && (
          <HistoryList onSelect={handleHistorySelect} onBack={handleBackToInput} />
        )}

        {view === "input" && !result && (
          <ResumeInput onSubmit={handleSubmit} isLoading={isLoading} />
        )}

        {view === "result" && result && (
          <ResultCard result={result} resumeText={resumeText} onReset={handleReset} />
        )}

        {/* 空状态欢迎引导 */}
        {view === "input" && !result && !isLoading && (
          <div className="welcome-guide">
            <div className="welcome-steps">
              <div className="welcome-step"><span>1</span> 粘贴或上传简历</div>
              <div className="welcome-step"><span>2</span> AI 解析简历结构</div>
              <div className="welcome-step"><span>3</span> 推荐匹配岗位</div>
              <div className="welcome-step"><span>4</span> 查看深度分析</div>
            </div>
          </div>
        )}
      </main>

      <footer>
        <p>简历智能分析工具 v0.2.0 | React + FastAPI + DeepSeek</p>
      </footer>
    </div>
  );
}
