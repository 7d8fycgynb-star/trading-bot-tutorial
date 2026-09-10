# KOMISE — maturitní četba

## Otevři a uč se

1. **Stáhni `komise.html` a otevři v prohlížeči** (nic instalovat nemusíš).
   Na GitHubu otevři [komise.html](https://github.com/7d8fycgynb-star/trading-bot-tutorial/blob/cursor/maturita-cetba-app-9c97/komise.html) a klepni **Download raw file**. Ulož na plochu a otevři dvojklikem.
2. **Nebo spusť online ve StackBlitzu** (první načtení chvíli trvá):
   https://stackblitz.com/github/7d8fycgynb-star/trading-bot-tutorial/tree/cursor/maturita-cetba-app-9c97

Aplikace na učení 20 děl ze seznamu maturitní četby. Má být zábavná, ať u toho neusneš, a zároveň tě pořádně přezkoušet: kvízy, doplňovačky, párování, ústní u komise a opakování chyb.

Obsah vychází z rozborů `maturitni_rozbory_komplet_v5.pdf` (Molière až Dousková).

## Vývoj u sebe

```bash
npm install
npm run dev
```

Otevři URL, kterou vypíše Vite (obvykle http://localhost:5173).

```bash
npm run build
npm run preview
npm run standalone   # vyrobí komise.html
```

## Jak se učit

1. **Karty** — klepni na dílo → Učit. Odhaluj části I / II / III a kontext, jak u maturity.
2. **Kvíz díla** — 12 otázek jen z toho textu.
3. **Dnešní sprint** — mix všech děl, 18 s na otázku, po chybě vysvětlení.
4. **Blitz** — ještě rychlejší, ať neztrácíš pozornost.
5. **Párování** — autor, postava, směr, žánr.
6. **Ústní u komise** — píšeš odpověď, bodují se klíčová slova, pak vzor.
7. **Slabiny** — jen otázky, které jsi pokazil.
8. **Survival** — tři životy, combo násobí XP.

Postup (XP, streak, mistrovství děl, achievementy) se ukládá v prohlížeči do `localStorage`.

Klávesy `1–4` v kvízu volí odpověď.
