def square(n):
    for i in range(n + 1):
        yield i * i
for num in square(5):
    print(num)