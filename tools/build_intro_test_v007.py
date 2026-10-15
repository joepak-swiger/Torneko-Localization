from pathlib import Path
from collections import defaultdict, deque
import hashlib

ROOT = Path(__file__).resolve().parent.parent
INPUT_HASH = '4f44f32a86259a28ef3d98efe9ee95caa5fd15b064e17b9ba1807ea223ac04c7'
START, END = 0x43FAAC, 0x4410E4

def unpack(data):
    if data[0] != 0x10:
        raise ValueError('Unexpected compression format.')
    size = int.from_bytes(data[1:4], 'little')
    out = bytearray()
    p = 4
    while len(out) < size:
        flags = data[p]
        p += 1
        for bit in range(7, -1, -1):
            if len(out) == size:
                break
            if flags & (1 << bit):
                a, b = data[p:p + 2]
                p += 2
                length = (a >> 4) + 3
                distance = ((a & 15) << 8 | b) + 1
                if distance > len(out) or len(out) + length > size:
                    raise ValueError('Invalid compressed reference.')
                for _ in range(length):
                    out.append(out[-distance])
            else:
                out.append(data[p])
                p += 1
    return out

def pack(data):
    n = len(data)
    index = defaultdict(deque)
    matches = []
    for p in range(n):
        key = bytes(data[p:p + 3])
        queue = index[key]
        while queue and queue[0] < p - 4096:
            queue.popleft()
        best, distance = 0, 0
        if len(key) == 3:
            for old in reversed(queue):
                length = 3
                while length < 18 and p + length < n and data[old + length] == data[p + length]:
                    length += 1
                if length > best:
                    best, distance = length, p - old
                if length == 18:
                    break
            queue.append(p)
        matches.append((best, distance))

    costs = [[0] * 8 for _ in range(n + 1)]
    choices = [[1] * 8 for _ in range(n)]
    for p in range(n - 1, -1, -1):
        for slot in range(8):
            nxt, header = (slot + 1) % 8, int(slot == 0)
            best, take = header + 1 + costs[p + 1][nxt], 1
            for length in range(3, matches[p][0] + 1):
                cost = header + 2 + costs[p + length][nxt]
                if cost < best:
                    best, take = cost, length
            costs[p][slot], choices[p][slot] = best, take

    out = bytearray(b'\x10' + n.to_bytes(3, 'little'))
    p, slot = 0, 0
    while p < n:
        if slot == 0:
            flagpos = len(out)
            out.append(0)
        length = choices[p][slot]
        if length == 1:
            out.append(data[p])
        else:
            out[flagpos] |= 1 << (7 - slot)
            word = ((length - 3) << 12) | (matches[p][1] - 1)
            out.extend(word.to_bytes(2, 'big'))
        p += length
        slot = (slot + 1) % 8
    return bytes(out)

def main():
    source = ROOT / 'builds' / 'Torneko2-English-Name-Test-v006.gba'
    original = source.read_bytes()
    if hashlib.sha256(original).hexdigest() != INPUT_HASH:
        raise SystemExit('v006 hash mismatch. Build stopped.')
    block = unpack(original[START:END])
    edits = [
        (0x1CB4, '老人「・・・いかんな。\r　あれは　まさしく　しあわせの箱。\r老人「このままでは・・・。',
         'ELDER: ...OH DEAR.\rTHE HAPPINESS BOX!\rELDER: THIS IS BAD.'),
        (0x1D09, '老人「・・・・・・。', 'ELDER: ...'),
        (0x1D1E, '老人「・・・奥方っ！', 'ELDER: ...MADAM!'),
    ]
    for offset, japanese, english in edits:
        expected = japanese.encode('shift_jis')
        end = offset + len(expected)
        if block[offset:end + 1] != expected + b'\0':
            raise SystemExit(f'Text mismatch at {offset:#x}.')
        replacement = english.encode('ascii')
        if len(replacement) > len(expected):
            raise SystemExit('Translation exceeds its original allocation.')
        block[offset:end] = replacement.ljust(len(expected), b'\0')

    compressed = pack(block)
    if unpack(compressed) != block:
        raise SystemExit('Compression round-trip failed.')
    if len(compressed) > END - START:
        raise SystemExit('Compressed block does not fit. Nothing written.')
    build = bytearray(original)
    build[START:END] = compressed.ljust(END - START, b'\0')
    if len(build) != len(original) or build[:START] != original[:START] or build[END:] != original[END:]:
        raise SystemExit('Unexpected changes outside the script block.')
    output = ROOT / 'builds' / 'Torneko2-English-Intro-Test-v007.gba'
    output.write_bytes(build)
    print(f'Created: {output}')
    print(f'Compressed script: {len(compressed)} / {END - START} bytes')
    print('Translated three opening entries. Emulator test still required.')
    print('SHA256:', hashlib.sha256(build).hexdigest())

if __name__ == '__main__':
    main()
