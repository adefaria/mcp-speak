#!/usr/bin/env python3
"""Switch the agent personality in a rules file without touching anything else.

Unlike setup.py, which regenerates the entire rules file, this script replaces
only the personality block (delimited by marker comments) so that custom
sections such as keybinding preferences or transcript-mirroring rules are
preserved.

Personality definitions are read from the personalities/ directory.

Usage:
    personality                 # interactive menu
    personality smith           # fuzzy match on personality name
    personality --list          # list personalities and show the active one
    personality --file PATH ... # target a different rules file
"""
import argparse
import re
import sys
from pathlib import Path

PERSONALITIES_DIR = Path(__file__).resolve().parent / "personalities"
DEFAULT_TARGET = Path("~/.gemini/GEMINI.md").expanduser()
START = "<!-- personality:start -->"
END = "<!-- personality:end -->"
LEGACY_MARKERS = {"<!-- persona:start -->": START, "<!-- persona:end -->": END}
EXCLUDE = {"base_guidelines"}
# Heading used inside the personality definition files.
HEADING_RE = r"\*\*Persona:\s*(.+?)\*\*"


def available_personalities():
    return sorted(p.stem for p in PERSONALITIES_DIR.glob("*.md") if p.stem not in EXCLUDE)


def personality_title(stem):
    text = (PERSONALITIES_DIR / f"{stem}.md").read_text()
    m = re.search(HEADING_RE, text)
    return m.group(1).strip() if m else stem


def ensure_markers(content):
    """Wrap an existing, unmarked personality block in marker comments."""
    for old, new in LEGACY_MARKERS.items():
        content = content.replace(old, new)
    if START in content and END in content:
        return content
    m = re.search(r"^#### \*\*Persona:.*$", content, re.M)
    if not m:
        sys.exit("Error: no personality block or markers found in the target file.")
    start = m.start()
    # The block ends at the first level-3 heading after its
    # "Execution Boundaries" section, or at end of file.
    eb = re.search(r"^### \*\*Execution Boundaries\*\*.*$", content[start:], re.M)
    search_from = start + (eb.end() if eb else 0)
    nxt = re.search(r"^### ", content[search_from:], re.M)
    end = search_from + nxt.start() if nxt else len(content)
    block = content[start:end].rstrip()
    return content[:start] + f"{START}\n{block}\n{END}\n\n" + content[end:].lstrip("\n")


def current_personality(content):
    m = re.search(HEADING_RE, content)
    return m.group(1).strip() if m else None


def resolve(choice, personalities):
    if choice.isdigit() and 1 <= int(choice) <= len(personalities):
        return personalities[int(choice) - 1]
    key = choice.lower().replace(" ", "_").removesuffix(".md")
    if key in personalities:
        return key
    matches = [p for p in personalities if key in p]
    if len(matches) == 1:
        return matches[0]
    sys.exit(f"Error: '{choice}' matches {matches or 'nothing'}. Use --list to see options.")


def main():
    ap = argparse.ArgumentParser(description="Switch the agent personality.")
    ap.add_argument("personality", nargs="?", help="Personality name, partial name, or menu number")
    ap.add_argument("--list", action="store_true", help="List personalities and exit")
    ap.add_argument("--file", type=Path, default=DEFAULT_TARGET, help="Rules file to edit")
    args = ap.parse_args()

    target = args.file.expanduser()
    content = target.read_text()
    personalities = available_personalities()
    active = current_personality(content)

    if args.list or not args.personality:
        for i, p in enumerate(personalities, 1):
            title = personality_title(p)
            mark = "*" if active and title == active else " "
            print(f" {mark} [{i}] {p:<20} {title}")
        if args.list:
            return
        choice = input("\nSelect personality: ").strip()
        if not choice:
            return
    else:
        choice = args.personality

    stem = resolve(choice, personalities)
    new_block = (PERSONALITIES_DIR / f"{stem}.md").read_text().rstrip()

    content = ensure_markers(content)
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    content = pattern.sub(lambda _: f"{START}\n{new_block}\n{END}", content, count=1)

    target.write_text(content)
    print(f"Personality set to '{personality_title(stem)}' in {target}")
    print("Start a new conversation for the change to take effect.")


if __name__ == "__main__":
    main()
