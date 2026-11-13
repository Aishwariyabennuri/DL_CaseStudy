import os
import sys
import gdown

def download_file(file_id, output_path):
    if os.path.exists(output_path) and os.path.getsize(output_path) > 1024 * 1024:
        print(f"[ALREADY EXISTS] {output_path} ({os.path.getsize(output_path) / (1024*1024):.2f} MB)")
        return True
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    print(f"[DOWNLOADING] {output_path} from Google Drive ID: {file_id} ...")
    
    try:
        gdown.download(id=file_id, output=output_path, quiet=False)
        if os.path.exists(output_path) and os.path.getsize(output_path) > 1024:
            print(f"[SUCCESS] Downloaded {output_path} ({os.path.getsize(output_path) / (1024*1024):.2f} MB)")
            return True
        else:
            print(f"[WARNING] Downloaded file seems too small: {output_path}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to download {output_path}: {e}")
        return False

def main():
    base_dir = os.path.abspath(os.path.dirname(__file__))
    checkpoints_dir = os.path.join(base_dir, "checkpoints")
    schp_checkpoints_dir = os.path.join(base_dir, "Self-Correction-Human-Parsing", "checkpoints")
    
    models = [
        # Cloth segmentation (U2NET)
        ("1ysEoAJNxou7RNuT9iKOxRhjVRNY5RLjx", os.path.join(base_dir, "cloth_segm_u2net_latest.pth")),
        # Try-on models
        ("18q4lS7cNt1_X8ewCgya1fq0dSk93jTL6", os.path.join(checkpoints_dir, "alias_final.pth")),
        ("1uDRPY8gh9sHb3UDonq6ZrINqDOd7pmTz", os.path.join(checkpoints_dir, "gmm_final.pth")),
        ("1d7lZNLh51Qt5Mi1lXqyi6Asb2ncLrEdC", os.path.join(checkpoints_dir, "seg_final.pth")),
        # SCHP Human parsing model
        ("1k4dllHpu0bdx38J7H28rVVLpU-kOHmnH", os.path.join(schp_checkpoints_dir, "final.pth")),
    ]
    
    print("=" * 60)
    print("Checking and downloading required model checkpoints...")
    print("=" * 60)
    
    all_ok = True
    for file_id, out_path in models:
        ok = download_file(file_id, out_path)
        if not ok:
            all_ok = False
            
    if all_ok:
        print("\nAll model checkpoints are ready!")
    else:
        print("\nSome checkpoints failed to download. Check network or drive permissions.")

if __name__ == "__main__":
    main()
