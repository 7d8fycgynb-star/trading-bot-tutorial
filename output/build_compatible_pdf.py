#!/usr/bin/env python3
"""Build a widely compatible Czech PDF (PyMuPDF only)."""

from __future__ import annotations

import fitz
from PIL import Image, ImageDraw, ImageFont
import os

SRC = "/home/ubuntu/.cursor/projects/workspace/uploads/Nabi_dka_Orac_ko_0e95.pdf"
OUT = "/workspace/Nabidka_Oracko_AN260350_CS.pdf"
OUT_ALT = "/workspace/AN260350-Oracko-nabidka-CZ.pdf"
DPI = 150
SCALE = DPI / 72.0
PAGE_SIZE = (612.0, 792.0)

FONT_REG = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
FONT_SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
FONT_SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
FONT_SERIF_BI = "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"
FONT_TAHOMA = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

EXACT = {
    "Kundenadresse:                            ": "Adresa zákazníka:                       ",
    "DEUTSCHLAND": "NĚMECKO",
    "Angebot:": "Nabídka:",
    "Bauvorhaben": "Stavební objekt",
    "Bearbeiter": "Zpracovatel",
    "E-Mail": "E-mail",
    "Datum                                      ": "Datum                                     ",
    "Position": "Pozice",
    "Menge": "Množství",
    "Beschreibung": "Popis",
    "Preis": "Cena",
    "Preis * Stück": "Cena × ks",
    "1 Stück": "1 ks",
    "2 Stück": "2 ks",
    "Serie:": "Série:",
    "System HST": "Systém HST",
    "Rahmen:": "Rám:",
    "HS-Rahmen (A-R) mit HSB476": "HS-rám (A-R) s HSB476",
    "Flügel:": "Křídlo:",
    "HS-Flügel (FF) HS476 (HSB576), HS-Flügel ": "HS-křídlo (FF) HS476 (HSB576), HS-křídlo ",
    "Farbe:": "Barva:",
    "Außen": "Exteriér ",
    "/ Innen": "/ Interiér",
    "Rahm.farbe:": "Barva rámu:",
    "023-Anthrazit glatt": "023-Antracit hladký ",
    "/ 023-Anthrazit glatt": "/ 023-Antracit hladký",
    "Flügelfarbe:": "Barva křídla: ",
    "Beschlag:": "Kování:",
    "HAUTAU  Festflügel, HAUTAU ATRIUM® ": "HAUTAU pevné křídlo, HAUTAU ATRIUM® ",
    "heben & schieben (rechts)": "zdvižně-posuvné (vpravo)",
    "Füllung:": "Výplň:",
    "2 * 4/18/4/18/4, TGI-M/ schwarz (RAL 9005), ": "2 * 4/18/4/18/4, TGI-M/ černá (RAL 9005), ",
    "Ug: 0.50 W/m²K, 33 dB": "Ug: 0,50 W/m²K, 33 dB",
    "Entwässer:": "Odvodnění:",
    "Entwässerung außen": "Odvodnění vně",
    "Aufdoppl.:": "Nástavec:",
    "Aufdopplung                 /Lage": "Nástavec                      /Umístění",
    "Dummy für Aufdopplung KP40 Außen+Innen": "Maketa pro nástavec KP40 Exteriér+Interiér",
    "/ unten": "/ dole",
    "Dummy für Aufdopplung KP100 ": "Maketa pro nástavec KP100 ",
    "Außen+Innen": "Exteriér+Interiér",
    "Masse:": "Rozměry:",
    "Mehrpreis Standarddekor beidsetig": "Příplatek standardní dekor oboustranně",
    "Mehrpreis Aufdopplung 100mm A+I": "Příplatek nástavec 100 mm E+I",
    "Mehrpreis Aufdopplung 40mm A+I": "Příplatek nástavec 40 mm E+I",
    "Mehrpreis 4-18-4-18-4 iplus Top 1.1-Pl. Cll.-iplus Top 1.1, ": "Příplatek 4-18-4-18-4 iplus Top 1.1-Pl. Cll.-iplus Top 1.1, ",
    "14,240 mMehrpreis TGI": "14,240 m Příplatek TGI",
    "12,840 mMehrpreis TGI": "12,840 m Příplatek TGI",
    "Übertrag:": "Přenos:",
    "Angebot": "Nabídka",
    "Seite 1 von 3 01.10.2026": "Strana 1 z 3 01.10.2026",
    "Seite 2 von 3 01.10.2026": "Strana 2 z 3 01.10.2026",
    "Seite 3 von 3 01.10.2026": "Strana 3 z 3 01.10.2026",
    "Summe der Positionen unrabattiert": "Součet pozic bez slevy",
    "Summe der Positionen": "Součet pozic",
    "Betrag ohne MwSt": "Částka bez DPH",
    "MwSt. 0%": "DPH 0 %",
    "Gesamtpreis": "Celková cena",
    "Konditionen": "Podmínky",
    ": Bei Zahlung innerhalb 7 Tagen 2 % Skonto": ": Při platbě do 7 dnů 2 % skonto",
    "20 Tage rein netto.": "20 dní čistě netto.",
    "Lieferung frei Haus": "Dodání franco dům",
    "Über Ihren Auftrag würden wir uns freuen, und sichern Ihnen schon jetzt eine fach-":
        "Budeme rádi za Vaši objednávku a již nyní Vám zajišťujeme odborné",
    "und termingerechte Ausführung ": "a termínové provedení.",
    "zu.": "",
    "Mit freundlichen Grüßen": "S přátelským pozdravem",
    "Geschäftsführer": "Jednatel",
    "(Preise verstehen sich bei geschlossener Abnahme der angebotenen Menge)":
        "(Ceny platí při odběru celého nabízeného množství)",
    "Ware bleibt bis zur vollständigen Bezahlung unser Eigentum!":
        "Zboží zůstává až do úplného zaplacení naším vlastnictvím!",
    "Angebotsgültigkeit": "Platnost nabídky",
    ": 4 Wochen ab Ausstellungsdatum": ": 4 týdny od data vystavení",
}


def translate(text: str) -> str:
    return EXACT.get(text, text)


def fontfile_for(name: str) -> str:
    fn = name.lower()
    if "times" in fn or "roman" in fn:
        if "bold" in fn and "italic" in fn:
            return FONT_SERIF_BI
        if "bold" in fn:
            return FONT_SERIF_B
        return FONT_SERIF
    if "tahoma" in fn:
        return FONT_TAHOMA
    if "bold" in fn:
        return FONT_BOLD
    return FONT_REG


def bg_for(raw: Image.Image, span: dict, old: str, page_index: int) -> tuple[int, int, int]:
    x0, y0, _, _ = span["bbox"]
    if "Kundenadresse" in old:
        return (192, 192, 192)
    if page_index == 0 and 274 <= span["origin"][1] <= 288:
        sx = min(max(int(50 * SCALE), 0), raw.width - 1)
        sy = min(max(int(278 * SCALE), 0), raw.height - 1)
        return raw.getpixel((sx, sy))
    sx = min(max(int(x0 * SCALE), 0), raw.width - 1)
    sy = min(max(int(max(y0 - 2, 0) * SCALE), 0), raw.height - 1)
    bg = raw.getpixel((sx, sy))
    if sum(bg) < 80:
        return (255, 255, 255)
    return bg


def build() -> None:
    src = fitz.open(SRC)
    out = fitz.open()
    font_cache: dict[str, fitz.Font] = {}

    for pi, page in enumerate(src):
        mat = fitz.Matrix(SCALE, SCALE)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        raw = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        draw = ImageDraw.Draw(raw)
        jobs: list[dict] = []

        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            for line in b["lines"]:
                for span in line["spans"]:
                    old = span["text"]
                    if not old or old.strip("\x00 ").strip() == "":
                        continue
                    new = translate(old)
                    if new == old:
                        continue
                    jobs.append({"span": span, "new": new, "old": old})
                    x0, y0, x1, y1 = span["bbox"]
                    pad = 1.2
                    rx0 = int((x0 - pad) * SCALE)
                    ry0 = int((y0 - 0.5) * SCALE)
                    rx1 = int((x1 + 1.5) * SCALE)
                    ry1 = int((y1 + 0.8) * SCALE)
                    draw.rectangle([rx0, ry0, rx1, ry1], fill=bg_for(raw, span, old, pi))

        jpeg = raw.convert("RGB")
        buf = __import__("io").BytesIO()
        jpeg.save(buf, format="JPEG", quality=92, optimize=True)
        jpeg_bytes = buf.getvalue()

        new_page = out.new_page(width=PAGE_SIZE[0], height=PAGE_SIZE[1])
        new_page.insert_image(new_page.rect, stream=jpeg_bytes)

        fn_counter = 0
        for j in jobs:
            if not j["new"]:
                continue
            sp = j["span"]
            ff = fontfile_for(sp["font"])
            fn_counter += 1
            white_header = pi == 0 and 274 <= sp["origin"][1] <= 288
            new_page.insert_text(
                sp["origin"],
                j["new"],
                fontsize=sp["size"],
                fontfile=ff,
                fontname=f"cz{pi}_{fn_counter}",
                color=(1, 1, 1) if white_header else (0, 0, 0),
            )

    meta = {
        "title": "Nabidka AN260350 Oracko (CZ)",
        "author": "Opti-Tech-Okna s.r.o.",
        "subject": "Nabidka",
        "creator": "Cursor Cloud Agent",
        "producer": "PyMuPDF",
    }
    out.set_metadata(meta)
    for path in (OUT, OUT_ALT):
        out.save(
            path,
            garbage=4,
            deflate=True,
            clean=True,
            pretty=True,
            no_new_id=False,
        )
        print("Wrote", path, os.path.getsize(path))

    # Sanity check
    for path in (OUT, OUT_ALT):
        check = fitz.open(path)
        assert len(check) == 3
        for i in range(3):
            check[i].get_pixmap(matrix=fitz.Matrix(0.3, 0.3))
        assert "Adresa zákazníka" in check[0].get_text()
        check.close()
    out.close()
    src.close()


if __name__ == "__main__":
    build()
