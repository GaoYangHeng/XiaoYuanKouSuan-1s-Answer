import hashlib
import struct
import itertools

KEY = "wdi4n2t8edr"

SAMPLES = [
    ("/leo-game-pk/android/math/pk/match/v2", "7ccaf869bade9bf18c8f0c3e8a034e23", 1788059163),
    ("/leo-game-pk/android/math/pk/match/v2", "cfe580fae28fc66c89610b620c815478", 1788059227),
    ("/leo-game-pk/android/math/pk/match/v2", "f56ed48991777ba7c272d97167a2619c", 1788059353),
    ("/leo-game-pk/android/math/pk/match/v2", "8f8118bb867adacf8eecc9c8c139f8b1", 1788059615),
]


def md5b(b):
    return hashlib.md5(b).hexdigest()


def try_binary():
    for path, target, ref in SAMPLES:
        hit = None
        pb = path.encode()
        kb = KEY.encode()
        for delta in range(-120, 121):
            sec = ref + delta
            minute = sec // 60
            ts_bin_variants = [
                struct.pack("<I", sec),
                struct.pack("<I", minute),
                struct.pack(">I", sec),
                struct.pack(">I", minute),
                struct.pack("<Q", sec),
                str(sec).encode(),
                str(minute).encode(),
            ]
            for tb in ts_bin_variants:
                parts = [pb, kb, tb]
                for perm in itertools.permutations([0, 1, 2]):
                    cand = b"".join(parts[i] for i in perm)
                    if md5b(cand) == target:
                        hit = cand
                        break
                if hit:
                    break
            if hit:
                break
        print(f"{'[命中]' if hit else '[未命中]'} {path} {hit!r}")


if __name__ == "__main__":
    try_binary()
