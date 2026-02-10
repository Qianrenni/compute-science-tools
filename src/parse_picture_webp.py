import os

from PIL import Image


def convert_images_to_webp(root_directory, quality=80):
    """
    递归遍历指定目录及其所有子目录，将所有 .jpg、.jpeg 和 .png 文件转换为 .webp 格式，并删除原文件。
    :param root_directory: 要处理的根目录路径
    :param quality: WebP 图像质量（0-100，默认80）
    """
    # 扩展支持的文件后缀，增加 .png
    supported_formats = ('.jpg', '.jpeg', '.png')
    for dirpath, dirnames, filenames in os.walk(root_directory):
        for filename in filenames:
            if filename.lower().endswith(supported_formats):
                filepath = os.path.join(dirpath, filename)
                webp_filename = os.path.splitext(filename)[0] + ".webp"
                webp_path = os.path.join(dirpath, webp_filename)

                try:
                    with Image.open(filepath) as img:
                        # 处理图像模式：PNG 可能是 RGBA（带透明通道），WebP 支持 RGBA，无需转为 RGB
                        # 仅对非 RGBA/RGB 的模式做兼容转换，优先保留原模式（避免丢失透明通道）
                        if img.mode not in ("RGB", "RGBA"):
                            # 有透明通道需求则转 RGBA，否则转 RGB
                            img = img.convert("RGBA") if "A" in img.mode else img.convert("RGB")

                        # 保存为 WebP，保持原有透明通道（如果有）
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

    convert_images_to_webp(target_dir)