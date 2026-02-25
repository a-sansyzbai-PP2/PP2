def even(n):
    for i in range(n + 1):
        if i % 2 == 0:
            yield i

n = int(input(4))
print(",".join(str(num) for num in even(n)))