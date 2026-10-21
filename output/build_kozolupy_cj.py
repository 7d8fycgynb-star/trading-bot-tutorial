#!/usr/bin/env python3
"""Build Czech PDF: Nabidka-Kozolupy-CJ (AN260377), EUR -> CZK."""

from __future__ import annotations

import io
import os

import fitz
from PIL import Image, ImageDraw

SRC = "/home/ubuntu/.cursor/projects/workspace/uploads/Nabidka-Kozolupy-DE_d754.pdf"
OUT = "/workspace/Nabidka-Kozolupy-CJ.pdf"
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
    "Angebot": "Nabídka",
    "Seite 1 von 6 19.10.2026": "Strana 1 z 6 19.10.2026",
    "Seite 2 von 6 19.10.2026": "Strana 2 z 6 19.10.2026",
    "Seite 3 von 6 19.10.2026": "Strana 3 z 6 19.10.2026",
    "Seite 4 von 6 19.10.2026": "Strana 4 z 6 19.10.2026",
    "Seite 5 von 6 19.10.2026": "Strana 5 z 6 19.10.2026",
    "Seite 6 von 6 19.10.2026": "Strana 6 z 6 19.10.2026",
    "Sehr geehrter": "Vážený",
    "Herr Shelemba,": "pane Shelembo,",
    "wir bedanken uns für Ihre Anfrage und unterbreiten Ihren Wünschen und Angaben entsprechend unser Angebot ":
        "děkujeme za Vaši poptávku a na základě Vašich přání a údajů Vám předkládáme naši nabídku ",
    "über Top-Qualitätsfenster des Profilgebers Deceuninck.":
        "na okna nejvyšší kvality od profilového dodavatele Deceuninck.",
    "Zukunftsorientierte Profilgestaltung unseres Systems Grando mit einer Bautiefe von 84 mm sowie einer 6-":
        "Moderní tvarování profilů našeho systému Grando se stavební hloubkou 84 mm a 6-",
    "Kammergestaltung bieten höchsten Wärmeschutz.":
        "komorovou konstrukcí zajišťuje nejvyšší tepelnou ochranu.",
    "Alle Fenster generell mit verzinktem Stahl sowie 3 grauen Dichtungen und dem Beschlag ROTO NX silberfarbig mit ":
        "Všechna okna standardně s pozinkovanou ocelí, 3 šedými těsněními a kováním ROTO NX ve stříbrné barvě se ",
    "Flügelheber, Fehlbedienungssperre, und Pilzzapfenverriegelung für optimale Grundsicherheit.":
        "zvedákem křídla, pojistkou proti chybné obsluze a hříbkovým uzavíráním pro základní bezpečnost.",
    "Darüberhinaus sind sämtliche Rolladenführungen serienmäßig mit Bürstendichtungen ausgestattet.":
        "Kromě toho jsou všechna vedení rolety sériově vybavena kartáčovým těsněním.",
    "Ein weiterer Vorteil ist die grundsätzliche Ausstattung aller Fenster mit Secustik Griffen für das hörbare Plus an ":
        "Další výhodou je standardní vybavení všech oken klikami Secustik pro slyšitelný plus na ",
    "Sicherheit.": "bezpečnosti.",
    "Gerne bieten wir wie folgt an:": "Rádi Vám nabízíme následující:",
    "System:": "Systém:",
    "Uf: 0,95 W/m²K Rahmen 84 und Flügel 84 mm Bautiefe, 6-Kammer-":
        "Uf: 0,95 W/m²K rám 84 a křídlo 84 mm stavební hloubka, 6-komorová ",
    "Technologie": "technologie",
    " Beidseitig Anthrazit glatt": " Oboustranně antracit hladký",
    "Glas": "Sklo",
    "Position": "Pozice",
    "Menge": "Množství",
    "Beschreibung": "Popis",
    "Preis": "Cena",
    "Preis * Stück": "Cena × ks",
    "1 Stück": "1 ks",
    "2 Stück": "2 ks",
    "3 Stück": "3 ks",
    "Serie:": "Série:",
    "System GRANDO MD 84": "Systém GRANDO MD 84",
    "System HST": "Systém HST",
    "Rahmen:": "Rám:",
    "Flügel:": "Křídlo:",
    "Pfosten:": "Sloupek:",
    "Farbe:": "Barva:",
    "Außen": "Exteriér ",
    "/ Innen": "/ Interiér",
    "Rahm.farbe:": "Barva rámu:",
    "023-Anthrazit glatt": "023-Antracit hladký ",
    "/ 023-Anthrazit glatt": "/ 023-Antracit hladký",
    "Flügelfarbe:": "Barva křídla: ",
    "Beschlag:": "Kování:",
    "Füllung:": "Výplň:",
    "Entwässer:": "Odvodnění:",
    "Entwässerung unten": "Odvodnění dole",
    "Entwässerung außen": "Odvodnění vně",
    "Ohne": "Bez",
    "Aufdoppl.:": "Nástavec:",
    "Aufdopplung                 /Lage": "Nástavec                      /Umístění",
    "/ unten": "/ dole",
    "Masse:": "Rozměry:",
    "USTP076 30mm Neubau": "USTP076 30mm novostavba",
    "05963-Aufdopplung 63/100-weiß-OV": "05963-Nástavec 63/100-bílý-OV",
    "Dummy für Aufdopplung KP40 Außen+Innen": "Maketa pro nástavec KP40 Exteriér+Interiér",
    "Dummy für Aufdopplung KP100 ": "Maketa pro nástavec KP100 ",
    "Außen+Innen": "Exteriér+Interiér",
    "LP284C + Schw.(SD)": "LP284C + práh (SD)",
    "HT Flügel HP484": "HT křídlo HP484",
    "Haustür   2AH Automatik SL RotoSil  45/92/8 ": "Vchodové dveře 2AH Automatik SL RotoSil 45/92/8 ",
    "16/3 Rechts": "16/3 vpravo",
    "DK Fenster P DM15 GSH Rechts": "DK okno P DM15 GSH vpravo",
    "D Fenster P zweitöffnend DM15 GSH Links, ": "D okno P druhé otvírání DM15 GSH vlevo, ",
    "DK Fenster P erstöffnend DM15 GSH ": "DK okno P první otvírání DM15 GSH ",
    "Rechts": "vpravo",
    "2 * FIB 84 Standard ohne Schwelle": "2 * FIB 84 Standard bez prahu",
    "05127-Pfosten/Kämpfer MD 84/94": "05127-Sloupek/příčka MD 84/94",
    "2 * Fixfeld": "2 * pevné pole",
    "Fixfeld": "Pevné pole",
    "Fixfeld, DK Tür P DM15 GSH Rechts": "Pevné pole, DK dveře P DM15 GSH vpravo",
    "FIB 84 Standard ohne Schwelle, ZP184C": "FIB 84 Standard bez prahu, ZP184C",
    "HS-Rahmen (A-R) mit HSB476": "HS-rám (A-R) s HSB476",
    "HS-Flügel (F) HS476 (A-HSB476), HS-": "HS-křídlo (F) HS476 (A-HSB476), HS-",
    "Flügel (FF) HS476 (HSB576)": "křídlo (FF) HS476 (HSB576)",
    "HAUTAU ATRIUM® HS -": "HAUTAU ATRIUM® HS -",
    "heben & schieben ": "zdvižně-posuvné ",
    "(links), HAUTAU  Festflügel": "(vlevo), HAUTAU pevné křídlo",
    "4/18/4/18/4, TGI-M/ schwarz (RAL 9005), ": "4/18/4/18/4, TGI-M/ černá (RAL 9005), ",
    "2 * 4/18/4/18/4, TGI-M/ schwarz (RAL 9005), ": "2 * 4/18/4/18/4, TGI-M/ černá (RAL 9005), ",
    "Ug: 0.50 W/m²K, 33 dB": "Ug: 0,50 W/m²K, 33 dB",
    "Mehrpreis Standarddekor beidsetig": "Příplatek standardní dekor oboustranně",
    "Mehrpreis Fensterbankanschluss 30mm": "Příplatek napojení na parapet 30 mm",
    "Mehrpreis 4-18-4-18-4 iplus Top 1.1-Pl. Cll.-iplus Top 1.1, ":
        "Příplatek 4-18-4-18-4 iplus Top 1.1-Pl. Cll.-iplus Top 1.1, ",
    "Mehrpreis TGI": "Příplatek TGI",
    "12,280 mMehrpreis TGI": "12,280 m Příplatek TGI",
    "13,440 mMehrpreis TGI": "13,440 m Příplatek TGI",
    "Mehrpreis Aufdopplung 100mm weiß": "Příplatek nástavec 100 mm bílý",
    "Mehrpreis Aufdopplung 100mm A+I": "Příplatek nástavec 100 mm E+I",
    "Mehrpreis Aufdopplung 40mm A+I": "Příplatek nástavec 40 mm E+I",
    "Mehrpreis Rahmen 84mm farbig": "Příplatek rám 84 mm barevný",
    "Mehrpreis Flügelsystem HP484 farbig": "Příplatek systém křídla HP484 barevný",
    "Mehrpreis Satinato 4mm": "Příplatek Satinato 4 mm",
    "Olive Rotoline Secustic EV1": "Klička Rotoline Secustic EV1",
    "Wechselgarnitur Hoppe Liége Knopf/Drücker EV1":
        "Výměnná garnitura Hoppe Liége knoflík/klička EV1",
    "BKS Profilzylinder mit Not-": "BKS profilová vložka s nouzovou ",
    "u. Gefahrenfunktion incl. ": "a bezpečnostní funkcí včetně ",
    "3Stck. Schlüssel": "3 ks klíčů",
    "Maß: 45/60 mm": "Rozměr: 45/60 mm",
    "Transport und Montage": "Doprava a montáž",
    "Übertrag:": "Přenos:",
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
    new = EXACT.get(text, text)
    if "EUR" in new:
        new = new.replace("EUR", "CZK")
    return new


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
                    draw.rectangle(
                        [
                            int((x0 - pad) * SCALE),
                            int((y0 - 0.5) * SCALE),
                            int((x1 + 1.5) * SCALE),
                            int((y1 + 0.8) * SCALE),
                        ],
                        fill=bg_for(raw, span, old, pi),
                    )

        buf = io.BytesIO()
        raw.convert("RGB").save(buf, format="JPEG", quality=92, optimize=True)
        new_page = out.new_page(width=PAGE_SIZE[0], height=PAGE_SIZE[1])
        new_page.insert_image(new_page.rect, stream=buf.getvalue())

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
        print(f"page {pi+1}: {len(jobs)} replacements")

    out.set_metadata(
        {
            "title": "Nabidka Kozolupy CJ AN260377",
            "author": "Opti-Tech-Okna s.r.o.",
            "subject": "Nabidka Kozolupy CJ",
            "creator": "Cursor Cloud Agent",
            "producer": "PyMuPDF",
        }
    )
    out.save(OUT, garbage=4, deflate=True, clean=True, pretty=True)
    print("Wrote", OUT, os.path.getsize(OUT))

    check = fitz.open(OUT)
    assert len(check) == 6
    text = "\n".join(p.get_text() for p in check)
    assert "Adresa zákazníka" in text
    assert "pane Shelembo" in text
    assert "Celková cena" in text
    assert "Jednatel" in text
    assert "CZK" in text
    assert "EUR" not in text
    assert "Kundenadresse" not in text
    assert "Geschäftsführer" not in text
    for i in range(6):
        check[i].get_pixmap(matrix=fitz.Matrix(0.25, 0.25))
    check.close()
    print("Verified", OUT)
    out.close()
    src.close()


if __name__ == "__main__":
    build()
