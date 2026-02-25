from datetime import datetime

d1 = datetime(2026, 2, 20, 10, 0, 0)
d2 = datetime(2026, 2, 25, 12, 0, 0)

dif = d2 - d1
sec = dif.total_seconds()
print(sec)