/**
 * Dashboard types + API helper（roadmap 3-3a）。
 *
 * 對應後端 `/dashboard/stats`；schema 與 `backend/api/routes/dashboard.py` 一致。
 */

import { api } from "./api";

export interface PathProgress {
  path_id: string;
  title: string;
  total_units: number;
  completed_units: number;
  percent: number;
}

export interface WeekQuiz {
  total_attempts: number;
  correct_count: number;
  accuracy_percent: number;
}

export interface MasteryOverview {
  total_concepts: number;
  started_count: number;
  mastered_count: number;
}

export interface TodaySuggestion {
  title: string;
  description: string;
  link: string;
  next_concept_name: string | null;
}

export interface DashboardStats {
  path_progress: PathProgress | null;
  week_quiz: WeekQuiz;
  mastery: MasteryOverview;
  reflection_count: number;
  today_suggestion: TodaySuggestion;
}

export async function getDashboardStats(): Promise<DashboardStats> {
  return api<DashboardStats>("/dashboard/stats");
}

// === 3-3b 活動時間線 ===

export type ActivityType = "quiz" | "reflection" | "unit_completed";

export interface ActivityItem {
  type: ActivityType;
  timestamp: string;  // ISO
  title: string;
  detail: string;
  link: string | null;
  is_correct: boolean | null;
}

export async function getRecentActivities(
  limit: number = 30,
): Promise<ActivityItem[]> {
  const data = await api<{ items: ActivityItem[] }>(
    `/dashboard/timeline?limit=${limit}`,
  );
  return data.items;
}

// === 3-3c 精熟度詳細總覽 ===

export interface ConceptMasteryDetail {
  concept_tag: string;
  concept_name_zh: string;
  video_order: number | null;
  difficulty: number;
  /** 0.0-1.0；未練 = 0 */
  confidence: number;
}

export interface CategoryBreakdown {
  name: string;
  total: number;
  started: number;
  mastered: number;
  concepts: ConceptMasteryDetail[];
}

export interface MasteryOverviewData {
  categories: CategoryBreakdown[];
}

export async function getMasteryOverview(): Promise<MasteryOverviewData> {
  return api<MasteryOverviewData>("/dashboard/mastery-overview");
}
