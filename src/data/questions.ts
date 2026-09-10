import { BOOKS, bookLabel, type Book } from "./books";
import { normalizeAnswer, pickN, shuffle, unique } from "../lib/text";

export type QType = "mcq" | "blank" | "oral";

export type Question = {
  id: string;
  type: QType;
  bookId?: number;
  difficulty: 1 | 2 | 3;
  category: string;
  prompt: string;
  options?: string[];
  answer: string;
  aliases?: string[];
  explanation: string;
  keywords?: string[];
};

function others(book: Book) {
  return BOOKS.filter((b) => b.id !== book.id);
}

function sameAuthor(book: Book) {
  return BOOKS.filter((b) => b.authorShort === book.authorShort);
}

function namesOverlap(a: string, b: string) {
  const na = normalizeAnswer(a);
  const nb = normalizeAnswer(b);
  if (na.length < 4 || nb.length < 4) return false;
  return na.includes(nb) || nb.includes(na);
}

function mentionsBook(text: string, book: Book) {
  if (namesOverlap(text, book.title)) return true;
  return book.aliases.some(
    (alias) => alias.length > 3 && namesOverlap(alias, book.title) && namesOverlap(text, alias),
  );
}

const GENERIC = new Set([
  "komedie",
  "tragedie",
  "drama",
  "epika",
  "lyrika",
  "novela",
  "povidka",
  "roman",
  "proza",
  "autor",
  "dilo",
  "dila",
  "postava",
  "motiv",
  "tema",
  "kontext",
  "stoleti",
  "literarni",
  "historicky",
  "klasicky",
  "vypravec",
  "satira",
  "hrdina",
  "hlavni",
  "vedlejsi",
]);

/** True when the prompt already contains a distinctive piece of the answer. */
function answerInPrompt(prompt: string, answer: string, book?: Book) {
  if (book && mentionsBook(prompt, book) && mentionsBook(answer, book)) return true;
  const promptNorm = normalizeAnswer(prompt);
  const tokens = normalizeAnswer(answer)
    .split(" ")
    .filter((t) => t.length >= 6 && !GENERIC.has(t));
  return tokens.some((t) => promptNorm.includes(t));
}

function usableCharacter(book: Book) {
  return book.characters.find((c) => !namesOverlap(c.name, book.title)) ?? null;
}

function distractors(book: Book, pick: (b: Book) => string, n = 3) {
  const value = pick(book);
  const pool = unique(others(book).map(pick).filter((v) => v && v !== value));
  return pickN(pool, n);
}

function mcq(
  id: string,
  book: Book | undefined,
  prompt: string,
  answer: string,
  wrong: string[],
  explanation: string,
  category: string,
  difficulty: 1 | 2 | 3 = 2,
): Question | null {
  if (answerInPrompt(prompt, answer, book)) return null;
  const opts = unique([answer, ...wrong.filter(Boolean)]).filter((o) => o !== answer);
  if (opts.length < 2) return null;
  return {
    id,
    type: "mcq",
    bookId: book?.id,
    difficulty,
    category,
    prompt,
    options: shuffle([answer, ...pickN(opts, 3)]),
    answer,
    explanation,
    aliases: book?.aliases,
  };
}

function blank(
  id: string,
  book: Book,
  prompt: string,
  answer: string,
  aliases: string[],
  explanation: string,
  category: string,
  difficulty: 1 | 2 | 3 = 2,
): Question | null {
  if (answerInPrompt(prompt, answer, book)) return null;
  return {
    id,
    type: "blank",
    bookId: book.id,
    difficulty,
    category,
    prompt,
    answer,
    aliases: [...book.aliases, ...aliases],
    explanation,
  };
}

function oral(
  id: string,
  book: Book,
  prompt: string,
  answer: string,
  keywords: string[],
  category: string,
): Question {
  return {
    id,
    type: "oral",
    bookId: book.id,
    difficulty: 3,
    category,
    prompt,
    answer,
    explanation: answer,
    keywords: keywords.map((k) => k.trim()).filter((k) => k.length > 2),
  };
}

function buildBank(): Question[] {
  const qs: Question[] = [];
  const add = (q: Question | null | undefined) => {
    if (q) qs.push(q);
  };

  const authorsDone = new Set<string>();

  for (const book of BOOKS) {
    const siblings = sameAuthor(book);

    add(
      mcq(
        `${book.id}-author`,
        book,
        `Kdo napsal dílo ${book.title}?`,
        book.authorFull,
        distractors(book, (b) => b.authorFull),
        `${book.title} napsal/a ${book.authorFull} (${book.life}). ${siblings.length > 1 ? `Stejný autor má na seznamu i: ${siblings.filter((s) => s.id !== book.id).map((s) => s.title).join(", ")}.` : ""}`,
        "autor",
        1,
      ),
    );

    if (siblings.length === 1) {
      add(
        mcq(
          `${book.id}-title-from-author`,
          book,
          `Které dílo z četby patří autorovi ${book.authorShort}?`,
          book.title,
          distractors(book, (b) => b.title),
          `${book.authorShort}: ${book.title}.`,
          "dílo",
          1,
        ),
      );
      add(
        blank(
          `${book.id}-blank-title`,
          book,
          `Doplň název díla, které na seznamu napsal/a ${book.authorShort}.`,
          book.title,
          [book.title.replaceAll(".", "")],
          `${book.authorShort}: ${book.title}`,
          "dílo",
          1,
        ),
      );
    }

    add(
      mcq(
        `${book.id}-kind`,
        book,
        `Jaký literární druh je ${book.title}?`,
        book.kind,
        distractors(book, (b) => b.kind),
        `${book.title} je ${book.kind.toLowerCase()}. Žánr: ${book.genre}.`,
        "druh",
        1,
      ),
    );
    add(
      mcq(
        `${book.id}-genre`,
        book,
        `Jaký žánr je ${book.title}?`,
        book.genre,
        distractors(book, (b) => b.genre),
        `${book.title} = ${book.genre}.`,
        "žánr",
        2,
      ),
    );
    add(
      mcq(
        `${book.id}-period`,
        book,
        `Do jakého směru / období patří ${book.title}?`,
        book.period,
        distractors(book, (b) => b.period),
        `${book.title}: ${book.period}. ${book.periodDetail}`,
        "kontext",
        2,
      ),
    );

    if (!mentionsBook(book.setting, book)) {
      add(
        mcq(
          `${book.id}-setting`,
          book,
          `Kde se odehrává ${book.title}?`,
          book.setting,
          distractors(book, (b) => b.setting),
          `Časoprostor: ${book.setting}. ${book.timeFrame}.`,
          "časoprostor",
          2,
        ),
      );
      add(
        mcq(
          `${book.id}-setting-rev`,
          book,
          `Které dílo se odehrává zde: ${book.setting}?`,
          book.title,
          distractors(book, (b) => b.title),
          `${book.title}: ${book.setting}.`,
          "časoprostor",
          2,
        ),
      );
    }

    if (!mentionsBook(book.timeFrame, book)) {
      add(
        mcq(
          `${book.id}-time`,
          book,
          `Jaký je časový rámec díla ${book.title}?`,
          book.timeFrame,
          distractors(book, (b) => b.timeFrame),
          book.timeFrame,
          "časoprostor",
          2,
        ),
      );
    }

    add(
      mcq(
        `${book.id}-narrator`,
        book,
        `Jaký vypravěč / lyrický subjekt má ${book.title}?`,
        book.narrator,
        distractors(book, (b) => b.narrator),
        book.narrator,
        "vypravěč",
        2,
      ),
    );
    add(
      mcq(
        `${book.id}-verse`,
        book,
        `Jaká je veršová výstavba díla ${book.title}?`,
        book.verse,
        distractors(book, (b) => b.verse),
        book.verse,
        "verš",
        2,
      ),
    );
    add(
      mcq(
        `${book.id}-composition`,
        book,
        `Jaká je kompozice díla ${book.title}?`,
        book.composition,
        distractors(book, (b) => b.composition),
        book.composition,
        "kompozice",
        3,
      ),
    );
    add(
      mcq(
        `${book.id}-theme`,
        book,
        `Co je tématem díla ${book.title}?`,
        book.theme,
        distractors(book, (b) => b.theme),
        `Téma: ${book.theme} Motivy: ${book.motifs.join(", ")}.`,
        "téma",
        2,
      ),
    );
    add(
      mcq(
        `${book.id}-language`,
        book,
        `Jaké jazykové prostředky jsou typické pro ${book.title}?`,
        book.language,
        distractors(book, (b) => b.language),
        book.language,
        "jazyk",
        3,
      ),
    );
    add(
      mcq(
        `${book.id}-tropes`,
        book,
        `Jaké tropy a figury se pojí s dílem ${book.title}?`,
        book.tropes,
        distractors(book, (b) => b.tropes),
        `${book.tropes} Funkce: ${book.tropesFunction}`,
        "tropy",
        3,
      ),
    );
    add(
      mcq(
        `${book.id}-context`,
        book,
        `Jaký je literárněhistorický kontext díla ${book.title}?`,
        book.literaryContext,
        distractors(book, (b) => b.literaryContext),
        book.literaryContext,
        "kontext",
        3,
      ),
    );

    if (!authorsDone.has(book.authorShort)) {
      authorsDone.add(book.authorShort);
      add(
        mcq(
          `${book.authorShort}-fun`,
          book,
          `Který fakt platí o autorovi ${book.authorShort}?`,
          book.funFact,
          unique(BOOKS.filter((b) => b.authorShort !== book.authorShort).map((b) => b.funFact)),
          `${book.authorFull}: ${book.funFact}`,
          "autor",
          2,
        ),
      );
    }

    const face = usableCharacter(book);
    if (face) {
      add(
        mcq(
          `${book.id}-char-work`,
          book,
          `Ve kterém díle vystupuje ${face.name}?`,
          book.title,
          distractors(book, (b) => b.title),
          `${face.name} (${face.about}) — ${bookLabel(book)}.`,
          "postavy",
          1,
        ),
      );
      if (!mentionsBook(face.about, book)) {
        add(
          mcq(
            `${book.id}-char-who`,
            book,
            `Kdo je ${face.name}?`,
            `${face.about} (${book.title})`,
            pickN(
              others(book).flatMap((b) => {
                const c = usableCharacter(b);
                return c ? [`${c.about} (${b.title})`] : [];
              }),
              3,
            ),
            `${face.name}: ${face.about}. Dílo: ${book.title}.`,
            "postavy",
            2,
          ),
        );
      }
    }

    const extraChar = book.characters.find(
      (c, i) => i > 0 && !namesOverlap(c.name, book.title) && c.name !== face?.name,
    );
    if (extraChar) {
      add(
        mcq(
          `${book.id}-char-extra`,
          book,
          `Která postava patří do díla ${book.title}?`,
          extraChar.name,
          pickN(
            others(book)
              .flatMap((b) => b.characters.map((c) => c.name))
              .filter((n) => !namesOverlap(n, book.title)),
            3,
          ),
          `${extraChar.name}: ${extraChar.about}.`,
          "postavy",
          2,
        ),
      );
    }

    const motif = book.motifs.find((m) => !namesOverlap(m, book.title));
    if (motif) {
      add(
        mcq(
          `${book.id}-motif`,
          book,
          `Který motiv je ústřední pro ${book.title}?`,
          motif,
          pickN(
            unique(others(book).flatMap((b) => b.motifs)).filter((m) => !book.motifs.includes(m)),
            3,
          ),
          `Motivy ${book.title}: ${book.motifs.join(", ")}.`,
          "motivy",
          2,
        ),
      );
    }

    add(
      blank(
        `${book.id}-blank-genre`,
        book,
        `Doplň žánr díla ${book.title}.`,
        book.genre,
        [],
        `${book.title} = ${book.genre}`,
        "žánr",
        2,
      ),
    );
    add(
      blank(
        `${book.id}-blank-period`,
        book,
        `Doplň směr / období díla ${book.title}.`,
        book.period,
        [book.period.split("/")[0].trim()],
        `${book.title}: ${book.period}`,
        "kontext",
        2,
      ),
    );
    add(
      blank(
        `${book.id}-blank-kind`,
        book,
        `Doplň literární druh díla ${book.title} (drama / epika / lyricko-epický text).`,
        book.kind,
        [book.kind.split(" ")[0]],
        `${book.title} je ${book.kind.toLowerCase()}.`,
        "druh",
        1,
      ),
    );

    add(
      oral(
        `${book.id}-oral-theme`,
        book,
        `Řekni komisi téma a motivy díla ${book.title}.`,
        `${book.theme} Motivy: ${book.motifs.join(", ")}.`,
        [book.theme.split(",")[0], ...book.motifs.slice(0, 3)],
        "ústní I",
      ),
    );
    add(
      oral(
        `${book.id}-oral-space`,
        book,
        `Popiš časoprostor díla ${book.title}.`,
        `${book.setting}. ${book.timeFrame}.`,
        [book.setting.split(",")[0], ...book.timeFrame.split(",").slice(0, 2)],
        "ústní I",
      ),
    );
    add(
      oral(
        `${book.id}-oral-comp`,
        book,
        `Jaká je kompoziční výstavba díla ${book.title}?`,
        book.composition,
        book.composition.split(/[,.]/).slice(0, 3),
        "ústní I",
      ),
    );
    add(
      oral(
        `${book.id}-oral-chars`,
        book,
        `Představ hlavní postavy díla ${book.title}.`,
        book.characters.map((c) => `${c.name}: ${c.about}`).join("; "),
        book.characters.slice(0, 3).map((c) => c.name),
        "ústní II",
      ),
    );
    add(
      oral(
        `${book.id}-oral-lang`,
        book,
        `Jazykové prostředky a tropy v díle ${book.title}?`,
        `${book.language} Tropy: ${book.tropes} Funkce: ${book.tropesFunction}`,
        [...book.tropes.split("(")[0].split(",").slice(0, 2), book.tropesFunction.split(" ")[0]],
        "ústní III",
      ),
    );
    add(
      oral(
        `${book.id}-oral-context`,
        book,
        `Literárněhistorický kontext a autor díla ${book.title}. Nepleť ho s jiným dílem téhož autora, pokud ho na seznamu máš.`,
        `${book.authorFull} (${book.life}). ${book.authorContext} ${book.literaryContext}`,
        [book.authorShort, book.period, book.life],
        "kontext",
      ),
    );
  }

  const lakomec = BOOKS.find((b) => b.id === 1)!;
  const tartuffe = BOOKS.find((b) => b.id === 2)!;
  add(
    mcq(
      "moliere-pair",
      lakomec,
      "Která dvojice děl na seznamu je od téhož autora — Molièra?",
      "Lakomec a Tartuffe",
      [
        "Lakomec a Revizor",
        "Tartuffe a Kulička",
        "Petr a Lucie a Malý princ",
        "R.U.R. a Farma zvířat",
      ],
      "Molière má na seznamu dvě hry: Lakomec (próza) a Tartuffe (alexandríny).",
      "zákeřné",
      2,
    ),
  );
  add(
    mcq(
      "moliere-not",
      tartuffe,
      "Které z těchto děl NENÍ od Molièra?",
      "Revizor",
      ["Lakomec", "Tartuffe", "Noc na Karlštejně"],
      "Lakomec i Tartuffe jsou Molière. Revizor je Gogol.",
      "zákeřné",
      1,
    ),
  );
  add(
    blank(
      "moliere-blank-kasa",
      lakomec,
      "Molièrova hra, kde hospodář zuří kvůli ukradené kasičce, se jmenuje ____.",
      "Lakomec",
      ["harpagon"],
      "Lakomec. Tartuffe je o pokrytectví, ne o kasičce.",
      "dílo",
      2,
    ),
  );
  add(
    blank(
      "moliere-blank-ban",
      tartuffe,
      "Molièrova hra, kterou církev na pět let zakázala, se jmenuje ____.",
      "Tartuffe",
      ["tartuf"],
      "Tartuffe. Lakomec církev nezakázala.",
      "dílo",
      2,
    ),
  );

  const extras: Question[] = [
    {
      id: "x-moliere-pair",
      type: "mcq",
      bookId: 1,
      difficulty: 2,
      category: "zákeřné",
      prompt: "Co mají Lakomec a Tartuffe společného?",
      options: shuffle([
        "Klasicismus, 5 dějství, pravidlo tří jednot, Paříž, deus ex machina",
        "Obě jsou psány alexandrínem",
        "Obě se odehrávají v Irsku kvůli cenzuře",
        "Obě mají ich-formu a rámcovou kompozici",
      ]),
      answer: "Klasicismus, 5 dějství, pravidlo tří jednot, Paříž, deus ex machina",
      explanation:
        "Lakomec je v próze, Tartuffe v alexandrínech. Jinak jsou to klasicistní komedie s 5 dějstvími a deus ex machina.",
    },
    {
      id: "x-tartuffe-verse",
      type: "mcq",
      bookId: 2,
      difficulty: 3,
      category: "zákeřné",
      prompt: "Které Molièrovo dílo je v alexandrínech?",
      options: shuffle(["Tartuffe", "Lakomec", "Noc na Karlštejně", "Revizor"]),
      answer: "Tartuffe",
      explanation: "Tartuffe = alexandríny AABB. Lakomec = próza.",
    },
    {
      id: "x-lakomec-prose",
      type: "mcq",
      bookId: 1,
      difficulty: 2,
      category: "zákeřné",
      prompt: "Lakomec je psán…",
      options: shuffle(["prózou", "alexandrínem", "osmislabičným veršem", "volným veršem"]),
      answer: "prózou",
      explanation: "Lakomec je próza. Alexandríny má Tartuffe.",
    },
    {
      id: "x-moliere-genre-split",
      type: "mcq",
      bookId: 1,
      difficulty: 2,
      category: "zákeřné",
      prompt: "Lakomec je charakterová komedie. Tartuffe je…",
      options: shuffle(["satirická komedie", "charakterová komedie taky", "tragédie", "veselohra o Karlu IV."]),
      answer: "satirická komedie",
      explanation: "Lakomec = charakterová (Harpagon). Tartuffe = satirická (pokrytectví, falešná zbožnost).",
    },
    {
      id: "x-moliere-harpagon",
      type: "mcq",
      bookId: 1,
      difficulty: 1,
      category: "postavy",
      prompt: "Harpagon je hlavní postava…",
      options: shuffle(["Lakomce", "Tartuffa", "Revizora", "Král Lávry"]),
      answer: "Lakomce",
      explanation: "Harpagon = lakomec. Tartuffe je pokrytec u Orgona.",
    },
    {
      id: "x-moliere-orgon",
      type: "mcq",
      bookId: 2,
      difficulty: 1,
      category: "postavy",
      prompt: "Orgon a Dorina patří do díla…",
      options: shuffle(["Tartuffe", "Lakomec", "Revizor", "Noc na Karlštejně"]),
      answer: "Tartuffe",
      explanation: "Orgon je zaslepený hospodář, Dorina hlas rozumu. V Lakomci je Harpagon, Kleant, Eliška.",
    },
    {
      id: "x-moliere-deus-who",
      type: "mcq",
      bookId: 2,
      difficulty: 3,
      category: "zákeřné",
      prompt: "Deus ex machina: příchod Anselma uzavírá ____, zásah krále uzavírá ____.",
      options: shuffle(["Lakomce ; Tartuffa", "Tartuffa ; Lakomce", "Revizora ; Lakomce", "Tartuffa ; Revizora"]),
      answer: "Lakomce ; Tartuffa",
      explanation: "Lakomec = Anselmo. Tartuffe = král. Revizor má otevřený závěr, ne deus ex machina.",
    },
    {
      id: "x-moliere-cover",
      type: "mcq",
      bookId: 2,
      difficulty: 2,
      category: "zákeřné",
      prompt: "Která Molièrova postava hraje zbožného, ale jde jí o majetek a svádění?",
      options: shuffle(["Tartuffe", "Harpagon", "Orgon", "Valér"]),
      answer: "Tartuffe",
      explanation: "Tartuffe = pokrytec. Harpagon = lakomec. Orgon = naivka, která Tartuffovi věří.",
    },
    {
      id: "x-deus",
      type: "mcq",
      difficulty: 3,
      category: "zákeřné",
      prompt: "Deus ex machina najdeš v závěru…",
      options: shuffle(["Lakomce i Tartuffa", "jen Revizora", "Krysaře", "Proměny"]),
      answer: "Lakomce i Tartuffa",
      explanation: "Lakomec: Anselmo. Tartuffe: zásah krále. Revizor má otevřený závěr s němým výjevem.",
    },
    {
      id: "x-revizor-end",
      type: "mcq",
      bookId: 5,
      difficulty: 2,
      category: "kompozice",
      prompt: "Jak končí Revizor?",
      options: shuffle([
        "Otevřený závěr — němá scéna, přijíždí pravý revizor",
        "Deus ex machina — zásah cara",
        "Svatební happy end",
        "Chlestakov je popraven",
      ]),
      answer: "Otevřený závěr — němá scéna, přijíždí pravý revizor",
      explanation: "Hejtman: „Čemu se smějete? Sami sobě se smějete!“",
    },
    {
      id: "x-robot",
      type: "mcq",
      bookId: 17,
      difficulty: 1,
      category: "autor",
      prompt: "Kdo vymyslel slovo robot?",
      options: shuffle(["Josef Čapek", "Karel Čapek", "Karel Hynek Mácha", "George Orwell"]),
      answer: "Josef Čapek",
      explanation: "Karel psal R.U.R., slovo poradil bratr Josef.",
    },
    {
      id: "x-budzes",
      type: "blank",
      bookId: 20,
      difficulty: 2,
      category: "tropy",
      prompt: "Hrdý Budžes je špatně pochopené… (doplň originální slova)",
      answer: "a hrdý buď, žes",
      aliases: ["hrdy bud zes", "a hrdy bud zes", "hrdý buď žes"],
      explanation: "Dětské komolení komunistické fráze „a hrdý buď, žes…“",
    },
    {
      id: "x-kulicka-mirror",
      type: "mcq",
      bookId: 4,
      difficulty: 2,
      category: "kompozice",
      prompt: "Zrcadlový kontrast v Kuličce znamená:",
      options: shuffle([
        "Na začátku hrdinka hostí všechny, na konci se s ní nikdo nerozdělí",
        "Děj začíná i končí u stejné tůně",
        "Vypravěč přijde do hospody a zase odejde",
        "Sedm přikázání se postupně přepisuje",
      ]),
      answer: "Na začátku hrdinka hostí všechny, na konci se s ní nikdo nerozdělí",
      explanation: "Kruhová tůň = O myších a lidech. Rámec hospody = Podkoní a žák. Přikázání = Farma zvířat.",
    },
    {
      id: "x-iceberg",
      type: "mcq",
      bookId: 11,
      difficulty: 2,
      category: "jazyk",
      prompt: "Metoda ledovce patří k dílu…",
      options: shuffle(["Stařec a moře", "Proměna", "Krysař", "Petr a Lucie"]),
      answer: "Stařec a moře",
      explanation: "Hemingway: úsporný styl, minimum adjektiv, čtení mezi řádky.",
    },
    {
      id: "x-circle",
      type: "mcq",
      bookId: 12,
      difficulty: 2,
      category: "kompozice",
      prompt: "Kruhová kompozice (začátek i konec u tůně) je v díle…",
      options: shuffle(["O myších a lidech", "Kulička", "Malý princ", "Král Lávra"]),
      answer: "O myších a lidech",
      explanation: "Steinbeck začíná i končí u stejné tůně tragickým završením.",
    },
    {
      id: "x-lavra-where",
      type: "mcq",
      bookId: 6,
      difficulty: 3,
      category: "zákeřné",
      prompt: "Proč se Král Lávra odehrává v Irsku?",
      options: shuffle([
        "Kvůli dobové cenzuře — myšleno je Rakousko",
        "Havlíček tam žil v exilu",
        "Jde o překlad irské hry",
        "Irsko bylo tehdy české území",
      ]),
      answer: "Kvůli dobové cenzuře — myšleno je Rakousko",
      explanation: "Lávra = alegorie Ferdinanda V. Dobrotivého. Havlíček šel do Brixenu, ne do Irska.",
    },
    {
      id: "x-kafka-burn",
      type: "mcq",
      bookId: 13,
      difficulty: 1,
      category: "autor",
      prompt: "Co si Kafka přál po smrti?",
      options: shuffle([
        "Aby Max Brod spálil jeho díla",
        "Aby Proměnu zfilmovali",
        "Aby byl pohřben v Paříži",
        "Aby rodina Samsových dostala tantiémy",
      ]),
      answer: "Aby Max Brod spálil jeho díla",
      explanation: "Brod to neudělal — a díky tomu čteš Proměnu.",
    },
    {
      id: "x-rur-genre",
      type: "mcq",
      bookId: 17,
      difficulty: 2,
      category: "žánr",
      prompt: "R.U.R. je…",
      options: shuffle([
        "Antiutopická sci-fi hra (drama)",
        "Antiutopická bajka (epika)",
        "Filozofická pohádka",
        "Absurdní povídka",
      ]),
      answer: "Antiutopická sci-fi hra (drama)",
      explanation: "Bajka = Farma zvířat. Pohádka = Malý princ. Absurdní povídka = Proměna.",
    },
    {
      id: "x-orwell-genre",
      type: "mcq",
      bookId: 14,
      difficulty: 2,
      category: "žánr",
      prompt: "Farma zvířat je žánrově…",
      options: shuffle([
        "Antiutopická bajka (alegorický román)",
        "Antiutopická sci-fi hra",
        "Satirická komedie",
        "Psychologická novela",
      ]),
      answer: "Antiutopická bajka (alegorický román)",
      explanation: "Alegorie SSSR: Napoleon = Stalin, Kuliš = Trockij, Boxer = dělník.",
    },
    {
      id: "x-lost-gen",
      type: "mcq",
      difficulty: 2,
      category: "kontext",
      prompt: "Který autor je hlavní tváří ztracené generace?",
      options: shuffle(["Ernest Hemingway", "Franz Kafka", "Karel Čapek", "Viktor Dyk"]),
      answer: "Ernest Hemingway",
      explanation: "Stařec a moře. Rolland se k ztracené generaci také řadí kontextem války, ale tváří je Hemingway.",
      bookId: 11,
    },
    {
      id: "x-podkoni-verse",
      type: "mcq",
      bookId: 3,
      difficulty: 2,
      category: "verš",
      prompt: "Podkoní a žák má verš…",
      options: shuffle([
        "staročeský osmislabičný se sdruženým rýmem",
        "alexandrín AABB",
        "nepravidelný verš, 34 strof po 7",
        "volný verš bez rýmu",
      ]),
      answer: "staročeský osmislabičný se sdruženým rýmem",
      explanation: "Alexandrín = Tartuffe. 34 strof = Král Lávra.",
    },
    {
      id: "x-green-mile-form",
      type: "mcq",
      bookId: 15,
      difficulty: 2,
      category: "vypravěč",
      prompt: "Zelenou míli vypráví…",
      options: shuffle([
        "Paul Edgecomb v ich-formě, retrospektivně",
        "vševědoucí er-forma bez hodnocení",
        "John Coffey vnitřním monologem",
        "osmileté dítě",
      ]),
      answer: "Paul Edgecomb v ich-formě, retrospektivně",
      explanation: "Rámec: stařec v domově důchodců vzpomíná na rok 1932.",
    },
    {
      id: "x-pavel-form",
      type: "mcq",
      bookId: 19,
      difficulty: 2,
      category: "žánr",
      prompt: "Smrt krásných srnců je…",
      options: shuffle([
        "autobiografický povídkový soubor (7 povídek)",
        "psychologická novela",
        "román s kruhovou kompozicí",
        "satirický spor",
      ]),
      answer: "autobiografický povídkový soubor (7 povídek)",
      explanation: "Spojuje je Ota a tatínek Leo Popper.",
    },
    {
      id: "x-karlstejn-myth",
      type: "mcq",
      bookId: 8,
      difficulty: 2,
      category: "kompozice",
      prompt: "Noc na Karlštejně stojí na…",
      options: shuffle([
        "historicky nepravdivé pověsti, že na hrad nesměly ženy",
        "skutečném zákazu Karla IV.",
        "irské pohádce o Midovi",
        "saské pověsti o krysaři",
      ]),
      answer: "historicky nepravdivé pověsti, že na hrad nesměly ženy",
      explanation: "3 dějství, historická komedie, lumírovci. Děj během jedné noci.",
    },
    {
      id: "x-which-drama",
      type: "mcq",
      difficulty: 2,
      category: "druh",
      prompt: "Které dílo NENÍ drama?",
      options: shuffle(["Krysař", "R.U.R.", "Revizor", "Noc na Karlštejně"]),
      answer: "Krysař",
      explanation: "Krysař je novela (epika). Drama: R.U.R., Revizor, Karlštejn, Lakomec, Tartuffe.",
      bookId: 16,
    },
    {
      id: "x-which-ich",
      type: "mcq",
      difficulty: 3,
      category: "vypravěč",
      prompt: "Které dílo NEMÁ ich-formu?",
      options: shuffle(["Kulička", "Malý princ", "Zelená míle", "Hrdý Budžes"]),
      answer: "Kulička",
      explanation: "Kulička = er-forma, objektivní vypravěč. Ich: Malý princ (letec), Zelená míle (Paul), Budžes (Helenka), Podkoní, Srnci.",
      bookId: 4,
    },
    {
      id: "x-lustig-escape",
      type: "mcq",
      bookId: 18,
      difficulty: 2,
      category: "autor",
      prompt: "Arnošt Lustig…",
      options: shuffle([
        "prošel koncentráky a z transportu smrti utekl skokem z vlaku",
        "bojoval ve Španělsku proti fašistům",
        "spálil druhý díl Mrtvých duší",
        "zemřel po představení Zdravého nemocného",
      ]),
      answer: "prošel koncentráky a z transportu smrti utekl skokem z vlaku",
      explanation: "Španělsko = Orwell. Spálené duše = Gogol. Zdravý nemocný = Molière.",
    },
    {
      id: "x-hemingway-quote",
      type: "blank",
      bookId: 11,
      difficulty: 2,
      category: "téma",
      prompt: "Doplň Hemingwayův citát: „Člověk není stvořen pro ____.“",
      answer: "porážku",
      aliases: ["porazku", "prohru"],
      explanation: "Nezlomnost vůle — i když ze žraloků zbude jen kostra.",
    },
    {
      id: "x-orwell-quote",
      type: "blank",
      bookId: 14,
      difficulty: 2,
      category: "téma",
      prompt: "Doplň: „Všichni jsou si rovni, někteří ____.“",
      answer: "rovnější",
      aliases: ["jsou si rovnejsi", "rovnejsi"],
      explanation: "Klíčová věta Farmy zvířat — zvrhnutí revoluce v totalitu.",
    },
    {
      id: "x-fox",
      type: "blank",
      bookId: 10,
      difficulty: 2,
      category: "tropy",
      prompt: "Doplň: „Správně vidíme jen ____.“ (Malý princ)",
      answer: "srdcem",
      aliases: ["srdcem", "srdce"],
      explanation: "Liška učí prince ochočení a dívání srdcem.",
    },
    {
      id: "x-gogol-laugh",
      type: "blank",
      bookId: 5,
      difficulty: 3,
      category: "postavy",
      prompt: "Doplň hejtmanův výrok: „Čemu se smějete? Sami ____ se smějete!“",
      answer: "sobě",
      aliases: ["sobe"],
      explanation: "Satira míří na diváky — a na ruskou společnost.",
    },
  ];

  qs.push(...extras.filter((q) => !answerInPrompt(q.prompt, q.answer)));
  return qs;
}

export const QUESTION_BANK: Question[] = buildBank();

export function questionsForBook(bookId: number, types?: QType[]) {
  return QUESTION_BANK.filter((q) => q.bookId === bookId && (!types || types.includes(q.type)));
}

export function mixedQuestions(opts: {
  count: number;
  bookIds?: number[];
  types?: QType[];
  preferIds?: string[];
  seed?: number;
}) {
  const { count, bookIds, types, preferIds = [] } = opts;
  let pool = QUESTION_BANK.filter((q) => {
    if (bookIds && q.bookId && !bookIds.includes(q.bookId)) return false;
    if (types && !types.includes(q.type)) return false;
    return true;
  });
  const preferred = pool.filter((q) => preferIds.includes(q.id));
  const rest = shuffle(pool.filter((q) => !preferIds.includes(q.id)));
  const picked: Question[] = [];
  for (const q of [...shuffle(preferred), ...rest]) {
    if (picked.length >= count) break;
    picked.push(q);
  }
  return picked;
}

export type MatchPair = { left: string; right: string; bookId: number };

export function matchRound(kind: "author" | "character" | "period" | "genre", n = 6): MatchPair[] {
  const used = new Set<string>();
  const pairs: MatchPair[] = [];
  for (const book of shuffle(BOOKS)) {
    const pair =
      kind === "author"
        ? { left: book.title, right: book.authorShort, bookId: book.id }
        : kind === "character"
          ? (() => {
              const c = usableCharacter(book);
              return c ? { left: c.name, right: book.title, bookId: book.id } : null;
            })()
          : kind === "period"
            ? { left: book.title, right: book.period, bookId: book.id }
            : kind === "genre"
              ? { left: book.title, right: book.genre, bookId: book.id }
              : null;
    if (!pair) continue;
    const key = `${pair.left}::${pair.right}`;
    if (used.has(pair.left) || used.has(pair.right) || used.has(key)) continue;
    used.add(pair.left);
    used.add(pair.right);
    pairs.push(pair);
    if (pairs.length >= n) break;
  }
  return pairs;
}

export const EXAMINER = {
  correct: [
    "Komise přikyvuje. Bod máš.",
    "To by na ústní prošlo. Bez červenání.",
    "Harpagon by ti kasičku nepůjčil, ale tuhle odpověď ano.",
    "Dorina by byla pyšná. Pokračuj.",
    "Přesně. Tohle je maturita, ne dohadování v krčmě.",
  ],
  wrong: [
    "Komise se tváří. Tohle by neprošlo.",
    "Molière se v hrobě otočil. Jinak.",
    "Záměna děl. Typická past. Zapamatuj si to.",
    "Ne. Teď si to pořádně přečti — a už to nespleť.",
    "Ústní by tady skončila. Pouč se z karty.",
  ],
  combo: [
    "Jsi v transu. Nerozbij to.",
    "Komise začíná být nervózní — v dobrém.",
    "Tohle už není hádání. Tohle je umění.",
  ],
};

export function examinerLine(ok: boolean, combo: number) {
  if (ok && combo >= 5) return pickN(EXAMINER.combo, 1)[0];
  return pickN(ok ? EXAMINER.correct : EXAMINER.wrong, 1)[0];
}
