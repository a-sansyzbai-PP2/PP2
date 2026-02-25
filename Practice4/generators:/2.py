from datetime import datetime, timedelta
t = datetime.now()
y = t - timedelta(days=1)
tm = t + timedelta(days=1)
print("Yesterday:", y)
print("Today:", t)
print("Tomorrow:", tm)