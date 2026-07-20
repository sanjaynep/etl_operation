import pandas as pd
import numpy as np
from faker import Faker
from multiprocessing import Pool, cpu_count

fake = Faker()

def maybe_null(value, prob=0.1):
    return value if np.random.rand() > prob else None

def generate_batch(batch_size=100_000):
    local_fake = Faker()  # each process gets its own Faker instance
    data = []
    for _ in range(batch_size):
        data.append({
            "name": local_fake.name(),
            "email": maybe_null(local_fake.email(), prob=0.05),
            "salary": maybe_null(np.random.randint(30000, 120000), prob=0.1),
            "dob": maybe_null(local_fake.date_of_birth(minimum_age=18, maximum_age=70), prob=0.05),
        })
    return pd.DataFrame(data)

if __name__ == "__main__":
    total_rows = 1_000_000
    batch_size = 100_000
    num_batches = total_rows // batch_size

    with Pool(cpu_count()) as pool:
        dfs = pool.map(generate_batch, [batch_size] * num_batches)

    final_df = pd.concat(dfs, ignore_index=True)

    final_df.to_parquet("fake_data.parquet", engine="pyarrow", compression="snappy")
    print("✅ Done! Saved to fake_data.parquet")
