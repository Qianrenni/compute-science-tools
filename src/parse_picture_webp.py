import os

from PIL import Image


def convert_jpg_to_webp(root_directory, quality=80):
    """
    递归遍历指定目录及其所有子目录，将所有 .jpg 和 .jpeg 文件转换为 .webp 格式，并删除原文件。
    :param root_directory: 要处理的根目录路径
    :param quality: WebP 图像质量（0-100，默认80）
    """
    for dirpath, dirnames, filenames in os.walk(root_directory):
        for filename in filenames:
            if filename.lower().endswith(('.jpg', '.jpeg')):
                filepath = os.path.join(dirpath, filename)
                webp_filename = os.path.splitext(filename)[0] + ".webp"
                webp_path = os.path.join(dirpath, webp_filename)

                try:
                    with Image.open(filepath) as img:
                        # JPG/JPEG 通常是 'RGB'，但为安全起见，统一转为 RGB
                        if img.mode != "RGB":
                            img = img.convert("RGB")

                        # 保存为 WebP
                        img.save(webp_path, "WEBP", quality=quality, method=6)

                        # 删除原文件
                        os.remove(filepath)
                        print(f"✅ 转换并删除: {filepath} → {webp_path}")

                except Exception as e:
                    print(f"❌ 转换失败: {filepath} - {e}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("用法: python convert_to_webp.py <目录路径>")
        sys.exit(1)

    target_dir = sys.argv[1]
    if not os.path.isdir(target_dir):
        print("错误: 指定路径不是有效目录")
        sys.exit(1)

    convert_jpg_to_webp(target_dir)
