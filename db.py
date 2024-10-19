from SQLClient import LastPricesSQLiteClient
from datetime import datetime
import matplotlib.pyplot as plt

client = LastPricesSQLiteClient(debug=True)
logs = client.get_prices()
tickers = [log[0] for log in logs]
timestamps = [datetime.strptime(log[1], '%Y-%m-%d %H:%M:%S.%f') for log in logs]
prices = [log[2] for log in logs]

fig = plt.figure(figsize=(15, 5))
plt.plot(timestamps, prices, color='b', marker='o', label='price')
plt.axhline(y=256.93, color='orange', linestyle='dashed')
plt.axvline(x=timestamps[5], color='black', linestyle='dashed')
plt.grid(True)
plt.legend()
plt.show()