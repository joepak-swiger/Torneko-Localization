from pathlib import Path
from collections import defaultdict
import hashlib
import json
import struct

ROOT = Path(__file__).resolve().parent.parent
EXPECTED_HASH = (
    "79986287eef366bba987393de8247141973"
    "d5564fa72fe2f3f6dd28684cd18aa"
)

def main():
    matches = sorted((ROOT / "originals").glob("*2 Advance*.gba"))
    if len(matches) != 1:
        raise SystemExit(
            "Expected exactly one Torneko 2 Advance .gba in originals."
        )

    rom_path = matches[0]
    data = rom_path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()

    if digest != EXPECTED_HASH:
        raise SystemExit(
            "ROM hash does not match our inspected Japanese version. "
            "Nothing was extracted."
        )

    # Scan aligned 32-bit values for possible ROM addresses.
    references = defaultdict(list)
    for position in range(0, len(data) - 3, 4):
        address = struct.unpack_from("<I", data, position)[0]
        offset = address - 0x08000000
        if 0 <= offset < len(data):
            references[offset].append(position)

    entries = []
    for offset, locations in sorted(references.items()):
        end = data.find(b"\0", offset, min(len(data), offset + 2049))
        if end <= offset:
            continue

        raw = data[offset:end]
        try:
            japanese = raw.decode("shift_jis")
        except UnicodeDecodeError:
            continue

        if any(
            ord(char) < 32 and char not in "\r\n\t"
            for char in japanese
        ):
            continue

        kana_count = sum(
            "\u3041" <= char <= "\u3096"
            or "\u30a1" <= char <= "\u30fa"
            for char in japanese
        )
        if kana_count < 2:
            continue

        entries.append({
            "id": f"T2_{offset:08X}",
            "rom_offset": f"0x{offset:08X}",
            "original_byte_length": len(raw),
            "candidate_pointer_offsets": [
                f"0x{position:08X}" for position in locations
            ],
            "original_hex": raw.hex(),
            "japanese": japanese,
            "english": "",
            "status": "unreviewed_candidate",
            "notes": ""
        })

    output_dir = ROOT / "extracted"
    output_dir.mkdir(parents=True, exist_ok=True)

    output = {
        "tool_version": "0.1",
        "rom_filename": rom_path.name,
        "rom_sha256": digest,
        "encoding": "shift_jis",
        "candidate_count": len(entries),
        "limitations": [
            "Candidate pointers have not been verified at runtime.",
            "Entries may overlap or include false positives.",
            "This is not a complete script extraction.",
            "Short, kanji-only, compressed, and custom-coded text "
            "may be missed.",
            "Original byte length is not a verified insertion budget."
        ],
        "entries": entries
    }

    json_path = output_dir / "torneko2_candidates.json"
    json_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    preview_path = output_dir / "torneko2_preview.txt"
    with preview_path.open("w", encoding="utf-8-sig") as preview:
        for entry in entries:
            preview.write(
                f"{entry['id']} | "
                f"{entry['original_byte_length']} bytes\n"
            )
            preview.write(entry["japanese"] + "\n\n")

    print(f"ROM verified: {rom_path.name}")
    print(f"Candidate text entries: {len(entries):,}")
    print(f"Editable data: {json_path}")
    print(f"Reading preview: {preview_path}")
    print("Original ROM was not modified.")

if __name__ == "__main__":
    main()
