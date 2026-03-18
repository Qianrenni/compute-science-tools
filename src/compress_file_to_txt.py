import argparse
import os 
import sys
from pathlib import Path
from loguru import logger
def compress_file_to_text(
    input_dir:Path,
    file_extension:list[str]
):
    """
    压缩指定文件夹内符合指定扩展名的文件为文本文件

    :param input_dir: 输入目录
    :param file_extension: 文件扩展名列表
    """
    if not input_dir.exists():
        logger.error(f"路径不存在: {input_dir}")
        return
    logger.info(f'文件拓展名: {file_extension}')
    out_file = input_dir / "compressed.txt"
    for file_ext in file_extension:
        for file_path in input_dir.glob(f"*.{file_ext}"):
            if file_path.is_file():
                logger.info(f"正在处理文件: {file_path}")
                with file_path.open("r", encoding="utf-8") as f:
                    content = f.read()
                    out_file.write_text(content)
    
    logger.info(f"压缩文件已保存到: {out_file}")

def get_args():
    parser = argparse.ArgumentParser(description="压缩指定文件夹内符合指定扩展名的文件为文本文件")
    parser.add_argument("-i", type=Path, help="输入目录")
    parser.add_argument("-e", type=str, help="文件扩展名,用','分隔",default="txt")
    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()
    compress_file_to_text(args.i, args.e.split(","))
