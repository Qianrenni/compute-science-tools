import os
import sys

# 配置部分：你可以根据需要修改这些列表
EXCLUDE_DIRS = ['__pycache__', '.git', 'venv', '.idea', 'node_modules']  # 要忽略的目录名
INCLUDE_EXTENSIONS =None # 只显示这些扩展名的文件，设为 None 则显示所有文件

def should_exclude_dir(dirname):
    """判断是否应该忽略该目录"""
    return dirname in EXCLUDE_DIRS

def should_include_file(filename):
    """判断是否应该包含该文件"""
    if INCLUDE_EXTENSIONS is None:
        return True  # 如果为 None，则包含所有文件
    return any(filename.endswith(ext) for ext in INCLUDE_EXTENSIONS)

def generate_directory_tree(startpath):
    """
    递归生成目录树结构，返回字符串
    """
    def _tree(dirpath, prefix=''):
        """
        内部递归函数，用于构建树状结构
        """
        entries = sorted(os.listdir(dirpath))
        pointers = ['├── '] * (len(entries) - 1) + ['└── ']
        result = []

        for pointer, entry in zip(pointers, entries):
            full_path = os.path.join(dirpath, entry)
            if os.path.isdir(full_path):
                if should_exclude_dir(entry):  # 如果是要忽略的目录，则跳过
                    continue
                result.append(prefix + pointer + entry + '/')
                result.append(_tree(full_path, prefix + '|   '))
            else:
                if should_include_file(entry):  # 如果文件符合条件，则加入
                    result.append(prefix + pointer + entry)
                # 否则跳过该文件

        return '\n'.join(result)

    # 开始构建树
    tree_str = startpath + '/\n'
    tree_str += _tree(startpath)
    return tree_str

def main():
    if len(sys.argv) != 2:
        print("用法: python script.py <目录路径>")
        sys.exit(1)

    directory = sys.argv[1]
    if not os.path.isdir(directory):
        print(f"错误: '{directory}' 不是一个有效的目录")
        sys.exit(1)

    # 生成目录树
    tree = generate_directory_tree(directory)

    # 输出到文件
    output_filename = os.path.basename(os.path.normpath(directory)) + "_structure.txt"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(tree)

    print(f"目录结构已写入到: {output_filename}")

if __name__ == "__main__":
    main()