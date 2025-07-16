import os
import sys

def generate_directory_tree(startpath):
    """
    递归生成目录树结构，返回字符串
    """
    def _tree(dirpath, prefix=''):
        """
        内部递归函数，用于构建树状结构
        """
        # 获取当前目录下的所有文件和子目录
        entries = sorted(os.listdir(dirpath))
        pointers = ['├── '] * (len(entries) - 1) + ['└── ']
        result = []

        for pointer, entry in zip(pointers, entries):
            full_path = os.path.join(dirpath, entry)
            if os.path.isdir(full_path):
                # 如果是目录，递归调用
                result.append(prefix + pointer + entry + '/')
                result.append(_tree(full_path, prefix + '    '))
            else:
                # 如果是文件
                result.append(prefix + pointer + entry)

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