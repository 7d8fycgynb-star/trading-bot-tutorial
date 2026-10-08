#!/usr/bin/env python3
"""Recreate the Opti-Tech quote PDF in Czech using exact original coordinates."""

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import Color, black, white, HexColor
import fitz

pdfmetrics.registerFont(TTFont("Sans", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Bold", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Serif", "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Serif-Bold", "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Serif-BI", "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf"))
pdfmetrics.registerFont(TTFont("TahomaLike", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))

SRC = "/home/ubuntu/.cursor/projects/workspace/uploads/Nabi_dka_Orac_ko_0e95.pdf"
OUT = "/workspace/output/Nabidka_Oracko_AN260350_CS.pdf"
LOGO = "/workspace/output/logo.png"
SCHEMA1 = "/workspace/output/schema1.png"
SCHEMA2 = "/workspace/output/schema2.png"

PAGE_W, PAGE_H = 612.0, 792.0

# Exact span text -> Czech (full span match first, then substring)
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
    if text in EXACT:
        return EXACT[text]
    return text


def font_name(font: str) -> str:
    fn = font.lower()
    if "times" in fn or "roman" in fn:
        if "bold" in fn and "italic" in fn:
            return "Serif-BI"
        if "bold" in fn:
            return "Serif-Bold"
        return "Serif"
    if "tahoma" in fn:
        return "TahomaLike"
    if "bold" in fn:
        return "Sans-Bold"
    return "Sans"


def draw_decorative(c, page_index, src_page):
    """Replay important filled rects / lines from original drawings (approx)."""
    if page_index == 0:
        # Customer address gray label background
        c.setFillColor(Color(0.753, 0.753, 0.753))
        c.rect(42.46, PAGE_H - 172.71, 155.8, 11.5, fill=1, stroke=0)
        c.setStrokeColor(black)
        c.setLineWidth(0.7)
        c.line(42.46, PAGE_H - 173.2, 120.5, PAGE_H - 173.2)
        # Contact header row: medium gray (headers only), black text
        c.setFillColor(Color(0.75, 0.75, 0.75))
        c.rect(42.46, PAGE_H - 286.5, 510.0, 12.5, fill=1, stroke=0)
        # Underline under "Stavební objekt"
        c.setStrokeColor(black)
        c.setLineWidth(0.6)
        c.line(42.46, PAGE_H - 262.5, 115.0, PAGE_H - 262.5)

    # Table header rules
    header_ys = {0: 351.53, 1: 40.00}
    if page_index in header_ys:
        by = header_ys[page_index]
        top = by - 11.5
        bot = by + 5.0
        c.setStrokeColor(black)
        c.setLineWidth(0.4)
        for x0, x1 in [(42.5, 178.5), (178.5, 255.0), (255.0, 396.7), (410.8, 481.6), (481.7, 552.5)]:
            c.line(x0, PAGE_H - top, x1, PAGE_H - top)
            c.line(x0, PAGE_H - bot, x1, PAGE_H - bot)


def build():
    src = fitz.open(SRC)
    c = canvas.Canvas(OUT, pagesize=(PAGE_W, PAGE_H))

    schemas = {0: SCHEMA1, 1: SCHEMA2}

    for page_index, page in enumerate(src):
        # Images
        for info in page.get_image_info(xrefs=True):
            xref = info["xref"]
            bbox = info["bbox"]  # x0,y0,x1,y1 top-origin
            x0, y0, x1, y1 = bbox
            w, h = x1 - x0, y1 - y0
            # Map xref to file
            if xref == 3:
                path = LOGO
            elif xref in (35, 44):
                path = schemas.get(page_index, SCHEMA1)
            else:
                # extract on the fly
                pix = fitz.Pixmap(src, xref)
                path = f"/tmp/img_{xref}.png"
                pix.save(path)
            c.drawImage(ImageReader(path), x0, PAGE_H - y1, width=w, height=h,
                        preserveAspectRatio=True, mask="auto")

        draw_decorative(c, page_index, page)

        # Text spans
        for b in page.get_text("dict")["blocks"]:
            if b.get("type") != 0:
                continue
            for line in b["lines"]:
                for span in line["spans"]:
                    text = span["text"]
                    if not text or text.strip("\x00") == "" or text.strip("\x00 ") == "":
                        continue
                    if text in ("\x00 ", "\x00"):
                        continue
                    new = translate(text)
                    if not new:
                        continue
                    # Skip pure spacer runs of spaces that only pad layout
                    ox, oy = span["origin"]
                    size = span["size"]
                    fname = font_name(span["font"])
                    c.setFillColor(black)
                    c.setFont(fname, size)
                    # reportlab y is baseline from bottom; pymupdf origin y is baseline from top
                    c.drawString(ox, PAGE_H - oy, new)

        c.showPage()

    c.save()
    print("Wrote", OUT)


if __name__ == "__main__":
    build()
