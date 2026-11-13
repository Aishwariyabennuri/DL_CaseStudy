from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from PIL import Image


class CatalogueSimilarity:
    def __init__(self, dataset_dir: Path, image_dir: Path):
        self.dataset_dir = dataset_dir
        self.image_dir = image_dir
        self._items = None

    @staticmethod
    def _feature(image: Image.Image) -> np.ndarray:
        array = cv2.cvtColor(np.array(image.convert("RGB")), cv2.COLOR_RGB2HSV)
        resized = cv2.resize(array, (96, 96))
        histogram = cv2.calcHist([resized], [0, 1], None, [16, 8], [0, 180, 0, 256])
        histogram = cv2.normalize(histogram, histogram).flatten()
        return histogram

    def _load_items(self):
        if self._items is not None:
            return self._items
        csv_path = self.dataset_dir / "styles.csv"
        frame = pd.read_csv(csv_path, engine="python", on_bad_lines="skip")
        categories = {
            "Dresses", "Jackets", "Jeans", "Kurtas", "Shirts",
            "Shorts", "Skirts", "Tops", "Trousers", "Tshirts",
        }
        items = []
        for _, row in frame[frame["articleType"].isin(categories)].iterrows():
            image_id = str(row["id"]).split(".")[0]
            image_path = self.image_dir / f"{image_id}.jpg"
            if not image_path.exists():
                continue
            try:
                with Image.open(image_path) as image:
                    items.append({
                        "id": image_id,
                        "name": str(row["productDisplayName"]),
                        "category": str(row["articleType"]),
                        "image": f"/fashion-images/{image_id}.jpg",
                        "feature": self._feature(image),
                    })
            except (OSError, ValueError):
                continue
        self._items = items
        return items

    def find(self, image_file, limit: int = 8):
        with Image.open(image_file) as image:
            query = self._feature(image)
        items = self._load_items()
        ranked = sorted(
            items,
            key=lambda item: cv2.compareHist(query.astype("float32"), item["feature"].astype("float32"), cv2.HISTCMP_BHATTACHARYYA),
        )
        return [
            {
                key: value
                for key, value in item.items()
                if key != "feature"
            }
            | {"similarity": round(max(0.0, 1.0 - float(cv2.compareHist(
                query.astype("float32"), item["feature"].astype("float32"), cv2.HISTCMP_BHATTACHARYYA
            ))) * 100, 2)}
            for item in ranked[:limit]
        ]
