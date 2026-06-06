/**
 * 简历分析相关 TypeScript 类型定义
 */

/** 联系方式 */
export interface ContactInfo {
  phone: string;
  email: string;
  wechat: string;
  other: string;
}

/** 教育经历 */
export interface EducationItem {
  school: string;
  degree: string;
  major: string;
  start_year: string;
  end_year: string;
}

/** 工作经历 */
export interface ExperienceItem {
  company: string;
  role: string;
  start_date: string;
  end_date: string;
  highlights: string[];
}

/** 项目经历 */
export interface ProjectItem {
  name: string;
  role: string;
  description: string;
  tech_stack: string[];
  highlights: string[];
}

/** AI 解析的结构化简历 */
export interface ParsedResume {
  name: string;
  contact: ContactInfo;
  education: EducationItem[];
  skills: string[];
  experience: ExperienceItem[];
  projects: ProjectItem[];
  certifications: string[];
  summary: string;
}

/** 岗位匹配推荐 */
export interface JobMatch {
  job_id: string;
  title: string;
  category: string;
  score: number;
  summary: string;
  level_recommendation: string;
  matched_skills: string[];
  missing_skills: string[];
  is_custom?: boolean;
}

/** 简历分析完整响应 */
export interface AnalysisResponse {
  id: string;
  status: string;
  parse_result: ParsedResume;
  job_matches: JobMatch[];
  processing_time_ms: number;
  model_used: string;
  created_at: string;
}

// ─── 详情分析类型 ─────────────────────────────────

export interface StrengthPoint {
  point: string;
  evidence: string;
  impact: string;
}

export interface WeaknessPoint {
  point: string;
  evidence: string;
  severity: "高" | "中" | "低";
}

export interface KeywordAnalysis {
  matched: string[];
  missing: string[];
  suggestion: string;
}

export interface JobAnalysis {
  strengths: StrengthPoint[];
  weaknesses: WeaknessPoint[];
  keyword_analysis: KeywordAnalysis;
  experience_assessment: string;
  overall: string;
}

export interface RewriteSuggestion {
  original: string;
  improved: string;
  reason: string;
  where: string;
}

export interface MissingItem {
  item: string;
  where: string;
  example: string;
}

export interface InterviewQuestion {
  question: string;
  reason: string;
  suggestion: string;
}

export interface KeywordOptimization {
  add_keywords: string[];
  placement: string;
}

export interface OptimizationAdvice {
  rewrite_suggestions: RewriteSuggestion[];
  missing_items: MissingItem[];
  structure_suggestions: string[];
  interview_questions: InterviewQuestion[];
  keyword_optimization: KeywordOptimization;
}

export interface AnalyzeDetailResponse {
  job_id: string;
  job_title: string;
  analysis: JobAnalysis;
  optimization: OptimizationAdvice;
  processing_time_ms: number;
}
