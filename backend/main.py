
from services.model_comparison import compare_models
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from io import BytesIO
import os
import tempfile
import pandas as pd
from PIL import Image

from services.classifier import classify_clothing
from services.virtual_tryon import VirtualTryOnUnavailable, generate_try_on
from services.similarity import CatalogueSimilarity

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "datasets" / "fashion-product-images-small"
IMAGE_DIR = DATASET_DIR / "images"
VTON_DIR = BASE_DIR / "vton_outputs"
UPLOAD_DIR = BASE_DIR / "uploads"
VTON_DIR.mkdir(exist_ok=True)
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_VTON_IMAGE_BYTES = 10 * 1024 * 1024
MIN_VTON_IMAGE_DIMENSION = 256
MIN_GARMENT_IMAGE_DIMENSION = 32
similarity_index = CatalogueSimilarity(DATASET_DIR, IMAGE_DIR)

# Create app only once
app = FastAPI(title="VestiAR API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Serve fashion dataset images
app.mount(
    "/fashion-images",
    StaticFiles(directory=str(IMAGE_DIR)),
    name="fashion-images"
)
app.mount(
    "/vton-outputs",
    StaticFiles(directory=str(VTON_DIR)),
    name="vton-outputs"
)
app.mount(
    "/vton-examples",
    StaticFiles(directory=str(BASE_DIR.parent / "clothes-virtual-try-on" / "assets")),
    name="vton-examples"
)

@app.get("/")
def home():
    return {"message": "VestiAR Backend Running"}

@app.get("/api/health")
def health():
    return {"status": "healthy"}

@app.get("/api/catalogue")
def get_catalogue(category: str = "All", limit: int = 40):
    csv_path = DATASET_DIR / "styles.csv"

    try:
        df = pd.read_csv(
            csv_path,
            engine="python",
            on_bad_lines="skip"
        )

        clothing_categories = [
                        "Dresses", "Jackets", "Jeans", "Kurtas",
                         "Shirts", "Shorts", "Skirts", "Tops",
                        "Trousers", "Tshirts"
                            ]

        limit = max(1, min(limit, 200))
        if category == "All":
            df = df[df["articleType"].isin(clothing_categories)]
        else:
            df = df[
            df["articleType"].fillna("").str.lower()
            == category.lower()
                ]

        total_matching = 0
        products = []

        for _, row in df.iterrows():
            image_id = str(row["id"]).split(".")[0]
            image_path = IMAGE_DIR / f"{image_id}.jpg"

            if image_path.exists():
                total_matching += 1
                if len(products) >= limit:
                    continue
                products.append({
                    "id": image_id,
                    "name": row["productDisplayName"],
                    "category": row["articleType"],
                    "image": f"/fashion-images/{image_id}.jpg"
                })

        return {"products": products, "total": total_matching}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/classify")
async def classify_image(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload an image."
        )

    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="The uploaded image is empty.")
        image_data = BytesIO(image_bytes)
        return classify_clothing(image_data)
    except HTTPException:
        raise
    except (OSError, ValueError) as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/compare-models")
async def compare_clothing_models(file: UploadFile = File(...)):

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload an image."
        )

    image_path = None
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="The uploaded image is empty.")
        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".image", dir=UPLOAD_DIR, delete=False
        ) as image_file:
            image_file.write(image_bytes)
            image_path = image_file.name
        return {"model_comparison": compare_models(image_path)}
    except HTTPException:
        raise
    except (OSError, ValueError) as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if image_path:
            try:
                os.remove(image_path)
            except OSError:
                pass

@app.get("/api/model-performance")
def model_performance():
    return {
        "models": [
            {"name": "VGG16", "accuracy": 84.30, "loss": 0.4507},
            {"name": "Custom CNN", "accuracy": 88.44, "loss": 0.3525},
            {"name": "ResNet50", "accuracy": 90.51, "loss": 0.2721},
        ]
    }

@app.post("/api/virtual-tryon")
async def virtual_tryon(
    person_image: UploadFile = File(...),
    garment_image: UploadFile = File(...),
    category: str = "upper_body",
):
    if category != "upper_body":
        raise HTTPException(
            status_code=400,
            detail="The current cloned model supports upper-body garments only. Select Upper body.",
        )
    for upload in (person_image, garment_image):
        if not upload.content_type or not upload.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Both inputs must be image files.")

    paths = []
    try:
        for label, upload in (("person", person_image), ("garment", garment_image)):
            image_bytes = await upload.read()
            if not image_bytes:
                raise HTTPException(status_code=400, detail=f"The {label} image is empty.")
            if len(image_bytes) > MAX_VTON_IMAGE_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"The {label} image must be smaller than 10 MB.",
                )
            suffix = Path(upload.filename or ".jpg").suffix.lower() or ".jpg"
            if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
                raise HTTPException(
                    status_code=400,
                    detail=f"The {label} image must be JPG, JPEG, PNG or WEBP.",
                )
            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=suffix, dir=VTON_DIR, delete=False
            ) as image_file:
                image_file.write(image_bytes)
                paths.append(Path(image_file.name))
            try:
                with Image.open(paths[-1]) as image:
                    width, height = image.size
                    image.verify()
                minimum_dimension = (
                    MIN_VTON_IMAGE_DIMENSION
                    if label == "person"
                    else MIN_GARMENT_IMAGE_DIMENSION
                )
                if width < minimum_dimension or height < minimum_dimension:
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"The {label} image is {width}x{height}px. "
                            f"It must be at least {minimum_dimension}x"
                            f"{minimum_dimension}px."
                        ),
                    )
                if label == "garment" and (
                    width < MIN_VTON_IMAGE_DIMENSION or height < MIN_VTON_IMAGE_DIMENSION
                ):
                    with Image.open(paths[-1]) as image:
                        scale = max(
                            MIN_VTON_IMAGE_DIMENSION / width,
                            MIN_VTON_IMAGE_DIMENSION / height,
                        )
                        resized = image.convert("RGB").resize(
                            (round(width * scale), round(height * scale)),
                            Image.Resampling.LANCZOS,
                        )
                        output_format = {
                            ".png": "PNG",
                            ".webp": "WEBP",
                        }.get(suffix, "JPEG")
                        save_options = {"quality": 95} if output_format in {"JPEG", "WEBP"} else {}
                        resized.save(paths[-1], format=output_format, **save_options)
            except HTTPException:
                raise
            except (OSError, ValueError) as error:
                raise HTTPException(
                    status_code=400,
                    detail=f"The {label} image is invalid or unreadable: {error}",
                ) from error
        try:
            output_data = generate_try_on(paths[0], paths[1], category)
        except VirtualTryOnUnavailable as error:
            raise HTTPException(status_code=503, detail=str(error)) from error
        return {"status": "succeeded", "generated_image_data": output_data}
    finally:
        for path in paths:
            try:
                path.unlink()
            except OSError:
                pass

@app.post("/api/search-similar")
async def search_similar(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image.")
    image_path = None
    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(status_code=400, detail="The uploaded image is empty.")
        if len(image_bytes) > 10 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="The image must be smaller than 10 MB.")
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".image", dir=VTON_DIR, delete=False) as image_file:
            image_file.write(image_bytes)
            image_path = image_file.name
        return {"products": similarity_index.find(image_path), "method": "HSV colour-distribution similarity"}
    except HTTPException:
        raise
    except (OSError, ValueError) as error:
        raise HTTPException(status_code=422, detail=f"Could not analyse image: {error}") from error
    finally:
        if image_path:
            try:
                Path(image_path).unlink()
            except OSError:
                pass
