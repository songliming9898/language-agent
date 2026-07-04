/** API 请求封装 */

const BASE = "/api";

async function request<T = any>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const json = await res.json();
  if (json.code !== 0) {
    throw new Error(json.message || "Request failed");
  }
  return json.data;
}

// ====== 课程 ======

export interface Course {
  id: number;
  grade: string;
  semester: string;
  version: string;
}

export interface Unit {
  id: number;
  unit_name: string;
  unit_order: number;
  description: string;
}

export interface Sentence {
  id: number;
  sentence_text: string;
  sentence_order: number;
  translation: string;
  difficulty: string;
}

export async function getCourses(): Promise<Course[]> {
  return request("/courses");
}

export async function getUnits(courseId: number): Promise<Unit[]> {
  return request(`/courses/${courseId}/units`);
}

export async function getSentences(unitId: number): Promise<Sentence[]> {
  return request(`/courses/units/${unitId}/sentences`);
}

// ====== 对练 ======

export interface EvaluateResult {
  transcript: string;
  scores: { accuracy: number; fluency: number; completeness: number };
  feedback: string;
}

export async function evaluateSentence(
  audioBlob: Blob,
  sentenceId: number,
  sentenceText: string
): Promise<EvaluateResult> {
  const form = new FormData();
  form.append("audio", audioBlob, "recording.webm");
  form.append("sentence_id", String(sentenceId));
  form.append("sentence_text", sentenceText);
  const res = await fetch(`${BASE}/practice/evaluate`, { method: "POST", body: form });
  const json = await res.json();
  if (json.code !== 0) throw new Error(json.message);
  return json.data;
}

export interface ChatResult {
  session_id: string;
  user_text: string;
  reply: string;
  audio_base64: string | null;
}

export async function sendChatMessage(
  text: string,
  sessionId: string
): Promise<ChatResult> {
  const form = new FormData();
  form.append("text", text);
  form.append("session_id", sessionId);
  const res = await fetch(`${BASE}/practice/chat`, { method: "POST", body: form });
  const json = await res.json();
  if (json.code !== 0) throw new Error(json.message);
  return json.data;
}

export async function sendVoiceMessage(
  audioBlob: Blob,
  sessionId: string
): Promise<ChatResult> {
  const form = new FormData();
  form.append("audio", audioBlob, "recording.webm");
  form.append("session_id", sessionId);
  const res = await fetch(`${BASE}/practice/chat`, { method: "POST", body: form });
  const json = await res.json();
  if (json.code !== 0) throw new Error(json.message);
  return json.data;
}

export async function startSession(mode: "course" | "free_talk" = "free_talk"): Promise<string> {
  const form = new FormData();
  form.append("mode", mode);
  const res = await fetch(`${BASE}/practice/session/start`, { method: "POST", body: form });
  const json = await res.json();
  return json.data.session_id;
}

export interface ChatMessage {
  id: number;
  role: string;
  text: string;
  time: string;
}

export async function getChatHistory(sessionId: string): Promise<ChatMessage[]> {
  return request(`/practice/session/${sessionId}/history`);
}

// ====== 进度 ======

export interface OverallProgress {
  total_sentences: number;
  mastered_count: number;
  total_practices: number;
  mastery_rate: number;
}

export async function getOverallProgress(): Promise<OverallProgress> {
  return request("/progress");
}

export interface UnitProgress {
  sentence_id: number;
  sentence_text: string;
  practice_count: number;
  score_avg: number;
  mastered: boolean;
}

export async function getUnitProgress(unitId: number): Promise<UnitProgress[]> {
  return request(`/progress/unit/${unitId}`);
}

// ====== 记忆 ======

export interface MemorySummary {
  records: Record<string, { key: string; value: string; confidence: number }[]>;
  context_text: string;
}

export async function getMemorySummary(): Promise<MemorySummary> {
  return request("/memory/summary");
}
