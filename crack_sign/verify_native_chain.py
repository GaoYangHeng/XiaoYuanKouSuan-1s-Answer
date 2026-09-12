import hashlib
import datetime

K = b"wdi4n2t8edr"

def chain(first_byte, minute, P):
    Pp = bytes([first_byte]) + P[1:].encode()
    h1 = hashlib.md5(Pp + K).hexdigest().encode()
    h2 = hashlib.md5(Pp + K + h1 + Pp).hexdigest().encode()
    base = Pp + K + h1 + Pp + h2
    T = str(minute).encode()
    h3 = hashlib.md5(base + T).hexdigest().encode()
    return hashlib.md5(base + T + h3 + K).hexdigest()

TZ = datetime.timezone(datetime.timedelta(hours=8))
day = datetime.datetime(2026, 8, 30, 0, 0, 0, tzinfo=TZ)

samples = [
    ("68637e3ae7506ac7c0328b7a146882dc", "/solar-activity/android/activity/6", "18:10:50", 1788084650),
    ("41d65d7b4f118c62f758fc8301b4e76f", "/orion-hubble-config/android/keys/v4", "18:10:53", 1788084653),
]

print("epoch 校准: 18:10:59 ->", int(day.timestamp()) + 18*3600 + 10*60 + 59, "(期望 1788084659)")

total = 0
for sign, path, hms, _ts in samples:
    hh, mm, ss = map(int, hms.split(":"))
    t_center = int(day.timestamp()) + hh*3600 + mm*60 + ss
    hit = False
    for delta in range(-128, 128):
        fb = (ord(path[0]) + delta) & 0xFF
        for dt in range(-120, 121):
            ts = t_center + dt
            total += 1
            if chain(fb, ts // 60, path) == sign:
                print(f"[HIT] sign={sign} path={path} delta={delta} ts={ts} (偏移{dt:+d}s) minute={ts//60} 首字节=0x{fb:02x}/{chr(fb)!r}")
                hit = True
    if not hit:
        print(f"[MISS] sign={sign} path={path}")
print(f"共 {total} 次计算")
