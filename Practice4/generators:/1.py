def square(n):
    for i in range(n + 1):
        yield i * i  #yield-generator
for num in square(5):
    print(num)