names = ["Ali", "Aruzhan", "Dias"]
scores = [90, 85, 88]
for i, name in enumerate(names):
    print(i, name)
for n, s in zip(names, scores):
    print(n, s)