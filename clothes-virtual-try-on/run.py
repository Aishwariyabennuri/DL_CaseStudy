import os
import sys
import shutil
import subprocess
import argparse
from PIL import Image

VALID_IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png')


def resize_img(path, size=(768, 1024)):
    image = Image.open(path).convert("RGB")
    scale = min(size[0] / image.width, size[1] / image.height)
    resized_size = (max(1, round(image.width * scale)), max(1, round(image.height * scale)))
    resized = image.resize(resized_size, Image.LANCZOS)
    canvas = Image.new("RGB", size, "white")
    offset = ((size[0] - resized.width) // 2, (size[1] - resized.height) // 2)
    canvas.paste(resized, offset)
    canvas.save(path, quality=95)


def validate_pose(json_dir):
    keypoint_files = [
        os.path.join(json_dir, name)
        for name in os.listdir(json_dir)
        if name.endswith("_keypoints.json")
    ]
    if len(keypoint_files) != 1:
        raise ValueError("Pose extraction must produce exactly one keypoint file.")
    import json
    with open(keypoint_files[0], "r", encoding="utf-8") as pose_file:
        people = json.load(pose_file).get("people", [])
    if not people:
        raise ValueError("Pose extraction did not detect a person.")
    keypoints = people[0].get("pose_keypoints_2d", [])
    confidences = keypoints[2::3]
    required_indices = [1, 2, 5, 8, 9, 12]
    if any(index >= len(confidences) or confidences[index] < 0.2 for index in required_indices):
        raise ValueError("Pose extraction did not detect the required shoulders and hips.")

def run_pipeline(inputs_dir="inputs", output_dir="output", checkpoints_dir="checkpoints", debug_dir=""):
    base_dir = os.path.abspath(os.path.dirname(__file__))
    python_exe = sys.executable

    test_dir = os.path.join(inputs_dir, "test")
    cloth_dir = os.path.join(test_dir, "cloth")
    cloth_mask_dir = os.path.join(test_dir, "cloth-mask")
    image_dir = os.path.join(test_dir, "image")
    image_parse_dir = os.path.join(test_dir, "image-parse")
    openpose_json_dir = os.path.join(test_dir, "openpose-json")
    openpose_img_dir = os.path.join(test_dir, "openpose-img")

    for d in [cloth_mask_dir, image_parse_dir, openpose_json_dir, openpose_img_dir, output_dir]:
        os.makedirs(d, exist_ok=True)

    print("=" * 60)
    print("STEP 1: Resizing cloth images to (768, 1024)...")
    print("=" * 60)
    for f in sorted(os.listdir(cloth_dir)):
        if f.lower().endswith(VALID_IMAGE_EXTENSIONS):
            resize_img(os.path.join(cloth_dir, f))

    print("\n" + "=" * 60)
    print("STEP 2: Generating cloth mask (U2Net)...")
    print("=" * 60)
    cloth_mask_script = os.path.join(base_dir, "cloth-mask.py")
    u2net_ckpt = os.path.join(base_dir, "cloth_segm_u2net_latest.pth")
    if not os.path.exists(u2net_ckpt):
        u2net_ckpt = os.path.join(checkpoints_dir, "cloth_segm_u2net_latest.pth")
    subprocess.run([
        python_exe, cloth_mask_script,
        "--image_dir", cloth_dir,
        "--result_dir", cloth_mask_dir,
        "--checkpoint_path", u2net_ckpt
    ], check=True)

    print("\n" + "=" * 60)
    print("STEP 3: Removing background and normalizing human image...")
    print("=" * 60)
    remove_bg_script = os.path.join(base_dir, "remove_bg.py")
    subprocess.run([
        python_exe, remove_bg_script,
        "--image_dir", image_dir,
        "--width", "768",
        "--height", "1024"
    ], check=True)

    print("\n" + "=" * 60)
    print("STEP 4: Human Parsing (SCHP)...")
    print("=" * 60)
    schp_script = os.path.join(base_dir, "Self-Correction-Human-Parsing", "simple_extractor.py")
    schp_ckpt = os.path.join(base_dir, "Self-Correction-Human-Parsing", "checkpoints", "final.pth")
    subprocess.run([
        python_exe, schp_script,
        "--dataset", "lip",
        "--model-restore", schp_ckpt,
        "--input-dir", image_dir,
        "--output-dir", image_parse_dir,
        "--gpu", "None"
    ], check=True)

    print("\n" + "=" * 60)
    print("STEP 5: Pose Estimation (BODY_25 via MediaPipe)...")
    print("=" * 60)
    pose_script = os.path.join(base_dir, "pose_extractor.py")
    subprocess.run([
        python_exe, pose_script,
        "--image_dir", image_dir,
        "--json_dir", openpose_json_dir,
        "--img_dir", openpose_img_dir
    ], check=True)
    validate_pose(openpose_json_dir)

    print("\n" + "=" * 60)
    print("STEP 6: Building pairs and synthesizing Try-On result (test.py)...")
    print("=" * 60)
    model_images = sorted([f for f in os.listdir(image_dir) if f.lower().endswith(VALID_IMAGE_EXTENSIONS)])
    cloth_images = sorted([f for f in os.listdir(cloth_dir) if f.lower().endswith(VALID_IMAGE_EXTENSIONS)])
    if len(model_images) != 1 or len(cloth_images) != 1:
        raise ValueError(
            "The fitting pipeline requires exactly one human image and one garment image."
        )

    pairs_file = os.path.join(inputs_dir, "test_pairs.txt")
    with open(pairs_file, 'w') as f:
        for m, c in zip(model_images, cloth_images):
            f.write(f"{m} {c}\n")

    test_script = os.path.join(base_dir, "test.py")
    test_command = [
        python_exe, test_script,
        "--name", "results",
        "--dataset_dir", inputs_dir,
        "--checkpoint_dir", checkpoints_dir,
        "--save_dir", output_dir
    ]
    if debug_dir:
        test_command.extend(["--debug_dir", debug_dir])
    subprocess.run(test_command, check=True)

    result_folder = os.path.join(output_dir, "results")
    print(f"\n[SUCCESS] Pipeline complete! Output generated in: {result_folder}")
    return result_folder

def main():
    parser = argparse.ArgumentParser(description="Run Virtual Try-On Pipeline")
    parser.add_argument("--inputs_dir", type=str, default="inputs", help="Path to inputs directory")
    parser.add_argument("--output_dir", type=str, default="output", help="Path to output directory")
    parser.add_argument("--checkpoints_dir", type=str, default="checkpoints", help="Path to checkpoints directory")
    parser.add_argument("--debug_dir", type=str, default="", help="Optional private directory for stage diagnostics")
    args = parser.parse_args()

    run_pipeline(args.inputs_dir, args.output_dir, args.checkpoints_dir, args.debug_dir)

if __name__ == "__main__":
    main()
