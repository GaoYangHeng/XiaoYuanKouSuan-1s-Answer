import hashlib
import itertools

KEY = "wdi4n2t8edr"

# 样本：(路径, sign, 参考时间戳秒)
SAMPLES = [
    ("/leo-game-pk/android/math/pk/match/v2", "7ccaf869bade9bf18c8f0c3e8a034e23", 1788059161),
    ("/leo-game-pk/android/math/pk/match/v2", "cfe580fae28fc66c89610b620c815478", 1788059225),
    ("/leo-game-pk/android/math/pk/multi/match/v2", "82ef6c3753a9582be8186b562771cf44", 1788059238),
    ("/leo-game-pk/android/math/pk/match/v2", "f56ed48991777ba7c272d97167a2619c", 1788059351),
    ("/leo-game-pk/android/word/eliminate/match/v2", "4364c6b8e228c3e3318da07c663ee724", 1788059227),
    ("/leo-game-pk/android/math/pk/match/v2", "901574426bac0e001f8ffbf46883b9c0", 1788059444),
    ("/leo-game-pk/android/math/pk/match/v2", "8f8118bb867adacf8eecc9c8c139f8b1", 1788059614),
]

SEPARATORS = ["", "&", "|", "-", "_", "/", "?", ","]


def md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()


def path_variants(p: str):
    yield p
    yield p.lstrip("/")
    yield "https://xyks.yuanfudao.com" + p
    yield "http://xyks.yuanfudao.com" + p


def ts_variants(sec: int):
    yield str(sec)
    yield str(sec // 60)
    yield str(sec // 60)  # 分钟
    yield str(sec // 600)
    yield str(sec // 600)


def run():
    found = []
    # 对每个样本独立爆破
    for path, target, ref_sec in SAMPLES:
        hits = []
        for pv in path_variants(path):
            # ts 在参考值前后 90 秒内扫描（覆盖分钟边界）
            for delta in range(-90, 91):
                sec = ref_sec + delta
                tvals = list(dict.fromkeys(ts_variants(sec)))
                parts_pool = [pv, KEY]
                for t in tvals:
                    items = [pv, KEY, t]
                    for perm in itertools.permutations([0, 1, 2]):
                        ordered = [items[i] for i in perm]
                        for sep in SEPARATORS:
                            cand = sep.join(ordered)
                            if md5(cand) == target:
                                hits.append(cand)
        if hits:
            found.append((path, hits[0]))
            print(f"[命中] {path} -> {hits[0]}")
        else:
            print(f"[未命中] {path}")
    return found


if __name__ == "__main__":
    run()
