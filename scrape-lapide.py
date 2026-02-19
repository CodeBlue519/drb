#!/usr/bin/env python3
"""
Scrape Cornelius à Lapide's Great Commentary from Archive.org OCR text
and structure it as TSV: BookAbbrev\tChapter:Verse\tCommentary

The English translation covers:
  V1: Matthew 1-9     V2: Matthew 10-21    V3: Matthew 22-28 + Mark
  V4: Luke             V5: John 1-11        V6: John 12-21 + 1-3 John
  V7: 1 Corinthians    V8: 2 Corinthians + Galatians

Usage:
  python3 scrape-lapide.py              # Download and parse all volumes
  python3 scrape-lapide.py --resume     # Resume from last completed volume
  python3 scrape-lapide.py --volume 3   # Process only volume 3
  python3 scrape-lapide.py --parse-only # Skip download, just parse cached files
"""

import os
import re
import sys
import json
import time
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
CACHE_DIR = SCRIPT_DIR / "lapide-cache"
STATE_FILE = CACHE_DIR / "state.json"
OUTPUT_FILE = SCRIPT_DIR / "lapide.tsv"

# Volume definitions: (archive_id, [(book_abbrev, start_chapter, end_chapter), ...])
VOLUMES = {
    1: ("TheGreatCommentaryOfCorneliusALapideV1", [("Mt", 1, 9)]),
    2: ("TheGreatCommentaryOfCorneliusALapideV2", [("Mt", 10, 21)]),
    3: ("TheGreatCommentaryOfCorneliusALapideV3", [("Mt", 22, 28), ("Mk", 1, 16)]),
    4: ("TheGreatCommentaryOfCorneliusALapideV4", [("Lk", 1, 24)]),
    5: ("TheGreatCommentaryOfCorneliusALapideV5", [("Jn", 1, 11)]),
    6: ("TheGreatCommentaryOfCorneliusALapideV6", [("Jn", 12, 21), ("1Jn", 1, 5), ("2Jn", 1, 1), ("3Jn", 1, 1)]),
    7: ("TheGreatCommentaryOfCorneliusALapideV7", [("1Cor", 1, 16)]),
    8: ("TheGreatCommentaryOfCorneliusALapideV8", [("2Cor", 1, 13), ("Gal", 1, 6)]),
}


def download_volume(vol_num):
    """Download OCR text for a volume from Archive.org."""
    CACHE_DIR.mkdir(exist_ok=True)
    archive_id = VOLUMES[vol_num][0]
    cache_file = CACHE_DIR / f"v{vol_num}.txt"

    if cache_file.exists() and cache_file.stat().st_size > 1000:
        print(f"  V{vol_num}: Using cached file ({cache_file.stat().st_size:,} bytes)")
        return cache_file

    url = f"https://archive.org/download/{archive_id}/{archive_id}_djvu.txt"
    print(f"  V{vol_num}: Downloading from {url}...")

    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (DRB Bible App Commentary Scraper)'})
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        cache_file.write_bytes(data)
        print(f"  V{vol_num}: Downloaded {len(data):,} bytes")
        time.sleep(2)  # Be polite to archive.org
        return cache_file
    except Exception as e:
        print(f"  V{vol_num}: Download failed: {e}")
        return None


def parse_volume(vol_num, text):
    """Parse a volume's OCR text into (book, chapter, verse, commentary) tuples.
    
    Strategy: The OCR text has these patterns:
    - Chapter headers on their own line: "CHAPTER I." or "CHAPTER XXII." 
      (but OCR often mangles these, e.g., "CHAPTER L" for "CHAPTER I.")
    - Verse commentary markers: "Ver. N .—" or "Verses N, N.—" at start of line
    - The chapters appear sequentially, so we track expected chapter numbers
    """
    books_info = VOLUMES[vol_num][1]
    results = []

    # Build a flat sequence of (book, chapter) we expect to encounter
    expected_chapters = []
    for book, start_ch, end_ch in books_info:
        for ch in range(start_ch, end_ch + 1):
            expected_chapters.append((book, ch))

    chapter_idx = 0  # Index into expected_chapters
    current_book = expected_chapters[0][0]
    current_chapter = expected_chapters[0][1]
    current_verse = 0
    current_commentary = []

    # Chapter header pattern - very loose because OCR mangles Roman numerals
    # We look for "CHAPTER" at the start of a line, then advance to next expected chapter
    chapter_pat = re.compile(r'^\s*CHAPTER\s', re.IGNORECASE)

    # Verse patterns - from strict to loose
    # "Ver. 1.—" or "Ver. 1 .—" or "Verses 17, 18.—"
    verse_pat = re.compile(
        r'^\s*Ver(?:se)?s?\.?\s+(\d+)\s*(?:[,&]\s*\d+)?\s*[.,]?\s*[—\-]',
        re.IGNORECASE
    )
    # Looser: "Ver. 1." or "Ver. 1 . Then" — just needs "Ver. N" at start
    verse_pat2 = re.compile(
        r'^\s*Ver(?:se)?s?\.?\s+(\d+)\s*[.,]?\s',
        re.IGNORECASE
    )

    # For multi-book volumes, detect book transitions
    book_markers = {}
    if len(books_info) > 1:
        # Build markers that appear BEFORE the first chapter of each subsequent book
        for i, (book, start_ch, end_ch) in enumerate(books_info[1:], 1):
            if book == "Mk":
                book_markers[book] = re.compile(r"MARK['']?S\s+GOSPEL|ACCORDING\s+TO\s+(?:S\.\s*)?MARK", re.IGNORECASE)
            elif book == "1Jn":
                book_markers[book] = re.compile(r"FIRST\s+EPISTLE.*JOHN|EPISTLE.*(?:I|1)\s*(?:OF|,)\s*(?:S\.\s*)?JOHN", re.IGNORECASE)
            elif book == "2Jn":
                book_markers[book] = re.compile(r"SECOND\s+EPISTLE.*JOHN|EPISTLE.*(?:II|2)\s*(?:OF|,)\s*(?:S\.\s*)?JOHN", re.IGNORECASE)
            elif book == "3Jn":
                book_markers[book] = re.compile(r"THIRD\s+EPISTLE.*JOHN|EPISTLE.*(?:III|3)\s*(?:OF|,)\s*(?:S\.\s*)?JOHN", re.IGNORECASE)
            elif book == "Gal":
                book_markers[book] = re.compile(r"EPISTLE.*GALATIANS|TO\s+THE\s+GALATIANS", re.IGNORECASE)

    def flush():
        """Save accumulated commentary for current verse."""
        if current_chapter > 0 and current_verse > 0 and current_commentary:
            commentary_text = ' '.join(current_commentary).strip()
            commentary_text = re.sub(r'\s+', ' ', commentary_text)
            if len(commentary_text) > 20:
                results.append((current_book, current_chapter, current_verse, commentary_text))

    # Clean OCR artifacts
    text = re.sub(r'\n.*?Digitized by.*?\n', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'\n.*?Google\s*\n', '\n', text)

    lines = text.split('\n')
    found_first_chapter = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check book transition markers
        for book, pattern in book_markers.items():
            if pattern.search(stripped):
                # Find the index in expected_chapters for this book's first chapter
                for idx, (b, ch) in enumerate(expected_chapters):
                    if b == book:
                        if idx > chapter_idx:
                            flush()
                            chapter_idx = idx
                            current_book = book
                            current_chapter = ch
                            current_verse = 0
                            current_commentary = []
                            found_first_chapter = False  # Need to find CHAPTER header again
                        break
                break

        # Check for chapter header
        if chapter_pat.match(stripped):
            flush()
            if not found_first_chapter:
                found_first_chapter = True
                # We're at the first chapter - use current expected
            else:
                # Advance to next expected chapter
                if chapter_idx + 1 < len(expected_chapters):
                    # Only advance if staying in same book or this is the next sequential chapter
                    next_idx = chapter_idx + 1
                    current_book = expected_chapters[next_idx][0]
                    current_chapter = expected_chapters[next_idx][1]
                    chapter_idx = next_idx
            current_verse = 0
            current_commentary = []
            continue

        if not found_first_chapter:
            continue

        # Check for verse marker
        m = verse_pat.match(stripped)
        if not m:
            m = verse_pat2.match(stripped)
        if m:
            flush()
            current_verse = int(m.group(1))
            after = stripped[m.end():].strip()
            current_commentary = [after] if after else []
            continue

        # Accumulate commentary text for current verse
        if current_verse > 0:
            current_commentary.append(stripped)

    flush()

    # Summary
    chapters_found = set()
    for book, ch, v, _ in results:
        chapters_found.add((book, ch))
    print(f"  V{vol_num}: Parsed {len(results)} verse commentaries across {len(chapters_found)} chapters")
    return results


def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"completed_volumes": [], "last_run": None}


def save_state(state):
    CACHE_DIR.mkdir(exist_ok=True)
    state["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S")
    STATE_FILE.write_text(json.dumps(state, indent=2))


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Scrape Lapide commentary from Archive.org")
    parser.add_argument("--resume", action="store_true", help="Resume from last completed volume")
    parser.add_argument("--volume", type=int, help="Process only this volume number (1-8)")
    parser.add_argument("--parse-only", action="store_true", help="Skip download, parse cached files only")
    parser.add_argument("--output", type=str, default=str(OUTPUT_FILE), help="Output TSV file path")
    args = parser.parse_args()

    state = load_state()
    volumes_to_process = sorted(VOLUMES.keys())

    if args.volume:
        volumes_to_process = [args.volume]
    elif args.resume:
        volumes_to_process = [v for v in volumes_to_process if v not in state["completed_volumes"]]

    if not volumes_to_process:
        print("All volumes already processed. Use --volume N to reprocess a specific volume.")
        return

    print(f"Processing volumes: {volumes_to_process}")
    all_results = []

    for vol_num in volumes_to_process:
        print(f"\n=== Volume {vol_num} ===")

        if not args.parse_only:
            cache_file = download_volume(vol_num)
        else:
            cache_file = CACHE_DIR / f"v{vol_num}.txt"

        if not cache_file or not cache_file.exists():
            print(f"  V{vol_num}: No cached file found, skipping")
            continue

        text = cache_file.read_text(encoding='utf-8', errors='replace')
        results = parse_volume(vol_num, text)

        for book, chapter, verse, commentary in results:
            clean = commentary.replace('\t', ' ').replace('\n', ' ').replace('\r', '')
            all_results.append((book, f"{chapter}:{verse}", clean))

        state["completed_volumes"] = list(set(state.get("completed_volumes", []) + [vol_num]))
        save_state(state)

    # Write output
    print(f"\nWriting {len(all_results)} entries to {args.output}...")
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write("Book\tVerse\tCommentary\n")
        for book, verse, commentary in all_results:
            f.write(f"{book}\t{verse}\t{commentary}\n")

    print(f"Done! {len(all_results)} verse commentaries written.")

    # Summary by book
    book_counts = {}
    for book, _, _ in all_results:
        book_counts[book] = book_counts.get(book, 0) + 1
    print("\nSummary by book:")
    for book, count in sorted(book_counts.items(), key=lambda x: x[0]):
        print(f"  {book}: {count} verses")


if __name__ == "__main__":
    main()
