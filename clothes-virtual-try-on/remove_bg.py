import os
import argparse
from PIL import Image
import numpy as np
from rembg import remove


class PreprocessInput:
    def __init__(self):
        self.o_image = None

    def process_image(self, file_path: str, width: int = 768, height: int = 1024):
        pic = Image.open(file_path).convert('RGB')
        # Remove background using rembg
        no_bg = remove(pic)
        
        scale = min(width / no_bg.width, height / no_bg.height)
        resized_size = (max(1, round(no_bg.width * scale)), max(1, round(no_bg.height * scale)))
        no_bg_resized = no_bg.resize(resized_size, Image.LANCZOS)
        
        # Place onto white background
        background = Image.new("RGBA", (width, height), (255, 255, 255, 255))
        offset = ((width - no_bg_resized.width) // 2, (height - no_bg_resized.height) // 2)
        if no_bg_resized.mode == "RGBA":
            background.paste(no_bg_resized, offset, mask=no_bg_resized.split()[3])
        else:
            background.paste(no_bg_resized, offset)
            
        final_img = background.convert('RGB')
        
        # Save back as JPEG to keep same format
        save_path = os.path.splitext(file_path)[0] + '.jpg'
        final_img.save(save_path, 'JPEG', quality=95)
        print(f"Removed background and standardized: {save_path}")
        return save_path


def process_all_images(image_dir: str, width: int = 768, height: int = 1024):
    preprocessor = PreprocessInput()
    valid_exts = ('.jpg', '.jpeg', '.png')
    images = [f for f in os.listdir(image_dir) if f.lower().endswith(valid_exts)]
    print(f"Found {len(images)} images to process in {image_dir}")

    for img_name in images:
        full_path = os.path.join(image_dir, img_name)
        preprocessor.process_image(full_path, width=width, height=height)


def main():
    parser = argparse.ArgumentParser(description="Remove background and normalize model image to white background")
    parser.add_argument("--image_dir", type=str, default="inputs/test/image")
    parser.add_argument("--width", type=int, default=768)
    parser.add_argument("--height", type=int, default=1024)
    args = parser.parse_args()

    process_all_images(args.image_dir, width=args.width, height=args.height)


if __name__ == "__main__":
    main()
