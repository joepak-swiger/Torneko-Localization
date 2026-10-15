from pathlib import Path
import hashlib
import re

ROOT = Path(__file__).resolve().parent.parent
INPUT_HASH = "08d8067a0069c2cd8b7b10d655ed20564c6e81988a3169fbbafa22b67d80f8a7"
OUTPUT_HASH = "4f44f32a86259a28ef3d98efe9ee95caa5fd15b064e17b9ba1807ea223ac04c7"

def main():
    source = ROOT / "builds" / "Torneko2-English-Menu-Test-v004.gba"
    if not source.exists():
        raise SystemExit("Run build_menu_test_v004.py first.")

    original = source.read_bytes()
    if hashlib.sha256(original).hexdigest() != INPUT_HASH:
        raise SystemExit("v004 hash mismatch. Build stopped.")

    build = bytearray(original)
    grid_start = 0x646BC
    grid_end = original.index(b"\0", grid_start)
    grid = original[grid_start:grid_end]

    cells = list(re.finditer(rb"\x04[\s\S]([\s\S]{2})", grid))
    if len(cells) != 60:
        raise SystemExit("Unexpected character-grid structure.")

    table_start = 0x141A54
    table = original[table_start:0x141AE2]

    for index, cell in enumerate(cells[:26]):
        japanese = cell.group(1)
        english = chr(0xFF21 + index).encode("shift_jis")

        matches = [
            offset for offset in range(0, len(table), 2)
            if table[offset:offset + 2] == japanese
        ]
        if len(matches) != 1:
            raise SystemExit("Character-table match was not unique.")

        display_offset = grid_start + cell.start(1)
        input_offset = table_start + matches[0]

        build[display_offset:display_offset + 2] = english
        build[input_offset:input_offset + 2] = english

    digest = hashlib.sha256(build).hexdigest()
    if len(build) != len(original) or digest != OUTPUT_HASH:
        raise SystemExit("Build verification failed.")

    output = ROOT / "builds" / "Torneko2-English-Name-Test-v006.gba"
    output.write_bytes(build)

    print(f"Created: {output}")
    print("Added A-Z to the first 26 cells of the hiragana page.")
    print(f"SHA256: {digest}")
    print("Original ROM and previous builds were not modified.")

if __name__ == "__main__":
    main()
