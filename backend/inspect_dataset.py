import pandas as pd
import os

path = "datasets/fashion-product-images-small"

df = pd.read_csv(
    os.path.join(path, "styles.csv"),
    engine="python",
    on_bad_lines="skip"
)

images = os.path.join(path, "images")

df["image_exists"] = df["id"].apply(
    lambda x: os.path.exists(os.path.join(images, f"{x}.jpg"))
)

print("Total records:", len(df))
print("Available images:", df["image_exists"].sum())

print("\nTop 20 clothing categories:")
print(df["articleType"].value_counts().head(20))

print("\nMaster categories:")
print(df["masterCategory"].value_counts())

print("\nClothing categories for VestiAR:")

selected = [
    "Shirts", "Tshirts", "Tops", "Kurtas",
    "Jeans", "Trousers", "Shorts", "Dresses",
    "Skirts", "Jackets"
]

print(
    df[df["articleType"].isin(selected)]
    ["articleType"].value_counts()
)