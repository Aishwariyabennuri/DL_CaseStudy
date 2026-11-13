"""Image-based fitting service backed by the cloned repository."""

import base64
import io
import os
import subprocess
import tempfile
import shutil
from pathlib import Path

import numpy as np
import cv2
from PIL import Image


class VirtualTryOnUnavailable(RuntimeError):
    """Raised when the fitting pipeline cannot produce a result."""


def _load_backend_env() -> None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if key and key not in os.environ:
            os.environ[key] = value


def _encode_image(path: Path) -> str:
    try:
        with Image.open(path) as image:
            image.load()
            image_format = image.format
    except (OSError, ValueError) as error:
        raise VirtualTryOnUnavailable("The fitting pipeline returned an invalid image.") from error
    mime = "image/png" if image_format == "PNG" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def _skin_mask(image: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    hue, saturation, value = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    red, green, blue = image[..., 0], image[..., 1], image[..., 2]
    return (
        (hue < 35)
        & (saturation > 20)
        & (saturation < 150)
        & (value > 60)
        &
        (red > 95)
        & (green > 40)
        & (blue > 20)
        & ((red.astype(np.int16) - green.astype(np.int16)) > 15)
        & (red > blue * 1.1)
        & (red > green * 1.1)
    )


def _validate_coverage(output_path: Path, parse_path: Path) -> None:
    try:
        output = np.asarray(Image.open(output_path).convert("RGB"))
        parsing = np.asarray(Image.open(parse_path))
    except (OSError, ValueError) as error:
        raise VirtualTryOnUnavailable(
            "The generated fitting image or human parsing output is unreadable."
        ) from error
    # SCHP LIP labels: 5 upper-clothes, 6 dress, 7 coat, 9 pants,
    # 10 jumpsuits and 12 skirt. The cloned pipeline can receive any of
    # these labels even though its agnostic synthesis focuses on the upper
    # garment classes.
    garment_region = np.isin(parsing, [5, 6, 7, 9, 10, 12])
    region_size = int(garment_region.sum())
    if region_size < 1000:
        raise VirtualTryOnUnavailable(
            "Human parsing did not identify a usable garment region."
        )
    skin_ratio = float((_skin_mask(output) & garment_region).sum()) / region_size
    if skin_ratio > 0.60:
        raise VirtualTryOnUnavailable(
            "The generated fitting image failed the body-coverage safety check."
        )


def _copy_debug_artifacts(request_root: Path, debug_root: str) -> None:
    if not debug_root:
        return
    destination = Path(debug_root).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    for source in (
        request_root / "inputs" / "test" / "cloth-mask",
        request_root / "inputs" / "test" / "image",
        request_root / "inputs" / "test" / "image-parse",
        request_root / "inputs" / "test" / "openpose-img",
        request_root / "output" / "results",
    ):
        if source.exists():
            target = destination / source.name
            shutil.copytree(source, target, dirs_exist_ok=True)


def _repository_settings() -> tuple[Path, Path]:
    repository = Path(
        os.getenv(
            "VESTIAR_FITTING_REPOSITORY",
            Path(__file__).resolve().parents[2] / "clothes-virtual-try-on",
        )
    ).resolve()
    python_executable = Path(
        os.getenv(
            "VESTIAR_FITTING_PYTHON",
            repository / ".venv" / "Scripts" / "python.exe",
        )
    )
    if not repository.joinpath("run.py").exists() or not python_executable.exists():
        raise VirtualTryOnUnavailable(
            "The AI Fitting Room repository or its Python environment is unavailable."
        )
    return repository, python_executable


def _report_device(repository: Path, python_executable: Path) -> None:
    try:
        device_check = subprocess.run(
            [
                str(python_executable),
                "-c",
                "import torch; print('cuda' if torch.cuda.is_available() else 'cpu')",
            ],
            cwd=repository,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise VirtualTryOnUnavailable(
            "Could not inspect the AI Fitting Room execution device."
        ) from error
    device = device_check.stdout.strip()
    if device != "cuda":
        print(
            "[AI FITTING ROOM] CUDA was not detected; continuing with CPU inference. "
            "This can be very slow.",
            flush=True,
        )
    else:
        print("[AI FITTING ROOM] Using CUDA inference.", flush=True)


def generate_try_on(person_path: Path, garment_path: Path, category: str) -> str:
    """Run the cloned repository's original run_pipeline entry point."""
    del category
    _load_backend_env()
    repository, python_executable = _repository_settings()
    _report_device(repository, python_executable)

    with tempfile.TemporaryDirectory(prefix="vestiar-fitting-") as request_dir:
        request_root = Path(request_dir)
        inputs_dir = request_root / "inputs"
        cloth_dir = inputs_dir / "test" / "cloth"
        image_dir = inputs_dir / "test" / "image"
        output_dir = request_root / "output"
        cloth_dir.mkdir(parents=True)
        image_dir.mkdir(parents=True)
        Image.open(person_path).convert("RGB").save(image_dir / "person.jpg", "JPEG", quality=95)
        Image.open(garment_path).convert("RGB").save(cloth_dir / "garment.jpg", "JPEG", quality=95)

        try:
            process = subprocess.Popen(
                [
                    str(python_executable),
                    "-u",
                    str(repository / "run.py"),
                    "--inputs_dir",
                    str(inputs_dir),
                    "--output_dir",
                    str(output_dir),
                    "--checkpoints_dir",
                    str(repository / "checkpoints"),
                ],
                cwd=repository,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            output_lines = []
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                output_lines.append(line)
                print(line, end="", flush=True)
            process.wait(timeout=900)
            if process.returncode:
                raise subprocess.CalledProcessError(
                    process.returncode,
                    process.args,
                    output="".join(output_lines),
                )
        except subprocess.TimeoutExpired as error:
            process.kill()
            process.communicate()
            raise VirtualTryOnUnavailable(
                "AI Fitting Room inference timed out."
            ) from error
        except subprocess.CalledProcessError as error:
            detail = (error.output or "unknown inference error")[-1000:]
            raise VirtualTryOnUnavailable(
                f"AI Fitting Room inference failed: {detail}"
            ) from error

        results = sorted((output_dir / "results").glob("*"))
        if not results:
            raise VirtualTryOnUnavailable(
                "AI Fitting Room inference produced no generated image."
            )
        parse_outputs = sorted((inputs_dir / "test" / "image-parse").glob("*.png"))
        if len(parse_outputs) != 1:
            raise VirtualTryOnUnavailable(
                "AI Fitting Room did not produce exactly one human parsing output."
            )
        _validate_coverage(results[0], parse_outputs[0])
        _copy_debug_artifacts(
            request_root,
            os.getenv("VESTIAR_FITTING_DEBUG_DIR", ""),
        )
        return _encode_image(results[0])
