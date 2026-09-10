import { useEffect, useMemo, useState } from "react";
import { BOOKS, bookLabel, getBook, type Book } from "./data/books";
import {
  ACHIEVEMENTS,
  levelFromXp,
  loadProgress,
  masteryOf,
  overallReadiness,
  recordAnswer,
  saveProgress,
  weakestBooks,
  type Progress,
} from "./lib/storage";
import { answersMatch, keywordHits, shuffle } from "./lib/text";
import {
  EXAMINER,
  examinerLine,
  matchRound,
  mixedQuestions,
  questionsForBook,
  type Question,
} from "./data/questions";

type View =
  | { name: "home" }
  | { name: "study"; bookId: number }
  | { name: "quiz"; mode: QuizMode; bookId?: number }
  | { name: "match" }
  | { name: "oral"; bookId?: number };

type QuizMode = "sprint" | "blitz" | "survival" | "book" | "weak";

function beep(ok: boolean) {
  try {
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.frequency.value = ok ? 784 : 196;
    gain.gain.value = 0.035;
    osc.start();
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.12);
    osc.stop(ctx.currentTime + 0.13);
  } catch {
    /* ignore */
  }
}

export default function App() {
  const [view, setView] = useState<View>({ name: "home" });
  const [progress, setProgress] = useState<Progress>(() => loadProgress());

  useEffect(() => saveProgress(progress), [progress]);

  const patch = (fn: (p: Progress) => Progress) => setProgress(fn);

  return (
    <div className="app">
      <header className="topbar">
        <button className="brand" onClick={() => setView({ name: "home" })}>
          <b>KOMISE</b>
          <span>maturitní četba</span>
        </button>
        <Hud progress={progress} />
      </header>
      {view.name === "home" && <Home progress={progress} go={setView} />}
      {view.name === "study" && <Study book={getBook(view.bookId)} go={setView} />}
      {view.name === "quiz" && (
        <Quiz
          mode={view.mode}
          bookId={view.bookId}
          progress={progress}
          onProgress={patch}
          onHome={() => setView({ name: "home" })}
          onStudy={(id) => setView({ name: "study", bookId: id })}
        />
      )}
      {view.name === "match" && (
        <Match progress={progress} onProgress={patch} onHome={() => setView({ name: "home" })} />
      )}
      {view.name === "oral" && (
        <Oral
          bookId={view.bookId}
          progress={progress}
          onProgress={patch}
          onHome={() => setView({ name: "home" })}
        />
      )}
    </div>
  );
}

function Hud({ progress }: { progress: Progress }) {
  const lv = levelFromXp(progress.xp);
  return (
    <div className="stats">
      <div className="pill">
        Lvl {lv.level}
        <span className="xpbar" aria-hidden>
          <i style={{ width: `${lv.pct}%` }} />
        </span>
      </div>
      <div className="pill">{progress.xp} XP</div>
      <div className="pill">🔥 {progress.currentStreak} dní</div>
    </div>
  );
}

function Home({
  progress,
  go,
}: {
  progress: Progress;
  go: (v: View) => void;
}) {
  const ready = overallReadiness(progress);
  const weak = weakestBooks(progress, 3);
  return (
    <>
      <section className="hero">
        <div className="panel">
          <div className="kicker">20 děl · žádný únik</div>
          <h1>Komise nespí. Ty taky ne.</h1>
          <p className="lead">
            Krátké sprinty, zákeřné záměny, doplňovačky a falešné ústní. Po každé chybě ti to
            rovnou vrazí do hlavy — a zítra to znovu vytáhne.
          </p>
          <div className="row">
            <button className="btn" onClick={() => go({ name: "quiz", mode: "sprint" })}>
              Dnešní sprint
            </button>
            <button className="btn wine" onClick={() => go({ name: "oral" })}>
              Ústní u komise
            </button>
            <button className="btn ghost" onClick={() => go({ name: "quiz", mode: "survival" })}>
              Survival
            </button>
          </div>
        </div>
        <div className="panel">
          <div className="kicker">připravenost</div>
          <div className="gauge">
            <svg width="148" height="148" viewBox="0 0 120 120">
              <circle cx="60" cy="60" r="52" fill="none" stroke="rgba(246,234,215,0.08)" strokeWidth="10" />
              <circle
                cx="60"
                cy="60"
                r="52"
                fill="none"
                stroke="#e8b86d"
                strokeWidth="10"
                strokeLinecap="round"
                strokeDasharray={`${2 * Math.PI * 52}`}
                strokeDashoffset={`${2 * Math.PI * 52 * (1 - ready / 100)}`}
              />
            </svg>
            <b>{ready}%</b>
          </div>
          <small>Mistrovství ze všech 20 děl</small>
          <div className="ach">
            {Object.entries(ACHIEVEMENTS).map(([id, a]) => (
              <span key={id} className={`badge ${progress.achievements.includes(id) ? "on" : ""}`} title={a.hint}>
                {a.title}
              </span>
            ))}
          </div>
        </div>
      </section>

      <div className="modes">
        <button className="mode" onClick={() => go({ name: "quiz", mode: "blitz" })}>
          <span className="tag">10 s · tlak</span>
          <strong>Blitz</strong>
          <p>Rychlovka, ať neusneš. Čtyři volby, žádné výmluvy.</p>
        </button>
        <button className="mode" onClick={() => go({ name: "match" })}>
          <span className="tag">páry</span>
          <strong>Párování</strong>
          <p>Autor, postava, směr, žánr. Klikni levou, klikni pravou.</p>
        </button>
        <button className="mode" onClick={() => go({ name: "quiz", mode: "weak" })}>
          <span className="tag">oprava</span>
          <strong>Slabiny</strong>
          <p>Jen to, co jsi pokazil. Komise má paměť.</p>
        </button>
        <button className="mode" onClick={() => go({ name: "quiz", mode: "survival" })}>
          <span className="tag">3 životy</span>
          <strong>Survival</strong>
          <p>Dokud nespadneš. Combo násobí XP.</p>
        </button>
      </div>

      <div className="section-h">
        <div>
          <div className="kicker">seznam četby</div>
          <h2>Klepni, uč se, pak se nech seřezat</h2>
        </div>
        <p className="lead" style={{ margin: 0 }}>
          Nejdřív karta, potom kvíz z díla. Slabá místa: {weak.map((b) => b.title).join(", ")}.
        </p>
      </div>
      <div className="shelf">
        {BOOKS.map((book) => {
          const m = masteryOf(progress.books[book.id]);
          return (
            <article key={book.id} className="book" style={{ ["--accent" as string]: book.accent }}>
              <em>
                {book.id}. {book.authorShort}
              </em>
              <b>{book.title}</b>
              <div className="stars">{"★".repeat(m)}{"☆".repeat(5 - m)}</div>
              <div className="row" style={{ marginTop: 10 }}>
                <button className="btn ghost" onClick={() => go({ name: "study", bookId: book.id })}>
                  Učit
                </button>
                <button className="btn" onClick={() => go({ name: "quiz", mode: "book", bookId: book.id })}>
                  Kvíz
                </button>
              </div>
            </article>
          );
        })}
      </div>
    </>
  );
}

function Study({ book, go }: { book: Book; go: (v: View) => void }) {
  const cards = useMemo(() => studyCards(book), [book]);
  const [open, setOpen] = useState<Record<string, boolean>>({});
  return (
    <div>
      <button className="back" onClick={() => go({ name: "home" })}>
        ← zpět ke komisi
      </button>
      <div className="kicker">
        {book.id} / 20 · {book.period}
      </div>
      <h1>
        {book.authorShort}: {book.title}
      </h1>
      <p className="lead">{book.theme}</p>
      <div className="row" style={{ marginBottom: 18 }}>
        <button className="btn" onClick={() => go({ name: "quiz", mode: "book", bookId: book.id })}>
          Přezkoušet tohle dílo
        </button>
        <button className="btn wine" onClick={() => go({ name: "oral", bookId: book.id })}>
          Ústní z díla
        </button>
      </div>
      <div className="cards">
        {cards.map((c) => (
          <button
            key={c.id}
            className={`flip ${open[c.id] ? "open" : ""}`}
            onClick={() => setOpen((s) => ({ ...s, [c.id]: !s[c.id] }))}
          >
            <div className="q">{c.q}</div>
            <div className="a">{open[c.id] ? c.a : "Klepni a odhal. Pak si to řekni nahlas."}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

function studyCards(book: Book) {
  return [
    { id: "i1", q: "I · Téma a motiv", a: `${book.theme} Motivy: ${book.motifs.join(", ")}.` },
    { id: "i2", q: "I · Časoprostor", a: `${book.setting}. ${book.timeFrame}.` },
    { id: "i3", q: "I · Kompozice", a: book.composition },
    { id: "i4", q: "I · Druh a žánr", a: `${book.kind}. Žánr: ${book.genre}.` },
    { id: "i5", q: "I · Kam zasadit výňatek", a: book.excerptHints.join(" · ") },
    { id: "ii1", q: "II · Vypravěč", a: book.narrator },
    {
      id: "ii2",
      q: "II · Postavy",
      a: book.characters.map((c) => `${c.name}: ${c.about}`).join(" · "),
    },
    { id: "ii3", q: "II · Typy promluv", a: book.speech },
    { id: "ii4", q: "II · Veršová výstavba", a: book.verse },
    { id: "iii1", q: "III · Jazyk", a: book.language },
    { id: "iii2", q: "III · Tropy a funkce", a: `${book.tropes} Funkce: ${book.tropesFunction}` },
    { id: "k1", q: "Kontext autora", a: `${book.authorFull} (${book.life}). ${book.authorContext}` },
    { id: "k2", q: "Literární kontext", a: `${book.literaryContext} ${book.periodDetail}` },
    { id: "k3", q: "To, co si komise pamatuje", a: book.funFact },
  ];
}

function buildQuiz(mode: QuizMode, bookId: number | undefined, weakIds: string[]) {
  if (mode === "book" && bookId) {
    return shuffle(questionsForBook(bookId, ["mcq", "blank"])).slice(0, 12);
  }
  if (mode === "weak") {
    return mixedQuestions({ count: 12, types: ["mcq", "blank"], preferIds: weakIds });
  }
  if (mode === "blitz") {
    return mixedQuestions({ count: 16, types: ["mcq"] });
  }
  if (mode === "survival") {
    return mixedQuestions({ count: 40, types: ["mcq", "blank"], preferIds: weakIds });
  }
  return mixedQuestions({ count: 12, types: ["mcq", "blank"], preferIds: weakIds });
}

function Quiz({
  mode,
  bookId,
  progress,
  onProgress,
  onHome,
  onStudy,
}: {
  mode: QuizMode;
  bookId?: number;
  progress: Progress;
  onProgress: (fn: (p: Progress) => Progress) => void;
  onHome: () => void;
  onStudy: (id: number) => void;
}) {
  const questions = useMemo(() => buildQuiz(mode, bookId, progress.weakIds), [mode, bookId]);
  const seconds = mode === "blitz" ? 10 : mode === "sprint" ? 18 : 0;
  const [i, setI] = useState(0);
  const [combo, setCombo] = useState(0);
  const [lives, setLives] = useState(3);
  const [correctN, setCorrectN] = useState(0);
  const [answered, setAnswered] = useState<null | boolean>(null);
  const [picked, setPicked] = useState<string | null>(null);
  const [typed, setTyped] = useState("");
  const [left, setLeft] = useState(seconds);
  const [misses, setMisses] = useState<Question[]>([]);
  const [line, setLine] = useState("");
  const [done, setDone] = useState(false);

  const q = questions[i];

  function resolve(ok: boolean, value: string) {
    if (answered !== null || !q) return;
    const nextCombo = ok ? combo + 1 : 0;
    beep(ok);
    setAnswered(ok);
    setPicked(value);
    setCombo(nextCombo);
    setLine(examinerLine(ok, nextCombo));
    setCorrectN((n) => n + (ok ? 1 : 0));
    if (!ok) {
      setMisses((ms) => [...ms, q]);
      setLives((l) => {
        if (mode === "survival" && l - 1 <= 0) window.setTimeout(() => setDone(true), 700);
        return l - 1;
      });
    }
    onProgress((p) => recordAnswer(p, q.bookId, q.id, ok, nextCombo));
  }

  useEffect(() => {
    if (!seconds || answered !== null || done || !q) return;
    setLeft(seconds);
    const t = window.setInterval(() => {
      setLeft((s) => {
        if (s <= 1) {
          window.clearInterval(t);
          resolve(false, "");
          return 0;
        }
        return s - 1;
      });
    }, 1000);
    return () => window.clearInterval(t);
  }, [i, seconds, done, answered]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!q || answered !== null || q.type !== "mcq" || !q.options) return;
      const n = Number(e.key);
      if (n >= 1 && n <= q.options.length) resolve(q.options[n - 1] === q.answer, q.options[n - 1]);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [q, answered]);

  if (!q || done) {
    const total = mode === "survival" ? Math.max(correctN + misses.length, 1) : questions.length;
    const pct = Math.round((correctN / total) * 100);
    return (
      <div className="panel result qwrap">
        <div className="kicker">{labelOf(mode)}</div>
        <h2>{pct}%</h2>
        <p className="lead">
          {correctN} správně · combo max se počítá do XP.{" "}
          {pct >= 85 ? "Komise mlčí — to je kompliment." : "Ještě to není ústní. Oprav chyby."}
        </p>
        <div className="row" style={{ justifyContent: "center" }}>
          <button className="btn" onClick={onHome}>
            Domů
          </button>
          {misses[0]?.bookId && (
            <button className="btn ghost" onClick={() => onStudy(misses[0].bookId!)}>
              Učit první chybu
            </button>
          )}
        </div>
        {misses.length > 0 && (
          <div className="misses">
            {misses.slice(0, 8).map((m) => (
              <div className="miss" key={m.id}>
                <b>{m.prompt}</b>
                <div>Správně: {m.answer}</div>
                <small style={{ color: "var(--muted)" }}>{m.explanation}</small>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  function next() {
    if (i + 1 >= questions.length) setDone(true);
    else {
      setI(i + 1);
      setAnswered(null);
      setPicked(null);
      setTyped("");
      setLine("");
    }
  }

  return (
    <div className="qwrap">
      <button className="back" onClick={onHome}>
        ← ven
      </button>
      <div className="meta">
        <span>
          {labelOf(mode)} · {i + 1}/{mode === "survival" ? "∞" : questions.length}
          {mode === "survival" ? ` · životy ${"♥".repeat(lives)}` : ""}
        </span>
        <span className="combo">{combo > 1 ? `combo ×${combo}` : " "}</span>
      </div>
      {seconds > 0 && (
        <div className={`timer ${left <= 4 ? "hot" : ""}`}>
          <i style={{ width: `${(left / seconds) * 100}%` }} />
        </div>
      )}
      <p className="prompt">{q.prompt}</p>
      {q.type === "mcq" && q.options && (
        <div className="options">
          {q.options.map((opt, idx) => {
            let cls = "opt";
            if (answered !== null && opt === q.answer) cls += " good";
            else if (answered !== null && opt === picked && !answered) cls += " bad";
            return (
              <button key={`${idx}-${opt.slice(0, 24)}`} className={cls} disabled={answered !== null} onClick={() => resolve(opt === q.answer, opt)}>
                <small>{idx + 1}</small>
                {opt}
              </button>
            );
          })}
        </div>
      )}
      {q.type === "blank" && (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            resolve(answersMatch(typed, q.answer, q.aliases), typed);
          }}
        >
          <input
            className="blank"
            autoFocus
            value={typed}
            placeholder="Napiš odpověď…"
            onChange={(e) => setTyped(e.target.value)}
            disabled={answered !== null}
          />
          <div className="row" style={{ marginTop: 12 }}>
            <button className="btn" disabled={answered !== null}>
              Zkontrolovat
            </button>
          </div>
        </form>
      )}
      {answered !== null && (
        <div className={`feedback ${answered ? "ok" : "no"}`}>
          <b>{line}</b>
          <p style={{ margin: "8px 0 12px", lineHeight: 1.5 }}>{q.explanation}</p>
          {q.bookId && (
            <button className="btn ghost" onClick={() => onStudy(q.bookId!)}>
              Otevřít {bookLabel(getBook(q.bookId))}
            </button>
          )}
          <button className="btn" style={{ marginLeft: 8 }} onClick={next}>
            Další
          </button>
        </div>
      )}
    </div>
  );
}

function labelOf(mode: QuizMode) {
  return {
    sprint: "Sprint",
    blitz: "Blitz",
    survival: "Survival",
    book: "Kvíz díla",
    weak: "Slabiny",
  }[mode];
}

function Match({
  onProgress,
  onHome,
}: {
  progress: Progress;
  onProgress: (fn: (p: Progress) => Progress) => void;
  onHome: () => void;
}) {
  const kinds = ["author", "character", "period", "genre"] as const;
  const [kind, setKind] = useState<(typeof kinds)[number]>("character");
  const [pairs, setPairs] = useState(() => matchRound("character"));
  const [leftSel, setLeftSel] = useState<number | null>(null);
  const [matched, setMatched] = useState<number[]>([]);
  const [score, setScore] = useState(0);
  const [wrong, setWrong] = useState(0);
  const left = useMemo(
    () => shuffle(pairs.map((p, idx) => ({ idx, label: p.left, bookId: p.bookId }))),
    [pairs],
  );
  const right = useMemo(
    () => shuffle(pairs.map((p, idx) => ({ idx, label: p.right, bookId: p.bookId }))),
    [pairs],
  );

  function deal(nextKind: (typeof kinds)[number]) {
    setKind(nextKind);
    setPairs(matchRound(nextKind));
    setLeftSel(null);
    setMatched([]);
    setScore(0);
    setWrong(0);
  }

  function clickRight(idx: number) {
    if (leftSel === null || matched.includes(idx)) return;
    const pair = pairs[leftSel];
    const ok = leftSel === idx;
    beep(ok);
    onProgress((p) => recordAnswer(p, pair.bookId, `match-${kind}-${pair.left}`, ok, ok ? score + 1 : 0));
    if (ok) {
      setMatched((m) => [...m, idx]);
      setScore((s) => s + 1);
      setLeftSel(null);
    } else {
      setWrong((w) => w + 1);
      setLeftSel(null);
    }
  }

  const done = matched.length === pairs.length;

  return (
    <div>
      <button className="back" onClick={onHome}>
        ← ven
      </button>
      <div className="kicker">párování</div>
      <h1>Spoj, než se to splete</h1>
      <div className="row" style={{ marginBottom: 16 }}>
        {kinds.map((k) => (
          <button key={k} className={`btn ${k === kind ? "" : "ghost"}`} onClick={() => deal(k)}>
            {k === "author" ? "Autor" : k === "character" ? "Postava" : k === "period" ? "Směr" : "Žánr"}
          </button>
        ))}
      </div>
      <p className="lead">
        Skóre {score}/{pairs.length} · chyby {wrong}
        {done ? " · hotovo. Dej další kolo." : ""}
      </p>
      <div className="matchboard">
        <div className="options">
          {left.map((item) => (
            <button
              key={`L${item.idx}`}
              className={`chip ${leftSel === item.idx ? "on" : ""} ${matched.includes(item.idx) ? "gone" : ""}`}
              onClick={() => setLeftSel(item.idx)}
              disabled={matched.includes(item.idx)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <div className="options">
          {right.map((item) => (
            <button
              key={`R${item.idx}`}
              className={`chip ${matched.includes(item.idx) ? "gone" : ""}`}
              onClick={() => clickRight(item.idx)}
              disabled={matched.includes(item.idx)}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function Oral({
  bookId,
  onProgress,
  onHome,
}: {
  bookId?: number;
  progress: Progress;
  onProgress: (fn: (p: Progress) => Progress) => void;
  onHome: () => void;
}) {
  const [id, setId] = useState(bookId ?? shuffle(BOOKS)[0].id);
  const book = getBook(id);
  const questions = useMemo(() => questionsForBook(id, ["oral"]), [id]);
  const [i, setI] = useState(0);
  const [text, setText] = useState("");
  const [revealed, setRevealed] = useState(false);
  const [scores, setScores] = useState<number[]>([]);
  const finished = scores.length === questions.length && questions.length > 0;
  const q = questions[i];
  const hits = q ? keywordHits(text, q.keywords ?? []) : [];
  const need = Math.max(q?.keywords?.length ?? 1, 1);
  const pct = Math.round((hits.length / need) * 100);

  if (finished || !q) {
    const avg = Math.round(scores.reduce((a, b) => a + b, 0) / Math.max(scores.length, 1));
    return (
      <div className="panel result qwrap">
        <div className="kicker">ústní · {book.title}</div>
        <h2>{avg}%</h2>
        <p className="lead">
          {avg >= 80
            ? "Komise by tě pustila dál. Ještě si procvič zákeřné detaily v kvízu."
            : "Chybí klíčová slova. Vrať se ke kartám a řekni to nahlas."}
        </p>
        <div className="row" style={{ justifyContent: "center" }}>
          <button className="btn" onClick={onHome}>
            Domů
          </button>
          <button
            className="btn ghost"
            onClick={() => {
              setId(shuffle(BOOKS.filter((b) => b.id !== id))[0].id);
              setI(0);
              setText("");
              setRevealed(false);
              setScores([]);
            }}
          >
            Další dílo
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="qwrap">
      <button className="back" onClick={onHome}>
        ← ven
      </button>
      <div className="kicker">
        ústní zkouška · {book.authorShort}: {book.title} · {q.category}
      </div>
      <p className="prompt">{q.prompt}</p>
      <p className="lead">Piš tak, jak bys to řekl komisi. Bodují se klíčová slova, ne sloh.</p>
      <textarea className="oral-box" value={text} onChange={(e) => setText(e.target.value)} placeholder="Mluv. Teda piš." />
      <div className="keys">
        {(q.keywords ?? []).map((k) => (
          <span key={k} className={`key ${hits.includes(k) ? "hit" : ""}`}>
            {revealed || hits.includes(k) ? k : "•••"}
          </span>
        ))}
      </div>
      <div className="row" style={{ marginTop: 14 }}>
        <button className="btn ghost" onClick={() => setRevealed(true)}>
          Ukázat vzor
        </button>
        <button
          className="btn"
          onClick={() => {
            const score = pct;
            const last = i + 1 >= questions.length;
            beep(score >= 60);
            onProgress((p) => {
              const next = recordAnswer(p, id, q.id, score >= 60, Math.round(score / 20));
              if (!last) return next;
              const avg = Math.round([...scores, score].reduce((a, b) => a + b, 0) / questions.length);
              return { ...next, oralBest: Math.max(next.oralBest, avg), xp: next.xp + Math.round(avg / 4) };
            });
            setScores((s) => [...s, score]);
            setI(i + 1);
            setText("");
            setRevealed(false);
          }}
        >
          Odevzdat ({pct}%)
        </button>
      </div>
      {revealed && (
        <div className="feedback ok">
          <b>{pickNLine()}</b>
          <p style={{ lineHeight: 1.55 }}>{q.answer}</p>
        </div>
      )}
    </div>
  );
}

function pickNLine() {
  return EXAMINER.correct[Math.floor(Math.random() * EXAMINER.correct.length)];
}
