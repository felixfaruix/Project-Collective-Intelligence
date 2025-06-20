import pandas as pd
import matplotlib.pyplot as plt

# Change path here!
file_path = '/mnt/data/snapshot_2025-06-19 20:29:13'
df = pd.read_csv(file_path)

# Compute population counts per frame
counts = df.groupby(['frame', 'Kind']).size().reset_index(name='count')
pivot = counts.pivot(index='frame', columns='Kind', values='count').fillna(0)

# Plot population over time
plt.figure()
plt.plot(pivot.index, pivot['Rabbit'], label='Rabbits')
plt.plot(pivot.index, pivot['Fox'], label='Foxes')
plt.xlabel('Frame')
plt.ylabel('Count')
plt.title('Population of Rabbits and Foxes Over Time')
plt.legend()
plt.show()
