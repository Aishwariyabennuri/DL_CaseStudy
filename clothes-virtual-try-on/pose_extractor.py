import os
import sys
import json
import argparse
import numpy as np
import cv2
import urllib.request
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# OpenPose BODY_25 limb connections (pairs of joint indices)
BODY_25_PAIRS = [
    (1, 8), (1, 2), (1, 5), (2, 3), (3, 4), (5, 6), (6, 7), (8, 9), (9, 10),
    (10, 11), (8, 12), (12, 13), (13, 14), (1, 0), (0, 15), (15, 17), (0, 16),
    (16, 18), (14, 19), (19, 20), (14, 21), (11, 22), (22, 23), (11, 24)
]

# Standard OpenPose BGR limb colors
LIMB_COLORS = [
    [255, 0, 85], [255, 0, 0], [255, 85, 0], [255, 170, 0], [255, 255, 0],
    [170, 255, 0], [85, 255, 0], [0, 255, 0], [0, 255, 85], [0, 255, 170],
    [0, 255, 255], [0, 170, 255], [0, 85, 255], [0, 0, 255], [255, 0, 170],
    [170, 0, 255], [255, 0, 255], [85, 0, 255], [0, 0, 255], [0, 0, 255],
    [0, 0, 255], [0, 255, 255], [0, 255, 255], [0, 255, 255]
]

JOINT_COLORS = [
    [255, 0, 0], [255, 85, 0], [255, 170, 0], [255, 255, 0], [170, 255, 0],
    [85, 255, 0], [0, 255, 0], [0, 255, 85], [0, 255, 170], [0, 255, 255],
    [0, 170, 255], [0, 85, 255], [0, 0, 255], [255, 0, 170], [170, 0, 255],
    [255, 0, 255], [85, 0, 255], [0, 0, 255], [0, 0, 255], [0, 0, 255],
    [0, 255, 255], [0, 255, 255], [0, 255, 255], [0, 255, 255], [0, 255, 255]
]

def ensure_model_downloaded(model_path="pose_landmarker.task"):
    if not os.path.exists(model_path):
        print(f"Downloading MediaPipe pose landmarker model to {model_path}...")
        url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/latest/pose_landmarker_full.task"
        urllib.request.urlretrieve(url, model_path)
    return model_path

def mediapipe_to_body25(landmarks, w, h):
    """
    Map 33 MediaPipe pose landmarks to OpenPose 25 keypoints.
    Returns: list of 25 (x, y, confidence)
    """
    pts = np.zeros((25, 3), dtype=np.float32)
    if not landmarks:
        return pts

    def get_pt(idx):
        lm = landmarks[idx]
        return np.array([lm.x * w, lm.y * h, lm.visibility or 0.9])

    # MediaPipe landmarks:
    # 0: nose, 2: left_eye, 5: right_eye, 7: left_ear, 8: right_ear
    # 11: left_shoulder, 12: right_shoulder, 13: left_elbow, 14: right_elbow, 15: left_wrist, 16: right_wrist
    # 23: left_hip, 24: right_hip, 25: left_knee, 26: right_knee, 27: left_ankle, 28: right_ankle
    # 29: left_heel, 30: right_heel, 31: left_foot_index, 32: right_foot_index

    # 0: Nose
    pts[0] = get_pt(0)
    # 1: Neck = midpoint of left and right shoulder
    ls, rs = get_pt(11), get_pt(12)
    pts[1] = [(ls[0] + rs[0]) / 2.0, (ls[1] + rs[1]) / 2.0, min(ls[2], rs[2])]
    # 2: RShoulder
    pts[2] = get_pt(12)
    # 3: RElbow
    pts[3] = get_pt(14)
    # 4: RWrist
    pts[4] = get_pt(16)
    # 5: LShoulder
    pts[5] = get_pt(11)
    # 6: LElbow
    pts[6] = get_pt(13)
    # 7: LWrist
    pts[7] = get_pt(15)
    # 8: MidHip = midpoint of left and right hip
    lh, rh = get_pt(23), get_pt(24)
    pts[8] = [(lh[0] + rh[0]) / 2.0, (lh[1] + rh[1]) / 2.0, min(lh[2], rh[2])]
    # 9: RHip
    pts[9] = get_pt(24)
    # 10: RKnee
    pts[10] = get_pt(26)
    # 11: RAnkle
    pts[11] = get_pt(28)
    # 12: LHip
    pts[12] = get_pt(23)
    # 13: LKnee
    pts[13] = get_pt(25)
    # 14: LAnkle
    pts[14] = get_pt(27)
    # 15: REye
    pts[15] = get_pt(5)
    # 16: LEye
    pts[16] = get_pt(2)
    # 17: REar
    pts[17] = get_pt(8)
    # 18: LEar
    pts[18] = get_pt(7)
    # 19: LBigToe
    pts[19] = get_pt(31)
    # 20: LSmallToe
    pts[20] = get_pt(31)
    # 21: LHeel
    pts[21] = get_pt(29)
    # 22: RBigToe
    pts[22] = get_pt(32)
    # 23: RSmallToe
    pts[23] = get_pt(32)
    # 24: RHeel
    pts[24] = get_pt(30)

    return pts

def render_body25_skeleton(pts, w, h):
    """
    Renders standard OpenPose stick figure skeleton on black image.
    """
    canvas = np.zeros((h, w, 3), dtype=np.uint8)

    # Draw limbs
    for i, (j1, j2) in enumerate(BODY_25_PAIRS):
        p1 = pts[j1]
        p2 = pts[j2]
        if p1[2] > 0.05 and p2[2] > 0.05:
            pt1 = (int(round(p1[0])), int(round(p1[1])))
            pt2 = (int(round(p2[0])), int(round(p2[1])))
            color = LIMB_COLORS[i % len(LIMB_COLORS)]
            cv2.line(canvas, pt1, pt2, color, thickness=8, lineType=cv2.LINE_AA)

    # Draw joints
    for j in range(25):
        pj = pts[j]
        if pj[2] > 0.05:
            center = (int(round(pj[0])), int(round(pj[1])))
            color = JOINT_COLORS[j % len(JOINT_COLORS)]
            cv2.circle(canvas, center, radius=6, color=color, thickness=-1, lineType=cv2.LINE_AA)

    return canvas

def process_images(image_dir, json_dir, img_out_dir, model_path="pose_landmarker.task"):
    ensure_model_downloaded(model_path)
    os.makedirs(json_dir, exist_ok=True)
    os.makedirs(img_out_dir, exist_ok=True)

    base_options = python.BaseOptions(model_asset_path=model_path)
    options = vision.PoseLandmarkerOptions(
        base_options=base_options,
        output_segmentation_masks=False,
        num_poses=1,
        min_pose_detection_confidence=0.3,
        min_pose_presence_confidence=0.3,
        min_tracking_confidence=0.3
    )
    detector = vision.PoseLandmarker.create_from_options(options)

    valid_exts = ('.jpg', '.jpeg', '.png')
    image_files = [f for f in os.listdir(image_dir) if f.lower().endswith(valid_exts)]
    print(f"Found {len(image_files)} images in {image_dir} for pose extraction.")

    for img_file in image_files:
        img_path = os.path.join(image_dir, img_file)
        base_name = os.path.splitext(img_file)[0]
        
        cv_img = cv2.imread(img_path)
        if cv_img is None:
            continue
        h, w = cv_img.shape[:2]

        rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_img)
        result = detector.detect(mp_image)

        if result.pose_landmarks and len(result.pose_landmarks) > 0:
            landmarks = result.pose_landmarks[0]
            pts = mediapipe_to_body25(landmarks, w, h)
        else:
            print(f"Warning: No pose detected in {img_file}. Using zero pose.")
            pts = np.zeros((25, 3), dtype=np.float32)

        # 1. Save JSON in OpenPose BODY_25 format
        flat_keypoints = pts.flatten().tolist()
        json_data = {
            "version": 1.3,
            "people": [
                {
                    "person_id": [-1],
                    "pose_keypoints_2d": flat_keypoints,
                    "face_keypoints_2d": [],
                    "hand_left_keypoints_2d": [],
                    "hand_right_keypoints_2d": [],
                    "pose_keypoints_3d": [],
                    "face_keypoints_3d": [],
                    "hand_left_keypoints_3d": [],
                    "hand_right_keypoints_3d": []
                }
            ]
        }
        json_path = os.path.join(json_dir, f"{base_name}_keypoints.json")
        with open(json_path, "w") as f:
            json.dump(json_data, f)

        # 2. Save Rendered skeleton image
        rendered_skeleton = render_body25_skeleton(pts, w, h)
        out_img_path = os.path.join(img_out_dir, f"{base_name}_rendered.png")
        cv2.imwrite(out_img_path, rendered_skeleton)

        print(f"Processed pose for {img_file} -> {json_path}, {out_img_path}")

def main():
    parser = argparse.ArgumentParser(description="Pure-Python OpenPose BODY_25 Extractor using MediaPipe")
    parser.add_argument("--image_dir", type=str, required=True, help="Directory of model human images")
    parser.add_argument("--json_dir", type=str, required=True, help="Output directory for openpose-json")
    parser.add_argument("--img_dir", type=str, required=True, help="Output directory for openpose-img")
    parser.add_argument("--model_path", type=str, default="pose_landmarker.task", help="Path to pose_landmarker.task")
    args = parser.parse_args()

    process_images(args.image_dir, args.json_dir, args.img_dir, args.model_path)

if __name__ == "__main__":
    main()
