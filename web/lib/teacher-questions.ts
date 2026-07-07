/**
 * 教師題庫檢視 API wrapper（5-6c）— 對應後端 GET /quiz/bank（含正解 + 解析）。
 */

import { api } from "./api";

export interface TeacherQuestion {
  id: string;
  type: string;
  bloom_level: number;
  difficulty: number;
  content: {
    stem?: string;
    options?: string[];
    answer_index?: number;
    starter_code?: string;
    [k: string]: unknown;
  };
  explanation: string;
}

/** 取得某 concept 的題庫題目（僅教師；含正解與解析）。 */
export function listTeacherQuestions(tag: string): Promise<TeacherQuestion[]> {
  return api<{ questions: TeacherQuestion[] }>(
    `/quiz/bank?tag=${encodeURIComponent(tag)}`,
  ).then((r) => r.questions);
}
