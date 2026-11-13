import json
import numpy as np
import tensorflow as tf

from pathlib import Path
from PIL import Image
from tensorflow.keras.applications.vgg16 import preprocess_input

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "models" / "vestiar_vgg16.keras"
CLASS_PATH = BASE_DIR / "models" / "class_names.json"

# Load model and class names once
model = tf.keras.models.load_model(MODEL_PATH)

with open(CLASS_PATH, "r") as file:
    class_names = json.load(file)


def classify_clothing(image_file):
    image = Image.open(image_file).convert("RGB")
    image = image.resize((224, 224))

    image_array = np.array(image, dtype=np.float32)
    image_array = preprocess_input(image_array)
    image_array = np.expand_dims(image_array, axis=0)

    predictions = model.predict(image_array, verbose=0)[0]

    predicted_index = int(np.argmax(predictions))

    return {
        "category": class_names[predicted_index],
        "confidence": round(float(predictions[predicted_index]) * 100, 2)
    }