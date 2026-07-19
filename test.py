import pickle
with open("/mnt.pkl", "rb") as f:
    data = pickle.load(f)

# Print the first item or structural keys
print(type(data))
print(data[0] if isinstance(data, list) else data)