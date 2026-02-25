import math
n = int(input()) #number of sides
s = float(input()) #length of a side
area = (n * s**2) / (4 * math.tan(math.pi / n))
print(area) #The area of the polygon