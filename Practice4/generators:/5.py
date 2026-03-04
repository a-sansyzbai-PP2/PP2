def c(n):
    while n >= 0:
        yield n
        n -= 1
for i in c(5):
    print(i)