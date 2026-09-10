import { BOOKS, type Book } from "../data/books";
import { todayKey } from "./text";

export type BookStats = {
  seen: number;
  correct: number;
  wrong: number;
  streak: number;
  lastPlayed: string | null;
};

export type Progress = {
  xp: number;
  bestStreak: number;
  currentStreak: number;
  lastPlayDate: string | null;
  comboBest: number;
  books: Record<number, BookStats>;
  weakIds: string[];
  seenQuestionIds: string[];
  achievements: string[];
  oralBest: number;
};

const KEY = "komise-progress-v1";

function emptyBook(): BookStats {
  return { seen: 0, correct: 0, wrong: 0, streak: 0, lastPlayed: null };
}

export function defaultProgress(): Progress {
  const books: Record<number, BookStats> = {};
  for (const b of BOOKS) books[b.id] = emptyBook();
  return {
    xp: 0,
    bestStreak: 0,
    currentStreak: 0,
    lastPlayDate: null,
    comboBest: 0,
    books,
    weakIds: [],
    seenQuestionIds: [],
    achievements: [],
    oralBest: 0,
  };
}

export function loadProgress(): Progress {
  try {
    const raw = localStorage.getItem(KEY);
    if (!raw) return defaultProgress();
    const parsed = JSON.parse(raw) as Progress;
    const base = defaultProgress();
    return {
      ...base,
      ...parsed,
      books: { ...base.books, ...parsed.books },
    };
  } catch {
    return defaultProgress();
  }
}

export function saveProgress(progress: Progress) {
  localStorage.setItem(KEY, JSON.stringify(progress));
}

export function recordAnswer(
  progress: Progress,
  bookId: number | undefined,
  questionId: string,
  correct: boolean,
  combo: number,
): Progress {
  const next = structuredClone(progress) as Progress;
  const today = todayKey();
  if (next.lastPlayDate !== today) {
    if (next.lastPlayDate) {
      const prev = new Date(next.lastPlayDate + "T00:00:00");
      const now = new Date(today + "T00:00:00");
      const diff = (now.getTime() - prev.getTime()) / 86400000;
      next.currentStreak = diff === 1 ? next.currentStreak + 1 : 1;
    } else {
      next.currentStreak = 1;
    }
    next.lastPlayDate = today;
    next.bestStreak = Math.max(next.bestStreak, next.currentStreak);
  }

  next.xp += correct ? 12 + Math.min(combo, 8) * 2 : 2;
  next.comboBest = Math.max(next.comboBest, combo);
  if (!next.seenQuestionIds.includes(questionId)) {
    next.seenQuestionIds = [...next.seenQuestionIds.slice(-400), questionId];
  }

  if (correct) {
    next.weakIds = next.weakIds.filter((id) => id !== questionId);
  } else if (!next.weakIds.includes(questionId)) {
    next.weakIds = [questionId, ...next.weakIds].slice(0, 80);
  }

  if (bookId) {
    const stats = next.books[bookId] ?? emptyBook();
    stats.seen += 1;
    if (correct) {
      stats.correct += 1;
      stats.streak += 1;
    } else {
      stats.wrong += 1;
      stats.streak = 0;
    }
    stats.lastPlayed = today;
    next.books[bookId] = stats;
  }

  next.achievements = unlockAchievements(next);
  return next;
}

export function masteryOf(stats: BookStats | undefined) {
  if (!stats || stats.seen < 4) return 0;
  const ratio = stats.correct / stats.seen;
  if (ratio >= 0.92 && stats.seen >= 12) return 5;
  if (ratio >= 0.84 && stats.seen >= 10) return 4;
  if (ratio >= 0.72 && stats.seen >= 8) return 3;
  if (ratio >= 0.58) return 2;
  return 1;
}

export function overallReadiness(progress: Progress) {
  const scores = BOOKS.map((b) => masteryOf(progress.books[b.id]) / 5);
  return Math.round((scores.reduce((a, b) => a + b, 0) / scores.length) * 100);
}

export function levelFromXp(xp: number) {
  const level = Math.floor(Math.sqrt(xp / 40)) + 1;
  const floor = (level - 1) ** 2 * 40;
  const next = level ** 2 * 40;
  return { level, floor, next, pct: Math.min(100, ((xp - floor) / (next - floor)) * 100) };
}

function unlockAchievements(p: Progress) {
  const got = new Set(p.achievements);
  if (p.xp >= 50) got.add("prvni-kruh");
  if (p.currentStreak >= 3) got.add("tri-dny");
  if (p.comboBest >= 8) got.add("trans");
  if (BOOKS.every((b) => (p.books[b.id]?.seen ?? 0) >= 1)) got.add("vsech-dvacet");
  if (BOOKS.filter((b) => masteryOf(p.books[b.id]) >= 4).length >= 5) got.add("pet-jistych");
  if (p.oralBest >= 80) got.add("ustni-hrdina");
  if (p.xp >= 800) got.add("komise-se-boji");
  return [...got];
}

export const ACHIEVEMENTS: Record<string, { title: string; hint: string }> = {
  "prvni-kruh": { title: "První kruh pekla", hint: "Získej 50 XP" },
  "tri-dny": { title: "Tři dny bez úniku", hint: "Streak 3 dny" },
  trans: { title: "Trans", hint: "Combo 8 v řadě" },
  "vsech-dvacet": { title: "Seznam hotov", hint: "Alespoň jedna otázka ke každému dílu" },
  "pet-jistych": { title: "Pět jistých", hint: "5 děl na mistrovství 4+" },
  "ustni-hrdina": { title: "Ústní hrdina", hint: "80 %+ u komise" },
  "komise-se-boji": { title: "Komise se bojí", hint: "800 XP" },
};

export function weakestBooks(progress: Progress, n = 3): Book[] {
  return [...BOOKS]
    .sort((a, b) => {
      const sa = progress.books[a.id];
      const sb = progress.books[b.id];
      const ra = sa && sa.seen ? sa.correct / sa.seen : 0;
      const rb = sb && sb.seen ? sb.correct / sb.seen : 0;
      if ((sa?.seen ?? 0) === 0 && (sb?.seen ?? 0) > 0) return -1;
      if ((sb?.seen ?? 0) === 0 && (sa?.seen ?? 0) > 0) return 1;
      return ra - rb || (sa?.seen ?? 0) - (sb?.seen ?? 0);
    })
    .slice(0, n);
}
