def u32(x):
    return x & 0xFFFFFFFF

def f_b20(x):
    x = u32(x)
    r1 = u32((x >> 3) + (x >> 4))
    r1 = u32(r1 + (r1 >> 4))
    r1 = u32(r1 + (r1 >> 8))
    r1 = u32(r1 + (r1 >> 16))
    r2 = u32(r1 + (r1 << 2))          # 5*r1
    r2 = u32(-r2)                     # -5*r1
    r0 = u32(x + r2)                  # x - 5*r1
    r2 = 13
    r0 = u32(r0 * 13)
    r0 = u32(r1 + (r0 >> 6))
    return r0

def f_b44(x):
    x = u32(x)
    r0 = u32(x + (x >> 31))           # 处理符号
    r1 = u32((r0 >> 3) + (r0 >> 5))
    r1 = u32(r1 + (r1 >> 4))
    r1 = u32(r1 + (r1 >> 8))
    r1 = u32(r1 + (r1 >> 16))
    r2 = u32(r1 - (r1 << 2))          # -3*r1
    r0 = u32(r0 + (r2 << 1))          # x - 6*r1
    r2 = 11
    r0 = u32(r0 * 11)
    r0 = u32(r1 + (r0 >> 6))
    return r0

def f_b6c(x):
    x = u32(x)
    r1 = u32((x >> 1) + (x >> 2) + (x >> 3))
    r1 = u32(r1 + (r1 >> 6))
    r2 = u32(r1 + (r1 >> 12))
    r1 = u32(r2 + (r1 >> 24))
    r2 = u32(r1 >> 3)
    r2 = u32(r2 + (r2 << 3))          # 9*(r1>>3)
    r2 = u32(-r2)
    r0 = u32(x + r2)
    r0 = u32(r0 + 7)
    r0 = u32(r0 >> 4)
    r0 = u32(r0 + (r1 >> 3))
    return r0

def f_b96(x):
    x = u32(x)
    r0 = u32(x + (x >> 31))
    r1 = u32((r0 >> 1) + (r0 >> 2))
    r1 = u32(r1 + (r1 >> 4))
    r1 = u32(r1 + (r1 >> 8))
    r1 = u32(r1 + (r1 >> 16))
    r2 = u32(r1 >> 3)
    r2 = u32(r2 + (r2 << 2))          # 5*(r1>>3)
    r2 = u32(-r2)
    r0 = u32(r0 + (r2 << 1))          # x - 10*(r1>>3)
    r0 = u32(r0 + 6)
    r0 = u32(r0 >> 4)
    r0 = u32(r0 + (r1 >> 3))
    return r0

# 打印 0-31 的映射，观察规律
print("x  b20  b44  b6c  b96")
for x in range(0, 32):
    print(f"{x:3d} {f_b20(x)&0xff:4d} {f_b44(x)&0xff:4d} {f_b6c(x)&0xff:4d} {f_b96(x)&0xff:4d}")

# 检查是否为单射（置换）
for name, f in [("b20", f_b20), ("b44", f_b44), ("b6c", f_b6c), ("b96", f_b96)]:
    outs = [f(x) & 0xff for x in range(256)]
    print(f"\n{name}: 单射={len(set(outs))==256}, 值域大小={len(set(outs))}")

# 检查是否等于除以某常数
print("\n检查 b20 == x//7 ?")
ok = all((f_b20(x) & 0xff) == (x // 7) for x in range(256))
print("b20 == x//7:", ok)
ok = all((f_b20(x) & 0xff) == (x % 7) for x in range(256))
print("b20 == x%7:", ok)
print("检查 b44 == x//9 ?", all((f_b44(x)&0xff)==(x//9) for x in range(256)))
print("检查 b6c == x//5 ?", all((f_b6c(x)&0xff)==(x//5) for x in range(256)))
print("检查 b96 == x//3 ?", all((f_b96(x)&0xff)==(x//3) for x in range(256)))
