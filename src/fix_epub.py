import copy
import os
import tkinter as tk
from tkinter import filedialog, messagebox
import ebooklib
from ebooklib import epub


def fix_epub_cover(input_path, output_path):
    """
    正确修复 EPUB 封面的方法：
    - 查找最合适的封面图片
    - 删除原图（可选）
    - 创建新的 ITEM_COVER 类型项并添加进书籍
    """
    book = epub.read_epub(input_path)

    # 1️⃣ 检查是否有现有封面
    existing_cover = next((item for item in book.get_items() if item.get_type() == ebooklib.ITEM_COVER), None)
    if existing_cover:
        print(f"✅ '{os.path.basename(input_path)}' 已存在封面，跳过处理")
        return False

    # 2️⃣ 获取所有图片项
    images = list(book.get_items_of_type(ebooklib.ITEM_IMAGE))
    if not images:
        print(f"❌ '{os.path.basename(input_path)}' 中没有找到任何图片")
        return False

    # 3️⃣ 找出最可能是封面的图片（根据文件名关键词）
    possible_covers = []
    for item in images:
        filename = item.file_name.lower()
        score = 0
        if 'cover' in filename:
            score += 1
        if 'thumb' in filename:
            score += 1
        if 'front' in filename:
            score += 1
        if 'title' in filename:
            score += 1
        possible_covers.append((score, item))

    # 排序后取最高分的图片作为封面候选
    possible_covers.sort(reverse=True, key=lambda x: x[0])
    best_guess = possible_covers[0][1]
    print(f"📎 确定封面来源图片: {best_guess.file_name}")
    book.items.remove(best_guess)
    book.set_cover(file_name=best_guess.file_name,content=best_guess.content)
    # 7️⃣ 写入修复后的 EPUB 文件
    epub.write_epub(output_path, book)
    print(f"✅ '{os.path.basename(input_path)}' 封面已修复，新封面保存为: {best_guess.file_name}")
    return True
def process_directory(folder_path):
    """
    处理整个目录下的所有 .epub 文件
    """
    count_fixed = 0
    count_skipped = 0

    for filename in os.listdir(folder_path):
        if filename.lower().endswith('.epub'):
            input_path = os.path.join(folder_path, filename)
            output_path = os.path.join(folder_path, f"{os.path.splitext(filename)[0]}_fixed.epub")

            if os.path.exists(output_path):
                print(f"⚠️ 已存在修复文件，跳过: {filename}")
                count_skipped += 1
                continue

            try:
                success = fix_epub_cover(input_path, output_path)
                if success:
                    count_fixed += 1
                else:
                    count_skipped += 1
            except Exception as e:
                print(f"❌ 处理失败: {filename}，错误: {str(e)}")
                count_skipped += 1

    messagebox.showinfo("完成", f"修复完成！\n共修复: {count_fixed} 本\n跳过/失败: {count_skipped} 本")


def select_mode():
    """
    GUI 主界面：选择单个文件或整个目录
    """
    root = tk.Tk()
    root.title("EPUB 封面修复工具 - 已更新 set_type()")
    root.geometry("400x200")

    def on_single_file():
        epub_path = filedialog.askopenfilename(title="选择 EPUB 文件", filetypes=[("EPUB 文件", "*.epub")])
        if epub_path:
            output_path = os.path.splitext(epub_path)[0] + "_fixed.epub"
            if os.path.exists(output_path):
                messagebox.showwarning("警告", "修复文件已存在，跳过处理。")
                return
            try:
                success = fix_epub_cover(epub_path, output_path)
                if success:
                    messagebox.showinfo("成功", f"封面已修复，新文件保存为:\n{output_path}")
                else:
                    messagebox.showinfo("提示", "该书已有封面，无需修复。")
            except Exception as e:
                messagebox.showerror("错误", f"处理失败: {str(e)}")

    def on_folder():
        folder_path = filedialog.askdirectory(title="选择包含 EPUB 的文件夹")
        if folder_path:
            process_directory(folder_path)

    label = tk.Label(root, text="请选择操作方式", font=("Arial", 14))
    label.pack(pady=20)

    single_button = tk.Button(root, text="选择单个 EPUB 文件修复", command=on_single_file, width=30)
    single_button.pack(pady=5)

    folder_button = tk.Button(root, text="选择文件夹批量修复所有 EPUB", command=on_folder, width=30)
    folder_button.pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    select_mode()