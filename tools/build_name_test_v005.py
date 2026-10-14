from pathlib import Path
import hashlib

ROOT = Path(__file__).resolve().parent.parent
INPUT_HASH = "08d8067a0069c2cd8b7b10d655ed20564c6e81988a3169fbbafa22b67d80f8a7"
OUTPUT_HASH = "5e6d69480b7beafc4603f02ede3c80dbd5bc2823aac6b94a5140c50978a1d754"

def main():
    source = ROOT / "builds" / "Torneko2-English-Menu-Test-v004.gba"
    if not source.exists():
        raise SystemExit("Build v004 first using build_menu_test_v004.py.")

    original = source.read_bytes()
    if hashlib.sha256(original).hexdigest() != INPUT_HASH:
        raise SystemExit("v004 hash mismatch. Build stopped.")

    build = bytearray(original)

    for index, (japanese, english) in enumerate(zip("あいう", "ＡＢＣ")):
        expected = japanese.encode("shift_jis")
        replacement = english.encode("shift_jis")

        offsets = [
            0x646BE + 4 * index,   # Visible grid
            0x141A54 + 2 * index, # Candidate input-character table
        ]

        for offset in offsets:
            if build[offset:offset + 2] != expected:
                raise SystemExit(f"Unexpected bytes at {offset:#x}.")
            build[offset:offset + 2] = replacement

    digest = hashlib.sha256(build).hexdigest()
    if digest != OUTPUT_HASH:
        raise SystemExit("Output verification failed.")

    output = ROOT / "builds" / "Torneko2-English-Name-Test-v005.gba"
    output.write_bytes(build)

    print(f"Created: {output}")
    print("Changed 6 bytes relative to v004.")
    print(f"SHA256: {digest}")
    print("Experimental: English name entry needs emulator testing.")

if __name__ == "__main__":
    main()
