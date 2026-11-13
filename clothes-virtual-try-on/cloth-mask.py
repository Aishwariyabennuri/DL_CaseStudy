import os
import argparse
from PIL import Image
import numpy as np
from collections import OrderedDict

import torch
import torch.nn.functional as F
import torchvision.transforms as transforms

from networks.u2net import U2NET


def load_checkpoint_mgpu(model, checkpoint_path, device):
    if not os.path.exists(checkpoint_path):
        print(f"----No checkpoints at given path: {checkpoint_path}----")
        return None
    model_state_dict = torch.load(checkpoint_path, map_location=device)
    new_state_dict = OrderedDict()
    for k, v in model_state_dict.items():
        name = k[7:] if k.startswith("module.") else k
        new_state_dict[name] = v

    model.load_state_dict(new_state_dict)
    print(f"----checkpoints loaded from path: {checkpoint_path}----")
    return model


class Normalize_image(object):
    def __init__(self, mean, std):
        self.mean = mean
        self.std = std
        self.normalize_1 = transforms.Normalize(self.mean, self.std)
        self.normalize_3 = transforms.Normalize([self.mean] * 3, [self.std] * 3)

    def __call__(self, image_tensor):
        if image_tensor.shape[0] == 1:
            return self.normalize_1(image_tensor)
        elif image_tensor.shape[0] == 3:
            return self.normalize_3(image_tensor)
        return image_tensor


def get_palette(num_cls):
    palette = [0] * (num_cls * 3)
    for j in range(num_cls):
        lab = j
        palette[j * 3 + 0] = 0
        palette[j * 3 + 1] = 0
        palette[j * 3 + 2] = 0
        while lab:
            palette[j * 3 + 0] = 255
            palette[j * 3 + 1] = 255
            palette[j * 3 + 2] = 255
            lab >>= 3
    return palette


def process_cloth_masks(image_dir, result_dir, checkpoint_path):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Cloth mask processing using device: {device}")

    os.makedirs(result_dir, exist_ok=True)

    transform_rgb = transforms.Compose([
        transforms.ToTensor(),
        Normalize_image(0.5, 0.5)
    ])

    net = U2NET(in_ch=3, out_ch=4)
    net = load_checkpoint_mgpu(net, checkpoint_path, device)
    if net is None:
        raise FileNotFoundError(f"Missing checkpoint: {checkpoint_path}")
    net = net.to(device).eval()

    palette = get_palette(4)
    valid_exts = ('.jpg', '.jpeg', '.png')
    images_list = sorted([f for f in os.listdir(image_dir) if f.lower().endswith(valid_exts)])

    with torch.no_grad():
        for image_name in images_list:
            img_path = os.path.join(image_dir, image_name)
            img = Image.open(img_path).convert('RGB')
            img_size = img.size
            img_resized = img.resize((768, 768), Image.BICUBIC)
            image_tensor = transform_rgb(img_resized).unsqueeze(0).to(device)

            output_tensor = net(image_tensor)
            output_tensor = F.log_softmax(output_tensor[0], dim=1)
            output_tensor = torch.max(output_tensor, dim=1, keepdim=True)[1]
            output_tensor = output_tensor.squeeze().cpu().numpy()

            output_img = Image.fromarray(output_tensor.astype('uint8'), mode='L')
            output_img = output_img.resize(img_size, Image.BICUBIC)
            output_img.putpalette(palette)
            output_img = output_img.convert('L')
            
            base_name = os.path.splitext(image_name)[0]
            out_file = os.path.join(result_dir, f"{base_name}.jpg")
            output_img.save(out_file)
            print(f"Generated cloth mask: {out_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate cloth segmentation masks with U2Net")
    parser.add_argument("--image_dir", type=str, default="inputs/test/cloth")
    parser.add_argument("--result_dir", type=str, default="inputs/test/cloth-mask")
    parser.add_argument("--checkpoint_path", type=str, default="cloth_segm_u2net_latest.pth")
    args = parser.parse_args()

    process_cloth_masks(args.image_dir, args.result_dir, args.checkpoint_path)


if __name__ == "__main__":
    main()
