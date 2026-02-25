from datetime import datetime, timedelta
cd = datetime.now()
nd = cd - timedelta(days=5)
print("5 days ago:", nd)