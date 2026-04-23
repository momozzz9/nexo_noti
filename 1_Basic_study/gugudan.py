# 구구단 곱셈 결과의 합을 계산하는 프로그램

total = 0
for i in range(2, 10):
    for j in range(1, 10):
        total += i * j

print(f"구구단 곱셈 결과의 전체 합: {total}")
