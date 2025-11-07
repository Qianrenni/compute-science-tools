import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import threading
import uuid


# === 加密/解密核心逻辑 ===
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
TAG_SIZE = 16

def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=100_000,
    )
    return kdf.derive(password.encode())

def encrypt_file(password: str, input_path: Path, output_path: Path):
    try:
        salt = os.urandom(SALT_SIZE)
        key = derive_key(password, salt)
        aesgcm = AESGCM(key)

        with open(input_path, 'rb') as f:
            data = f.read()

        nonce = os.urandom(NONCE_SIZE)
        ciphertext = aesgcm.encrypt(nonce, data, None)

        with open(output_path, 'wb') as f:
            f.write(salt + nonce + ciphertext)
    except Exception as e:
        raise RuntimeError(f"加密失败 {input_path.name}: {e}")

def decrypt_file(password: str, input_path: Path, output_path: Path):
    try:
        with open(input_path, 'rb') as f:
            data = f.read()

        if len(data) < SALT_SIZE + NONCE_SIZE + TAG_SIZE:
            raise ValueError("文件太小，可能已损坏")

        salt = data[:SALT_SIZE]
        nonce = data[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
        ciphertext = data[SALT_SIZE + NONCE_SIZE:]

        key = derive_key(password, salt)
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        with open(output_path, 'wb') as f:
            f.write(plaintext)
    except Exception as e:
        raise RuntimeError(f"解密失败 {input_path.name}: {e}（密码是否正确？）")

def process_path(password: str, input_path: Path, output_dir: Path, is_encrypt: bool):
    output_dir.mkdir(parents=True, exist_ok=True)
    output_files = []

    def handle_file(file_path: Path):
        if is_encrypt:
            # 保留原始扩展名，如 .pdf, .jpg
            original_suffix = file_path.suffix  # 包括点，例如 ".pdf"
            out_name = f"{uuid.uuid4()}{original_suffix}.enc"
            out_path = output_dir / out_name
            encrypt_file(password, file_path, out_path)
            output_files.append(out_path)
        else:
            if file_path.suffix == '.enc':
                # 移除 .enc，保留中间的原始扩展名
                stem_with_ext = file_path.stem  # 如 "a1b2c3.pdf"
                out_path = output_dir / stem_with_ext
                decrypt_file(password, file_path, out_path)
                output_files.append(out_path)
            else:
                # 跳过非 .enc 文件（不解密）
                return

    if input_path.is_file():
        if is_encrypt:
            handle_file(input_path)
        else:
            if input_path.suffix == '.enc':
                handle_file(input_path)
            else:
                raise ValueError("仅支持解密 .enc 文件")
    elif input_path.is_dir():
        if is_encrypt:
            # 遍历所有文件（递归）
            for item in input_path.rglob('*'):
                if item.is_file():
                    handle_file(item)
        else:
            # 仅处理 .enc 文件（递归）
            for item in input_path.rglob('*.enc'):
                if item.is_file():
                    handle_file(item)
    else:
        raise FileNotFoundError("路径不存在")

    return output_files

# === GUI ===
class App:
    def __init__(self, root):
        self.root = root
        root.title("匿名化加解密工具（保留扩展名）")
        root.geometry("520x320")
        root.resizable(False, False)

        tk.Label(root, text="选择文件或文件夹进行加解密：", font=("Arial", 10)).pack(pady=(10, 0))
        self.path_var = tk.StringVar()
        tk.Entry(root, textvariable=self.path_var, width=65, state='readonly').pack(pady=5)
        tk.Button(root, text="浏览...", command=self.browse, width=10).pack()

        tk.Label(root, text="输入密码（用于加密/解密）：", font=("Arial", 10)).pack(pady=(12, 0))
        self.pw_var = tk.StringVar()
        self.pw_entry = tk.Entry(root, textvariable=self.pw_var, show='*', width=45)
        self.pw_entry.pack(pady=5)

        self.show_pw = tk.BooleanVar()
        tk.Checkbutton(root, text="显示密码", variable=self.show_pw, command=self.toggle_password).pack()

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="🔒 加密", width=14, command=lambda: self.run_action(True), bg="#e0f7fa").pack(side='left', padx=12)
        tk.Button(btn_frame, text="🔓 解密", width=14, command=lambda: self.run_action(False), bg="#f1f8e9").pack(side='right', padx=12)

        self.progress = ttk.Progressbar(root, mode='indeterminate')
        self.progress.pack(fill='x', padx=60, pady=10)

        tk.Label(root, text="说明：加密后文件名为 UUID + 原扩展名 + .enc\n解密后恢复为 UUID + 原扩展名", 
                 fg="gray", font=("Arial", 8)).pack(pady=(5, 0))

    def toggle_password(self):
        self.pw_entry.config(show='' if self.show_pw.get() else '*')

    def browse(self):
        path = filedialog.askdirectory(title="选择文件夹")
        if not path:
            path = filedialog.askopenfilename(title="选择文件")
        if path:
            self.path_var.set(path)

    def run_action(self, is_encrypt):
        input_path_str = self.path_var.get()
        password = self.pw_var.get()

        if not input_path_str:
            messagebox.showerror("错误", "请选择文件或文件夹")
            return
        if not password:
            messagebox.showerror("错误", "请输入密码")
            return

        input_path = Path(input_path_str)
        if not input_path.exists():
            messagebox.showerror("错误", "路径不存在")
            return

        # 输出目录：使用随机后缀避免冲突
        parent = input_path.parent
        action_name = "encrypted" if is_encrypt else "decrypted"
        output_dir_name = f"{action_name}_{uuid.uuid4().hex[:8]}"
        output_path = parent / output_dir_name

        def task():
            try:
                self.progress.start(10)
                self.root.config(cursor="watch")
                output_files = process_path(password, input_path, output_path, is_encrypt)
                self.root.after(0, lambda: messagebox.showinfo(
                    "成功",
                    f"{'加密' if is_encrypt else '解密'}完成！\n输出位置：\n{output_path}\n共处理 {len(output_files)} 个文件"
                ))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", str(e)))
            finally:
                self.root.after(0, lambda: self.progress.stop())
                self.root.config(cursor="")

        threading.Thread(target=task, daemon=True).start()


if __name__ == '__main__':
    root = tk.Tk()
    App(root)
    root.mainloop()