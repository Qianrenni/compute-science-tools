import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox


def delete_empty_folders(root_dir):
    deleted_count = 0
    # 遍历目录树，从下往上遍历，先删掉深层的空目录
    for dirpath, dirs, files in os.walk(root_dir, topdown=False):
        for d in dirs:
            full_path = os.path.join(dirpath, d)
            if not os.listdir(full_path):  # 如果目录为空
                try:
                    os.rmdir(full_path)
                    print(f"已删除空目录: {full_path}")
                    deleted_count += 1
                except Exception as e:
                    print(f"无法删除目录 {full_path}: {e}")
    return deleted_count


def select_directory():
    directory = filedialog.askdirectory()
    if directory:
        confirm = messagebox.askyesno("确认操作", f"确定要删除目录 '{directory}' 下的所有空目录吗？")
        if confirm:
            count = delete_empty_folders(directory)
            messagebox.showinfo("完成", f"已删除 {count} 个空目录。")


# 创建主窗口
root = tk.Tk()
root.title("删除空目录工具")
root.geometry("400x200")

label = tk.Label(root, text="点击按钮选择一个目录，将删除其中的所有空子目录：", wraplength=350, justify="center")
label.pack(pady=20)

button = tk.Button(root, text="选择目录并清理", command=select_directory)
button.pack(pady=10)

# 启动GUI
root.mainloop()