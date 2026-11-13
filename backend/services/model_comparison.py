
import os
import json
import numpy as np
import tensorflow as tf

from PIL import Image
from pathlib import Path
from tensorflow.keras.applications.vgg16 import preprocess_input as vgg_preprocess
from tensorflow.keras.applications.resnet50 import preprocess_input as resnet_preprocess

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_DIR = BASE_DIR / "models"

# Load class names
with open(MODEL_DIR / "class_names.json", "r") as file:
    CLASS_NAMES = json.load(file)

# Load all three trained models
MODELS = {
    "VGG16": tf.keras.models.load_model(
        MODEL_DIR / "vestiar_vgg16.keras"
    ),
    "Custom CNN": tf.keras.models.load_model(
        MODEL_DIR / "vestiar_custom_cnn.keras"
    ),
    "ResNet50": tf.keras.models.load_model(
        MODEL_DIR / "vestiar_resnet50.keras"
    )
}


def compare_models(image_path):

    image = Image.open(image_path).convert("RGB")
    image = image.resize((224, 224))

    image_array = np.array(image, dtype=np.float32)

    # Custom CNN uses normalized pixel values
    custom_input = np.expand_dims(image_array / 255.0, axis=0)

    # VGG16 preprocessing
    vgg_input = np.expand_dims(
        vgg_preprocess(image_array.copy()), axis=0
    )

    # ResNet50 preprocessing
    resnet_input = np.expand_dims(
        resnet_preprocess(image_array.copy()), axis=0
    )

    inputs = {
        "VGG16": vgg_input,
        "Custom CNN": custom_input,
        "ResNet50": resnet_input
    }

    results = {}

    for model_name, model in MODELS.items():

        predictions = model.predict(
            inputs[model_name], verbose=0
        )[0]

        predicted_index = int(np.argmax(predictions))

        results[model_name] = {
            "predicted_category": CLASS_NAMES[predicted_index],
            "confidence": round(
                float(predictions[predicted_index]) * 100, 2
            )
        }

    return results
