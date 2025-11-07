import os
import sys

# 配置部分：你可以根据需要修改这些列表
EXCLUDE_DIRS = ['__pycache__', '.git', 'venv', '.idea', 'node_modules', 'uni-modules', 'uview-ui']  # 要忽略的目录名
INCLUDE_EXTENSIONS = None  # 只显示这些扩展名的文件，设为 None 则显示所有文件

def should_exclude_dir(dirname):
    """判断是否应该忽略该目录"""
    return dirname in EXCLUDE_DIRS

def should_include_file(filename):
    """判断是否应该包含该文件"""
    if INCLUDE_EXTENSIONS is None:
        return True  # 如果为 None，则包含所有文件
    return any(filename.endswith(ext) for ext in INCLUDE_EXTENSIONS)

def generate_directory_tree(startpath, depth=-1):
    """
    递归生成目录树结构，返回字符串
    :param startpath: 起始目录路径
    :param depth: 最大递归深度，-1 表示无限制
    """
    def _tree(dirpath, prefix='', current_depth=0):
        """
        内部递归函数，用于构建树状结构
        :param dirpath: 当前目录路径
        :param prefix: 当前行的前缀（用于缩进和连接线）
        :param current_depth: 当前递归深度
        """
        # 如果 depth >= 0 且已达到最大深度，则不再展开子目录
        if depth >= 0 and current_depth >= depth:
            return ''

        entries = []
        try:
            entries = os.listdir(dirpath)
        except PermissionError:
            # 跳过无权限访问的目录
            return ''

        # 排序以保证输出一致性
        entries.sort()

        pointers = ['├── '] * (len(entries) - 1) + ['└── ']
        result = []

        for pointer, entry in zip(pointers, entries):
            full_path = os.path.join(dirpath, entry)
            if os.path.isdir(full_path):
                if should_exclude_dir(entry):
                    continue
                result.append(prefix + pointer + entry + '/')
                if not (depth >= 0 and current_depth + 1 >= depth):  # 只有未达深度限制才递归
                    result.append(_tree(full_path, prefix + ('│   ' if pointer == '├── ' else '    '), current_depth + 1))
            else:
                if should_include_file(entry):
                    result.append(prefix + pointer + entry)
                # 否则跳过该文件

        return '\n'.join(result)

    # 开始构建树
    tree_str = startpath.rstrip('/') + '/\n'
    tree_str += _tree(startpath, current_depth=0)
    return tree_str

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("用法: python script.py <目录路径> [最大深度]")
        sys.exit(1)

    directory = sys.argv[1]
    depth = int(sys.argv[2]) if len(sys.argv) == 3 else -1

    if not os.path.isdir(directory):
        print(f"错误: '{directory}' 不是一个有效的目录")
        sys.exit(1)

    # 生成目录树
    tree = generate_directory_tree(directory, depth=depth)

    # 输出到文件
    output_filename = os.path.basename(os.path.normpath(directory)) + "_structure.txt"
    with open(output_filename, 'w', encoding='utf-8') as f:
        f.write(tree)

    print(f"目录结构已写入到: {output_filename}")

if __name__ == "__main__":
    main()