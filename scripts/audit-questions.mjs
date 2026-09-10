import { QUESTION_BANK } from "../src/data/questions.ts";
import { normalizeAnswer } from "../src/lib/text.ts";
import { BOOKS } from "../src/data/books.ts";

function leak(prompt, answer) {
  const p = normalizeAnswer(prompt);
  const hits = [];
  for (const book of BOOKS) {
    const t = normalizeAnswer(book.title);
    if (t.length > 3 && p.includes(t) && normalizeAnswer(answer).includes(t)) hits.push(book.title);
  }
  return hits;
}

const quiz = QUESTION_BANK.filter((q) => q.type !== "oral");
console.log("quiz questions", quiz.length, "total", QUESTION_BANK.length);

const leaked = quiz.filter((q) => leak(q.prompt, q.answer).length > 0);
console.log("title leaked in prompt+answer", leaked.length);
for (const q of leaked) {
  console.log("-", q.id, "|", q.prompt, "=>", String(q.answer).slice(0, 90), "|", leak(q.prompt, q.answer));
}

const moliere = quiz.filter(
  (q) => /moliere|lakomec|tartuffe/i.test(q.id + q.prompt) || q.bookId === 1 || q.bookId === 2,
);
console.log("\nmoliere-related quiz", moliere.length);
for (const q of moliere.filter((q) => q.type === "mcq").slice(0, 30)) {
  console.log("*", q.prompt);
  console.log("  A:", q.answer);
}
