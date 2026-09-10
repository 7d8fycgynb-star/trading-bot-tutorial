export function stripDiacritics(value: string) {
  return value.normalize("NFD").replace(/\p{M}/gu, "");
}

export function normalizeAnswer(value: string) {
  return stripDiacritics(value)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim()
    .replace(/\s+/g, " ");
}

export function answersMatch(input: string, expected: string, aliases: string[] = []) {
  const a = normalizeAnswer(input);
  if (!a) return false;
  const pool = [expected, ...aliases].map(normalizeAnswer);
  return pool.some((p) => p === a || p.includes(a) || a.includes(p));
}

export function keywordHits(input: string, keywords: string[]) {
  const a = normalizeAnswer(input);
  return keywords.filter((k) => {
    const n = normalizeAnswer(k);
    return n.length > 2 && a.includes(n);
  });
}

export function shuffle<T>(items: T[], rng = Math.random): T[] {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

export function pickN<T>(items: T[], n: number, rng = Math.random): T[] {
  return shuffle(items, rng).slice(0, n);
}

export function unique<T>(items: T[]): T[] {
  return [...new Set(items)];
}

export function mulberry32(seed: number) {
  let t = seed >>> 0;
  return () => {
    t += 0x6d2b79f5;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}

export function todayKey() {
  return new Date().toISOString().slice(0, 10);
}
