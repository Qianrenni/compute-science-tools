#!/usr/bin/env python3
import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import uuid
from typing import List, Tuple

# === 配置参数 ===
SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32
TAG_SIZE = 16
MAX_WORKERS = min(2, max(1, (os.cpu_count() or 1) // 2))

# === 全局 Logger 配置 ===
logger = logging.getLogger("crypto_tool")
logger.setLevel(logging.DEBUG)  # 内部使用DEBUG，输出级别由handler控制

# 控制台处理器（默认INFO级别）
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# === 密码派生 ===
def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=100_000,
    )
    return kdf.derive(password.encode())

# === 同步加密/解密函数 ===
def _encrypt_file_sync(password: str, input_path: Path, output_path: Path) -> None:
    salt = os.urandom(SALT_SIZE)
    key = derive_key(password, salt)
    aesgcm = AESGCM(key)

    with open(input_path, 'rb') as f:
        data = f.read()

    nonce = os.urandom(NONCE_SIZE)
    ciphertext = aesgcm.encrypt(nonce, data, None)

    with open(output_path, 'wb') as f:
        f.write(salt + nonce + ciphertext)

def _decrypt_file_sync(password: str, input_path: Path, output_path: Path) -> None:
    with open(input_path, 'rb') as f:
        data = f.read()

    if len(data) < SALT_SIZE + NONCE_SIZE + TAG_SIZE:
        raise ValueError(f"文件太小，可能已损坏: {input_path}")

    salt = data[:SALT_SIZE]
    nonce = data[SALT_SIZE:SALT_SIZE + NONCE_SIZE]
    ciphertext = data[SALT_SIZE + NONCE_SIZE:]

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)

    with open(output_path, 'wb') as f:
        f.write(plaintext)

# === 文件收集器 ===
def collect_files(input_path: Path, is_encrypt: bool) -> List[Path]:
    if not input_path.exists():
        raise FileNotFoundError(f"路径不存在: {input_path}")

    if input_path.is_file():
        if is_encrypt:
            return [input_path]
        else:
            if input_path.suffix == '.enc':
                return [input_path]
            else:
                raise ValueError(f"仅支持解密 .enc 文件: {input_path}")
    
    if input_path.is_dir():
        if is_encrypt:
            return [p for p in input_path.rglob('*') 
                    if p.is_file() and not p.name.startswith('.')]
        else:
            return [p for p in input_path.rglob('*.enc') 
                    if p.is_file() and not p.name.startswith('.')]
    
    raise ValueError(f"无效路径类型: {input_path}")

# === 异步处理主函数 ===
async def process_files(
    password: str,
    input_path: Path,
    output_dir: Path,
    is_encrypt: bool,
    max_workers: int = MAX_WORKERS
) -> Tuple[List[Path], List[Tuple[Path, str]]]:
    files = collect_files(input_path, is_encrypt)
    total = len(files)
    
    if total == 0:
        action = "加密" if is_encrypt else "解密"
        logger.warning(f"未找到可{action}的文件")
        return [], []

    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"输入路径: {input_path}")
    logger.info(f"输出路径: {output_dir}")
    logger.info(f"待处理文件数: {total}")
    logger.info(f"并发工作线程数: {max_workers}")
    logger.info(f"操作类型: {'加密' if is_encrypt else '解密'}")
    logger.info("-" * 60)

    successes: List[Path] = []
    failures: List[Tuple[Path, str]] = []

    async def process_single_file(idx: int, file_path: Path):
        logger.info(f"[{idx+1}/{total}] 正在处理: {file_path}")
        try:
            if is_encrypt:
                original_suffix = file_path.suffix
                out_name = f"{uuid.uuid4()}{original_suffix}.enc"
                out_path = output_dir / out_name
                await asyncio.get_running_loop().run_in_executor(
                    executor, _encrypt_file_sync, password, file_path, out_path
                )
                successes.append(out_path)
                logger.debug(f"[✓] 已加密: {file_path.name} -> {out_name}")
            else:
                if file_path.suffix != '.enc':
                    raise ValueError("跳过非.enc文件")
                stem_with_ext = file_path.stem
                out_path = output_dir / stem_with_ext
                await asyncio.get_running_loop().run_in_executor(
                    executor, _decrypt_file_sync, password, file_path, out_path
                )
                successes.append(out_path)
                logger.debug(f"[✓] 已解密: {file_path.name} -> {stem_with_ext}")
            logger.info(f"[{idx+1}/{total}] 处理完成: {file_path}")
        except Exception as e:
            failures.append((file_path, str(e)))
            logger.error(f"[✗] 处理失败 {file_path.name}: {e}")

    # 创建线程池执行器
    executor = ThreadPoolExecutor(max_workers=max_workers)
    try:
        tasks = [process_single_file(i, f) for i, f in enumerate(files)]
        await asyncio.gather(*tasks)
        return successes, failures
    finally:
        executor.shutdown(wait=True)

# === 主函数 ===
async def main():
    parser = argparse.ArgumentParser(
        description="异步文件加解密工具（保留原始扩展名）",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input", type=Path, help="输入文件或文件夹路径")
    parser.add_argument("-o", "--output", type=Path, help="输出目录（默认：输入路径同级目录）")
    parser.add_argument("-e", "--encrypt", action="store_true", help="执行加密操作（默认）")
    parser.add_argument("-d", "--decrypt", action="store_true", help="执行解密操作")
    parser.add_argument("-p", "--password", required=True, help="加密/解密密码")
    parser.add_argument("-w", "--workers", type=int, default=MAX_WORKERS,
                        help=f"并发工作线程数（默认: {MAX_WORKERS}）")
    parser.add_argument("-v", "--verbose", action="store_true", 
                        help="显示详细日志（每个文件的处理结果）")
    
    args = parser.parse_args()
    
    # 设置日志详细级别
    if args.verbose:
        console_handler.setLevel(logging.DEBUG)
        logger.info("启用详细日志模式")
    
    # 操作模式校验
    if args.encrypt and args.decrypt:
        parser.error("不能同时指定 -e 和 -d")
    if not args.encrypt and not args.decrypt:
        args.encrypt = True  # 默认加密
    
    is_encrypt = args.encrypt
    input_path = args.input.resolve()
    
    # 设置输出目录
    if args.output:
        output_dir = args.output.resolve()
    else:
        parent = input_path.parent
        suffix = f"_{uuid.uuid4().hex[:8]}"
        prefix = "encrypted" if is_encrypt else "decrypted"
        output_dir = parent / f"{prefix}{suffix}"
    
    # 安全警告
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        logger.warning("密码通过命令行参数传递可能存在安全风险")
    
    # 执行处理
    try:
        logger.info("开始处理任务...")
        successes, failures = await process_files(
            password=args.password,
            input_path=input_path,
            output_dir=output_dir,
            is_encrypt=is_encrypt,
            max_workers=args.workers
        )
        
        # 结果汇总
        logger.info("=" * 60)
        logger.info(f"任务完成: {'加密' if is_encrypt else '解密'}")
        logger.info(f"成功: {len(successes)} 个文件")
        logger.info(f"失败: {len(failures)} 个文件")
        logger.info(f"输出目录: {output_dir}")
        
        if failures:
            logger.error("失败文件列表:")
            for i, (path, err) in enumerate(failures[:10], 1):
                logger.error(f"  {i}. {path.name}: {err[:100]}")
            if len(failures) > 10:
                logger.error(f"  ... 还有 {len(failures)-10} 个错误未显示")
        
        # 退出码
        sys.exit(0 if not failures else 1)
        
    except Exception as e:
        logger.exception(f"处理过程中发生致命错误: {e}")
        sys.exit(2)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("用户中断操作")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"未处理的异常: {e}")
        sys.exit(3)