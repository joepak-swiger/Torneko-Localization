from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parent.parent
SOURCE_HASH = "79986287eef366bba987393de8247141973d5564fa72fe2f3f6dd28684cd18aa"
BUILD_HASH = "fb5a0d18ba430e4398a93e6b35ea7b68d3c3b1b589f142df02f19938d2e7eb83"

def main():
    matches = sorted((ROOT / "originals").glob("*2 Advance*.gba"))
    if len(matches) != 1:
        raise SystemExit("Expected one Torneko 2 Advance ROM in originals.")

    original = matches[0].read_bytes()
    if hashlib.sha256(original).hexdigest() != SOURCE_HASH:
        raise SystemExit("Original ROM hash mismatch. Build stopped.")

    changes = [
        (0x61CD0, " サウンド", " SOUND"),
        (0x61CDC, " 冒険の書を消す", " DELETE SAVE"),
        (0x61CEC, " ハイスコア", " HIGH SCORE"),
        (0x61CF8, " つづきから", " CONTINUE"),
        (0x61D04, " はじめから", " NEW GAME"),
        (0x60140, "ひらがな", "HIRAGANA"),
        (0x647B4, "数字", "NUM"),
        (0x647D4, "カタカナ", "KATAKANA"),
    ]

    for start in (0x6014A, 0x647BA, 0x647DE):
        changes.extend([
            (start,      "すすむ", "NEXT"),
            (start + 8,  "もどる", "BACK"),
            (start + 16, "終わり", "DONE"),
        ])

    build = bytearray(original)
    allowed_changes = set()

    for offset, japanese, english in changes:
        expected = japanese.encode("shift_jis")
        end = offset + len(expected)

        if original[offset:end] != expected:
            raise SystemExit(f"Original text mismatch at {offset:#x}.")

        replacement = english.encode("ascii")
        if len(replacement) > len(expected):
            raise SystemExit(f"Replacement too long at {offset:#x}.")

        build[offset:end] = replacement.ljust(len(expected), b" ")
        allowed_changes.update(range(offset, end))

    if len(build) != len(original):
        raise SystemExit("Unexpected ROM size change.")

    changed_positions = [
        i for i, (a, b) in enumerate(zip(original, build)) if a != b
    ]
    if any(i not in allowed_changes for i in changed_positions):
        raise SystemExit("Unexpected change outside text regions.")

    digest = hashlib.sha256(build).hexdigest()
    if digest != BUILD_HASH:
        raise SystemExit("Build hash verification failed.")

    output = ROOT / "builds" / "Torneko2-English-Menu-Test-v003.gba"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(build)

    print(f"Created: {output}")
    print(f"Text replacements: {len(changes)}")
    print(f"Changed bytes: {len(changed_positions)}")
    print(f"SHA256: {digest}")
    print("Original ROM was not modified.")

if __name__ == "__main__":
    main()
