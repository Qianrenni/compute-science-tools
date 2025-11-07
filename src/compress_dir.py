import os
import zipfile
import sys

def compress_folder_with_dotfiles(folder_path, output_path=None):
    """
    压缩指定文件夹为 ZIP 文件，**明确包含所有隐藏文件（如 .git）**
    """
    if not os.path.isdir(folder_path):
        print(f"❌ 错误：'{folder_path}' 不是一个有效的文件夹。")
        return False

    if output_path is None:
        parent_dir = os.path.dirname(os.path.abspath(folder_path))
        folder_name = os.path.basename(os.path.abspath(folder_path))
        output_path = os.path.join(parent_dir, folder_name + '.zip')

    print(f"📦 正在压缩文件夹（包含 .git 等隐藏文件）: '{folder_path}'")
    print(f"💾 输出到: '{output_path}'")

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full_path = os.path.join(root, file)
                # 计算在 ZIP 中的相对路径（以父目录为基准，保留文件夹名）
                arcname = os.path.relpath(full_path, os.path.dirname(folder_path))
                zipf.write(full_path, arcname)
                print(f"  ➕ {arcname}")

    print(f"\n✅ 压缩完成！共包含所有文件（含 .git）")
    return True

def main():
    if len(sys.argv) < 2:
        print("用法: python compress_folder.py <文件夹路径> [输出ZIP路径]")
        print("示例: python compress_folder.py ./my_project")
        return

    folder = sys.argv[1]
    output = sys.argv[2] if len(sys.argv) > 2 else None

    compress_folder_with_dotfiles(folder, output)

if __name__ == "__main__":
    main()