from datetime import datetime
n = datetime.now()
wm = n.replace(microsecond=0)
print("Without microseconds:", wm)