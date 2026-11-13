import pandas as pd
import os

path = "datasets/fashion-product-images-small"

df = pd.read_csv(
    os.path.join(path, "styles.csv"),
    engine="python",
    on_bad_lines="skip"
)

print("Total records:", len(df))
print("\nAvailable columns:")
print(df.columns.tolist())

print("\nFirst 5 records:")
print(df.head())

print("\nImages folder exists:", os.path.exists(os.path.join(path, "images")))