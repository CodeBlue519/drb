#!/usr/bin/env python3
"""
Scrape Haydock Catholic Bible Commentary from ecatholic2000.com
Outputs TSV: BookAbbrev\tChapter:Verse\tCommentary

Restartable: skips books/chapters already present in output file.
"""

import re
import time
import urllib.request
import html
import os
import sys
import json

BASE_URL = "https://www.ecatholic2000.com/haydock/"
OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "haydock.tsv")
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "haydock-progress.json")

# Delay between requests (seconds) - be polite
DELAY = 1.0

# Map from ecatholic2000 book names to DRB abbreviations
BOOK_ABBREV = {
    # OT
    "GENESIS": "Gn", "EXODUS": "Ex", "LEVITICUS": "Lv", "NUMBERS": "Nm",
    "DEUTERONOMY": "Dt", "JOSUE": "Jos", "JUDGES": "Jgs", "RUTH": "Ru",
    "1 KINGS": "1Sm", "2 KINGS": "2Sm", "3 KINGS": "1Kgs", "4 KINGS": "2Kgs",
    "1 PARALIPOMENON": "1Chr", "2 PARALIPOMENON": "2Chr",
    "1 ESDRAS": "Ezr", "2 ESDRAS": "Neh",
    "TOBIAS": "Tb", "JUDITH": "Jdt", "ESTHER": "Est",
    "JOB": "Jb", "PSALMS": "Ps", "PSALM": "Ps",
    "PROVERBS": "Prv", "ECCLESIASTES": "Eccl",
    "CANTICLE OF CANTICLES": "Sg", "WISDOM": "Wis",
    "ECCLESIASTICUS": "Sir",
    "ISAIAS": "Is", "JEREMIAS": "Jer", "LAMENTATIONS": "Lam",
    "BARUCH": "Bar", "EZECHIEL": "Ez", "DANIEL": "Dn",
    "OSEE": "Hos", "JOEL": "Jl", "AMOS": "Am", "ABDIAS": "Ob",
    "JONAS": "Jon", "MICHEAS": "Mi", "NAHUM": "Na",
    "HABACUC": "Hb", "SOPHONIAS": "Zep", "AGGEUS": "Hg",
    "ZACHARIAS": "Zec", "MALACHIAS": "Mal",
    "1 MACHABEES": "1Mc", "2 MACHABEES": "2Mc",
    # NT
    "MATTHEW": "Mt", "MARK": "Mk", "LUKE": "Lk", "JOHN": "Jn",
    "ACTS": "Acts", "ROMANS": "Rom",
    "1 CORINTHIANS": "1Cor", "2 CORINTHIANS": "2Cor",
    "GALATIANS": "Gal", "EPHESIANS": "Eph", "PHILIPPIANS": "Phil",
    "COLOSSIANS": "Col", "1 THESSALONIANS": "1Thes", "2 THESSALONIANS": "2Thes",
    "1 TIMOTHY": "1Tm", "2 TIMOTHY": "2Tm", "TITUS": "Ti",
    "PHILEMON": "Phlm", "HEBREWS": "Heb", "JAMES": "Jas",
    "1 PETER": "1Pt", "2 PETER": "2Pt",
    "1 JOHN": "1Jn", "2 JOHN": "2Jn", "3 JOHN": "3Jn",
    "JUDE": "Jude", "APOCALYPSE": "Apc",
}

# Complete chapter listing with URLs
# Format: (ecatholic_book_name, chapter_number, url_filename)
# NT first (higher priority), then OT

NT_CHAPTERS = []
# Matthew 1-28: ntcomment3..ntcomment30
for ch in range(1, 29):
    NT_CHAPTERS.append(("MATTHEW", ch, f"ntcomment{ch+2}.shtml"))
# Mark 1-16: ntcomment32..ntcomment47
for ch in range(1, 17):
    NT_CHAPTERS.append(("MARK", ch, f"ntcomment{ch+31}.shtml"))
# Luke 1-24: ntcomment49..ntcomment72
for ch in range(1, 25):
    NT_CHAPTERS.append(("LUKE", ch, f"ntcomment{ch+48}.shtml"))
# John 1-21: ntcomment74..ntcomment94
for ch in range(1, 22):
    NT_CHAPTERS.append(("JOHN", ch, f"ntcomment{ch+73}.shtml"))
# Acts 1-28: ntcomment96..ntcomment123
for ch in range(1, 29):
    NT_CHAPTERS.append(("ACTS", ch, f"ntcomment{ch+95}.shtml"))
# Romans 1-16: ntcomment125..ntcomment140
for ch in range(1, 17):
    NT_CHAPTERS.append(("ROMANS", ch, f"ntcomment{ch+124}.shtml"))
# 1 Cor 1-16: ntcomment142..ntcomment157
for ch in range(1, 17):
    NT_CHAPTERS.append(("1 CORINTHIANS", ch, f"ntcomment{ch+141}.shtml"))
# 2 Cor 1-13: ntcomment159..ntcomment171
for ch in range(1, 14):
    NT_CHAPTERS.append(("2 CORINTHIANS", ch, f"ntcomment{ch+158}.shtml"))
# Gal 1-6: ntcomment173..ntcomment178
for ch in range(1, 7):
    NT_CHAPTERS.append(("GALATIANS", ch, f"ntcomment{ch+172}.shtml"))
# Eph 1-6: ntcomment180..ntcomment185
for ch in range(1, 7):
    NT_CHAPTERS.append(("EPHESIANS", ch, f"ntcomment{ch+179}.shtml"))
# Phil 1-4: ntcomment187..ntcomment190
for ch in range(1, 5):
    NT_CHAPTERS.append(("PHILIPPIANS", ch, f"ntcomment{ch+186}.shtml"))
# Col 1-4: ntcomment192..ntcomment195
for ch in range(1, 5):
    NT_CHAPTERS.append(("COLOSSIANS", ch, f"ntcomment{ch+191}.shtml"))
# 1 Thes 1-5: ntcomment197..ntcomment201
for ch in range(1, 6):
    NT_CHAPTERS.append(("1 THESSALONIANS", ch, f"ntcomment{ch+196}.shtml"))
# 2 Thes 1-3: ntcomment203..ntcomment205
for ch in range(1, 4):
    NT_CHAPTERS.append(("2 THESSALONIANS", ch, f"ntcomment{ch+202}.shtml"))
# 1 Tim 1-6: ntcomment207..ntcomment212
for ch in range(1, 7):
    NT_CHAPTERS.append(("1 TIMOTHY", ch, f"ntcomment{ch+206}.shtml"))
# 2 Tim 1-4: ntcomment214..ntcomment217
for ch in range(1, 5):
    NT_CHAPTERS.append(("2 TIMOTHY", ch, f"ntcomment{ch+213}.shtml"))
# Titus 1-3: ntcomment219..ntcomment221
for ch in range(1, 4):
    NT_CHAPTERS.append(("TITUS", ch, f"ntcomment{ch+218}.shtml"))
# Philemon 1: ntcomment223
NT_CHAPTERS.append(("PHILEMON", 1, "ntcomment223.shtml"))
# Hebrews 1-13: ntcomment225..ntcomment237
for ch in range(1, 14):
    NT_CHAPTERS.append(("HEBREWS", ch, f"ntcomment{ch+224}.shtml"))
# James 1-5: ntcomment239..ntcomment243
for ch in range(1, 6):
    NT_CHAPTERS.append(("JAMES", ch, f"ntcomment{ch+238}.shtml"))
# 1 Peter 1-5: ntcomment245..ntcomment249
for ch in range(1, 6):
    NT_CHAPTERS.append(("1 PETER", ch, f"ntcomment{ch+244}.shtml"))
# 2 Peter 1-3: ntcomment251..ntcomment253
for ch in range(1, 4):
    NT_CHAPTERS.append(("2 PETER", ch, f"ntcomment{ch+250}.shtml"))
# 1 John 1-5: ntcomment255..ntcomment259
for ch in range(1, 6):
    NT_CHAPTERS.append(("1 JOHN", ch, f"ntcomment{ch+254}.shtml"))
# 2 John 1: ntcomment261
NT_CHAPTERS.append(("2 JOHN", 1, "ntcomment261.shtml"))
# 3 John 1: ntcomment263
NT_CHAPTERS.append(("3 JOHN", 1, "ntcomment263.shtml"))
# Jude 1: ntcomment265
NT_CHAPTERS.append(("JUDE", 1, "ntcomment265.shtml"))
# Apocalypse 1-22: ntcomment267..ntcomment288
for ch in range(1, 23):
    NT_CHAPTERS.append(("APOCALYPSE", ch, f"ntcomment{ch+266}.shtml"))

# OT chapters - using the untitled-NN.shtml pattern from TOC
OT_CHAPTERS = []
# Genesis 1-50: untitled-03..untitled-52
for ch in range(1, 51):
    OT_CHAPTERS.append(("GENESIS", ch, f"untitled-{ch+2:02d}.shtml"))
# Exodus 1-40: untitled-55..untitled-94
for ch in range(1, 41):
    OT_CHAPTERS.append(("EXODUS", ch, f"untitled-{ch+54}.shtml"))
# Leviticus 1-27: untitled-97..untitled-123
for ch in range(1, 28):
    OT_CHAPTERS.append(("LEVITICUS", ch, f"untitled-{ch+96}.shtml"))
# Numbers 1-36: untitled-126..untitled-161
for ch in range(1, 37):
    OT_CHAPTERS.append(("NUMBERS", ch, f"untitled-{ch+125}.shtml"))
# Deuteronomy 1-34: untitled-165..untitled-198
for ch in range(1, 35):
    OT_CHAPTERS.append(("DEUTERONOMY", ch, f"untitled-{ch+164}.shtml"))
# Josue 1-24: untitled-202..untitled-225
for ch in range(1, 25):
    OT_CHAPTERS.append(("JOSUE", ch, f"untitled-{ch+201}.shtml"))
# Judges 1-21: untitled-229..untitled-249
for ch in range(1, 22):
    OT_CHAPTERS.append(("JUDGES", ch, f"untitled-{ch+228}.shtml"))
# Ruth 1-4: untitled-252..untitled-255
for ch in range(1, 5):
    OT_CHAPTERS.append(("RUTH", ch, f"untitled-{ch+251}.shtml"))
# 1 Kings (1 Samuel) 1-31: untitled-261..untitled-290 (with 1-kings-7.shtml for ch 7)
for ch in range(1, 32):
    if ch == 7:
        OT_CHAPTERS.append(("1 KINGS", ch, "1-kings-7.shtml"))
    elif ch <= 6:
        OT_CHAPTERS.append(("1 KINGS", ch, f"untitled-{ch+260}.shtml"))
    else:
        # ch 8 = untitled-267, ch 9 = untitled-268, etc.
        OT_CHAPTERS.append(("1 KINGS", ch, f"untitled-{ch+259}.shtml"))
# 2 Kings (2 Samuel) 1-24: untitled-296..untitled-319
for ch in range(1, 25):
    OT_CHAPTERS.append(("2 KINGS", ch, f"untitled-{ch+295}.shtml"))
# 3 Kings (1 Kings) 1-22: untitled-323..untitled-344
for ch in range(1, 23):
    OT_CHAPTERS.append(("3 KINGS", ch, f"untitled-{ch+322}.shtml"))
# 4 Kings (2 Kings) 1-25: untitled-348..untitled-372
for ch in range(1, 26):
    OT_CHAPTERS.append(("4 KINGS", ch, f"untitled-{ch+347}.shtml"))
# 1 Paralipomenon 1-29: untitled-376..untitled-404
for ch in range(1, 30):
    OT_CHAPTERS.append(("1 PARALIPOMENON", ch, f"untitled-{ch+375}.shtml"))
# 2 Paralipomenon 1-36: untitled-408..untitled-442 (note: ch 31 missing from TOC, jumps to 32)
for ch in range(1, 37):
    if ch <= 30:
        OT_CHAPTERS.append(("2 PARALIPOMENON", ch, f"untitled-{ch+407}.shtml"))
    else:
        # ch 32 = untitled-438, ch 33 = untitled-439, ...
        OT_CHAPTERS.append(("2 PARALIPOMENON", ch, f"untitled-{ch+406}.shtml"))
# 1 Esdras 1-10: untitled-446..untitled-455
for ch in range(1, 11):
    OT_CHAPTERS.append(("1 ESDRAS", ch, f"untitled-{ch+445}.shtml"))
# 2 Esdras 1-13: untitled-460..untitled-472
for ch in range(1, 14):
    OT_CHAPTERS.append(("2 ESDRAS", ch, f"untitled-{ch+459}.shtml"))
# Tobias 1-14: untitled-477..untitled-490
for ch in range(1, 15):
    OT_CHAPTERS.append(("TOBIAS", ch, f"untitled-{ch+476}.shtml"))
# Judith 1-16: untitled-494..untitled-509
for ch in range(1, 17):
    OT_CHAPTERS.append(("JUDITH", ch, f"untitled-{ch+493}.shtml"))
# Esther 1-16: untitled-513..untitled-528
for ch in range(1, 17):
    OT_CHAPTERS.append(("ESTHER", ch, f"untitled-{ch+512}.shtml"))
# Job 1-42: untitled-532..untitled-573
for ch in range(1, 43):
    OT_CHAPTERS.append(("JOB", ch, f"untitled-{ch+531}.shtml"))
# Psalms 1-150: untitled-577..untitled-726
for ch in range(1, 151):
    OT_CHAPTERS.append(("PSALM", ch, f"untitled-{ch+576}.shtml"))
# Proverbs 1-31: untitled-730..untitled-760
for ch in range(1, 32):
    OT_CHAPTERS.append(("PROVERBS", ch, f"untitled-{ch+729}.shtml"))
# Ecclesiastes 1-12: untitled-764..untitled-775
for ch in range(1, 13):
    OT_CHAPTERS.append(("ECCLESIASTES", ch, f"untitled-{ch+763}.shtml"))
# Canticle of Canticles 1-8: untitled-779..untitled-786
for ch in range(1, 9):
    OT_CHAPTERS.append(("CANTICLE OF CANTICLES", ch, f"untitled-{ch+778}.shtml"))
# Wisdom 1-19: untitled-790..untitled-808
for ch in range(1, 20):
    OT_CHAPTERS.append(("WISDOM", ch, f"untitled-{ch+789}.shtml"))
# Ecclesiasticus 1-51: untitled-812..untitled-861 (note: ch 10 missing from site, jumps 11)
for ch in range(1, 52):
    if ch <= 9:
        OT_CHAPTERS.append(("ECCLESIASTICUS", ch, f"untitled-{ch+811}.shtml"))
    else:
        # ch 11 = untitled-821, so offset is ch+810
        OT_CHAPTERS.append(("ECCLESIASTICUS", ch, f"untitled-{ch+810}.shtml"))
# Isaias 1-66: untitled-866..untitled-931 (ch 2 = untitled-867)
for ch in range(1, 67):
    OT_CHAPTERS.append(("ISAIAS", ch, f"untitled-{ch+865}.shtml"))
# Jeremias 1-52: untitled-935..untitled-986
for ch in range(1, 53):
    OT_CHAPTERS.append(("JEREMIAS", ch, f"untitled-{ch+934}.shtml"))
# Lamentations 1-5: untitled-990..untitled-994
for ch in range(1, 6):
    OT_CHAPTERS.append(("LAMENTATIONS", ch, f"untitled-{ch+989}.shtml"))
# Baruch 1-6: untitled-998..untitled-1003
for ch in range(1, 7):
    OT_CHAPTERS.append(("BARUCH", ch, f"untitled-{ch+997}.shtml"))
# Ezechiel 1-48: untitled-1007..untitled-1054
for ch in range(1, 49):
    OT_CHAPTERS.append(("EZECHIEL", ch, f"untitled-{ch+1006}.shtml"))
# Daniel 1-14: untitled-1058..untitled-1071
for ch in range(1, 15):
    OT_CHAPTERS.append(("DANIEL", ch, f"untitled-{ch+1057}.shtml"))
# Osee 1-14: untitled-1075..untitled-1088
for ch in range(1, 15):
    OT_CHAPTERS.append(("OSEE", ch, f"untitled-{ch+1074}.shtml"))
# Joel 1-3: untitled-1092..untitled-1094
for ch in range(1, 4):
    OT_CHAPTERS.append(("JOEL", ch, f"untitled-{ch+1091}.shtml"))
# Amos 1-9: untitled-1098..untitled-1106
for ch in range(1, 10):
    OT_CHAPTERS.append(("AMOS", ch, f"untitled-{ch+1097}.shtml"))
# Abdias 1: untitled-1110
OT_CHAPTERS.append(("ABDIAS", 1, "untitled-1110.shtml"))
# Jonas 1-4: untitled-1114..untitled-1117
for ch in range(1, 5):
    OT_CHAPTERS.append(("JONAS", ch, f"untitled-{ch+1113}.shtml"))
# Micheas 1-7: untitled-1121..untitled-1127
for ch in range(1, 8):
    OT_CHAPTERS.append(("MICHEAS", ch, f"untitled-{ch+1120}.shtml"))
# Nahum 1-3: untitled-1131..untitled-1133
for ch in range(1, 4):
    OT_CHAPTERS.append(("NAHUM", ch, f"untitled-{ch+1130}.shtml"))
# Habacuc 1-3: untitled-1137..untitled-1139
for ch in range(1, 4):
    OT_CHAPTERS.append(("HABACUC", ch, f"untitled-{ch+1136}.shtml"))
# Sophonias 1-3: untitled-1143..untitled-1145
for ch in range(1, 4):
    OT_CHAPTERS.append(("SOPHONIAS", ch, f"untitled-{ch+1142}.shtml"))
# Aggeus 1-2: untitled-1149..untitled-1150
for ch in range(1, 3):
    OT_CHAPTERS.append(("AGGEUS", ch, f"untitled-{ch+1148}.shtml"))
# Zacharias 1-14: untitled-1154..untitled-1167
for ch in range(1, 15):
    OT_CHAPTERS.append(("ZACHARIAS", ch, f"untitled-{ch+1153}.shtml"))
# Malachias 1-4: untitled-1171..untitled-1174
for ch in range(1, 5):
    OT_CHAPTERS.append(("MALACHIAS", ch, f"untitled-{ch+1170}.shtml"))
# 1 Machabees 1-16: untitled-1178..untitled-1193
for ch in range(1, 17):
    OT_CHAPTERS.append(("1 MACHABEES", ch, f"untitled-{ch+1177}.shtml"))
# 2 Machabees 1-15: untitled-1197..untitled-1211
for ch in range(1, 16):
    OT_CHAPTERS.append(("2 MACHABEES", ch, f"untitled-{ch+1196}.shtml"))

ALL_CHAPTERS = NT_CHAPTERS + OT_CHAPTERS


def strip_html(text):
    """Remove HTML tags and decode entities."""
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def fetch_page(url):
    """Fetch a page and return its text content."""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Haydock Commentary Scraper for personal Catholic study)'
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.read().decode('utf-8', errors='replace')
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}", file=sys.stderr)
        return None


def parse_commentary(html_text, book_name, chapter):
    """Parse verse commentary from HTML page.
    Returns list of (verse_num, commentary_text) tuples.
    """
    if not html_text:
        return []

    # Strip to body content
    body = html_text
    # Remove script/style tags
    body = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', body, flags=re.DOTALL|re.IGNORECASE)

    # Convert to text
    text = strip_html(body)

    results = []

    # Pattern: "Ver. N." or "Ver. N-M." at the start of commentary blocks
    # Also handle "Ver. N," and combined verse references
    parts = re.split(r'(?=Ver\.\s+\d+)', text)

    for part in parts:
        # Match verse number(s)
        m = re.match(r'Ver\.\s+(\d+)(?:\s*[-,&]\s*\d+)*\.?\s*(.*)', part, re.DOTALL)
        if not m:
            continue
        verse = int(m.group(1))
        commentary = m.group(2).strip()

        # Clean up commentary
        # Remove trailing navigation/footer text
        commentary = re.sub(r'(?:Previous|Next|Top)\s*$', '', commentary).strip()
        # Remove multiple spaces
        commentary = re.sub(r'\s+', ' ', commentary).strip()

        if commentary and len(commentary) > 5:
            results.append((verse, commentary))

    return results


def load_progress():
    """Load progress to know which chapters are done."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return set(json.load(f))
    return set()


def save_progress(done):
    """Save progress."""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(sorted(done), f)


def main():
    done = load_progress()

    # Open output file in append mode
    file_exists = os.path.exists(OUTPUT_FILE) and os.path.getsize(OUTPUT_FILE) > 0
    outf = open(OUTPUT_FILE, 'a', encoding='utf-8')

    total = len(ALL_CHAPTERS)
    for i, (book_name, chapter, filename) in enumerate(ALL_CHAPTERS):
        key = f"{book_name}:{chapter}"
        abbrev = BOOK_ABBREV.get(book_name)
        if not abbrev:
            print(f"  SKIP unknown book: {book_name}", file=sys.stderr)
            continue

        if key in done:
            continue

        url = BASE_URL + filename
        print(f"[{i+1}/{total}] {abbrev} {chapter} ({url})")

        page = fetch_page(url)
        if page is None:
            print(f"  Failed to fetch, skipping", file=sys.stderr)
            continue

        verses = parse_commentary(page, book_name, chapter)
        if not verses:
            print(f"  WARNING: No verses found for {book_name} {chapter}", file=sys.stderr)

        for verse, commentary in verses:
            # Escape tabs and newlines in commentary
            clean = commentary.replace('\t', ' ').replace('\n', ' ').replace('\r', '')
            outf.write(f"{abbrev}\t{chapter}:{verse}\t{clean}\n")

        outf.flush()
        done.add(key)
        save_progress(done)

        time.sleep(DELAY)

    outf.close()
    print(f"\nDone! Output: {OUTPUT_FILE}")
    print(f"Total chapters processed: {len(done)}")


if __name__ == "__main__":
    main()
