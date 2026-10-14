from pathlib import Path
import hashlib
import struct

ROOT = Path(__file__).resolve().parent.parent
SOURCE_HASH = (
    "79986287eef366bba987393de8247141973"
    "d5564fa72fe2f3f6dd28684cd18aa"
)
BUILD_HASH = (
    "425d6f46f544d4f877b4f31320a1999c7"
    "e650660b18f369d2686906caf12c68e"
)

def main():
    matches = sorted((ROOT / "originals").glob("*2 Advance*.gba"))
    if len(matches) != 1:
        raise SystemExit("Expected one Torneko 2 Advance ROM in originals.")

    original = matches[0].read_bytes()
    if hashlib.sha256(original).hexdigest() != SOURCE_HASH:
        raise SystemExit("Original ROM hash mismatch. Build stopped.")

    changes = [
        (
            0x61D04,
            bytes.fromhex("2082cd82b682df82a982e7"),
            " NEW GAME",
            0x141314
        ),
        (
            0x61CF8,
            bytes.fromhex("2082c282c382ab82a982e7"),
            " CONTINUE",
            0x141318
        ),
    ]

    build = bytearray(original)

    for offset, expected, english, pointer_offset in changes:
        end = offset + len(expected)
        if original[offset:end + 1] != expected + b"\0":
            raise SystemExit(f"Unexpected original text at {offset:#x}.")

        pointer = struct.unpack_from("<I", original, pointer_offset)[0]
        if pointer != 0x08000000 + offset:
            raise SystemExit(f"Unexpected pointer at {pointer_offset:#x}.")

        replacement = english.encode("ascii")
        if len(replacement) > len(expected):
            raise SystemExit("Replacement is too long.")

        build[offset:end] = replacement.ljust(len(expected), b" ")

    digest = hashlib.sha256(build).hexdigest()
    if len(build) != len(original) or digest != BUILD_HASH:
        raise SystemExit("Build verification failed.")

    output = ROOT / "builds" / "Torneko2-English-Menu-Test-v002.gba"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(build)

    changed = sum(a != b for a, b in zip(original, build))
    print(f"Created: {output}")
    print(f"Changed bytes: {changed}")
    print(f"SHA256: {digest}")
    print("Original ROM was not modified.")

if __name__ == "__main__":
    main()

