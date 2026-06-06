/**
 * API 调用层
 */
import type { AnalysisResponse, AnalyzeDetailResponse } from "../types/resume";

const API_BASE = "http://localhost:8010/api";

/** 提交简历文本 */
export async function submitResumeText(content: string): Promise<AnalysisResponse> {
  const form = new FormData();
  form.append("content", content);
  return _post("/resume/submit", form);
}

/** 上传简历文件 */
export async function submitResumeFile(file: File): Promise<AnalysisResponse> {
  const form = new FormData();
  form.append("file", file);
  return _post("/resume/submit", form);
}

async function _post(path: string, body: FormData): Promise<AnalysisResponse> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    body,
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    const detail = err.detail;
    const msg = typeof detail === "object" && detail ? detail.message || JSON.stringify(detail) : detail || `请求失败 (${response.status})`;
    throw new Error(msg);
  }
  return response.json();
}

/** 岗位详情分析 */
export async function analyzeJobDetail(params: {
  resume_text: string; parsed_resume: Record<string, unknown>;
  job_id: string; job_title: string; job_category: string;
  job_score: number; job_matched_skills: string[]; job_missing_skills: string[];
}): Promise<AnalyzeDetailResponse> {
  const r = await fetch(`${API_BASE}/resume/analyze-detail`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    const detail = err.detail;
    throw new Error(typeof detail === "object" && detail ? detail.message || JSON.stringify(detail) : `请求失败 (${r.status})`);
  }
  return r.json();
}

// ─── 历史记录 ──────────────────────────────

export interface HistoryItem {
  id: number; task_id: string; candidate_name: string;
  summary_text: string; job_count: number; created_at: string;
}

export interface HistoryDetail extends HistoryItem {
  parse_result: AnalysisResponse["parse_result"];
  job_matches: AnalysisResponse["job_matches"];
  original_text: string;
}

export async function getHistoryList(): Promise<HistoryItem[]> {
  const r = await fetch(`${API_BASE}/resume/history`);
  return r.json();
}

export async function getHistoryDetail(id: number): Promise<HistoryDetail> {
  const r = await fetch(`${API_BASE}/resume/history/${id}`);
  if (!r.ok) throw new Error("记录不存在");
  return r.json();
}

export async function deleteHistory(id: number): Promise<void> {
  await fetch(`${API_BASE}/resume/history/${id}`, { method: "DELETE" });
}

export async function healthCheck(): Promise<{ status: string; version: string }> {
  const r = await fetch(`${API_BASE}/health`);
  return r.json();
}
