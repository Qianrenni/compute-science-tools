import os
import json
from pathlib import Path
from tkinter import *
from tkinter import filedialog, messagebox, ttk
from markdown_it import MarkdownIt


class MarkdownToCourseConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Markdown 拆分与课程管理工具")
        self.root.geometry("800x600")

        # 输入变量
        self.input_dir = StringVar()
        self.level = IntVar(value=3)
        self.category_name = StringVar()
        self.course_name = StringVar()
        self.selected_title = StringVar()
        self.selected_level = IntVar()

        # 当前结构数据
        self.current_structure = None
        self.file_map = {}
        self.node_id_map = {}  # Tree ID -> Node Data

        # GUI 布局
        self.create_widgets()

    def create_widgets(self):
        top_frame = Frame(self.root)
        top_frame.pack(pady=10, fill=X)

        Label(top_frame, text="选择.md 文件", font=("Arial", 12)).grid(row=0, column=0, sticky=W)
        Entry(top_frame, textvariable=self.input_dir, width=40).grid(row=0, column=1, padx=5)
        Button(top_frame, text="浏览", command=self.select_directory).grid(row=0, column=2)

        Label(top_frame, text="最大解析层级（1~6）", font=("Arial", 12)).grid(row=1, column=0, sticky=W)
        Spinbox(top_frame, from_=1, to=6, textvariable=self.level, width=5).grid(row=1, column=1, sticky=W)

        Label(top_frame, text="分类名", font=("Arial", 12)).grid(row=2, column=0, sticky=W)
        Entry(top_frame, textvariable=self.category_name, width=40).grid(row=2, column=1, padx=5)

        Label(top_frame, text="课程名", font=("Arial", 12)).grid(row=3, column=0, sticky=W)
        Entry(top_frame, textvariable=self.course_name, width=40).grid(row=3, column=1, padx=5)

        Button(top_frame, text="开始转换", command=self.convert_all, bg="green", fg="white").grid(row=4, columnspan=3, pady=10)

        # 分隔线
        Frame(self.root, height=2, bd=1, relief=SUNKEN).pack(fill=X, padx=5, pady=5)

        # 加载 md 文件并展示 course.json 结构
        control_frame = Frame(self.root)
        control_frame.pack(pady=5, fill=X)

        Button(control_frame, text="选择 Markdown 文件", command=self.load_markdown_file).pack(side=LEFT, padx=5)
        Button(control_frame, text="加载结构", command=self.show_course_structure).pack(side=LEFT, padx=5)

        # 树形结构展示
        tree_frame = Frame(self.root)
        tree_frame.pack(padx=10, pady=5, fill=BOTH, expand=True)

        self.tree = ttk.Treeview(tree_frame, show="tree")
        self.tree.pack(side=LEFT, fill=BOTH, expand=True)

        scrollbar = Scrollbar(tree_frame, orient=VERTICAL, command=self.tree.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # 编辑区域
        edit_frame = Frame(self.root)
        edit_frame.pack(pady=5, fill=X)

        Label(edit_frame, text="标题:").pack(side=LEFT)
        Entry(edit_frame, textvariable=self.selected_title, width=30).pack(side=LEFT, padx=5)

        Label(edit_frame, text="层级:").pack(side=LEFT)
        Spinbox(edit_frame, from_=1, to=6, textvariable=self.selected_level, width=5).pack(side=LEFT, padx=5)

        Button(edit_frame, text="更新选中节点", command=self.update_selected_node).pack(side=LEFT, padx=5)
        Button(edit_frame, text="保存结构", command=self.save_course_json).pack(side=LEFT, padx=5)

    def select_directory(self):
        dir_path = filedialog.askopenfilename(filetypes=[("Markdown Files", "*.md")])
        if dir_path:
            self.input_dir.set(dir_path)

    def load_markdown_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Markdown Files", "*.md")])
        if file_path:
            self.md_file_path = file_path
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.current_content = content

    def parse_markdown(self, md_content, max_level):
        """解析 Markdown，提取标题结构，并返回原始内容片段"""
        md = MarkdownIt("commonmark")
        tokens = md.parse(md_content)

        result = []
        stack = []
        file_map = {}  # id -> filename 或 node 结构

        lines = md_content.splitlines(keepends=True)  # 保留换行符
        heading_positions = []

        # 找出所有标题的位置和层级
        for i, token in enumerate(tokens):
            if token.type == "heading_open":
                level = int(token.tag[1])
                title_token = tokens[i + 1]
                if title_token.type == "inline":
                    if level > max_level:
                        continue

                    start_line = token.map[0] if token.map else 0
                    end_line = token.map[1] if token.map else len(lines)
                    title = title_token.content.strip().replace('*', '')
                    clean_title = "".join(c for c in title if c.isalnum() or c in (" ", "-", "_"))[:50].strip()
                    filename = f"{len(file_map) + 1:03d}-{clean_title}.md"

                    node = {
                        "title": title,
                        "level": level,
                        "id": filename,
                        "children": [],
                    }

                    while stack and stack[-1]["level"] >= level:
                        stack.pop()
                    if stack:
                        stack[-1]["children"].append(node)
                    else:
                        result.append(node)
                    stack.append(node)

                    file_map[node["id"]] = {
                        "node": node,
                        "start_line": start_line,
                        "end_line": end_line,
                        "filename": filename,
                        "title": title,
                    }

        all_items = sorted(file_map.values(), key=lambda x: x["start_line"])
        for i, item in enumerate(all_items):
            next_item = all_items[i + 1] if i + 1 < len(all_items) else None
            end_line = next_item["start_line"] if next_item else len(lines)
            content_lines = lines[item["start_line"]:end_line]
            item["content"] = "".join(content_lines).rstrip()

        return result, file_map

    def show_course_structure(self):
        if not hasattr(self, 'md_file_path'):
            messagebox.showerror("错误", "请先选择一个 Markdown 文件")
            return

        max_level = self.level.get()
        structure, file_map = self.parse_markdown(self.current_content, max_level)
        self.current_structure = structure
        self.file_map = file_map
        self.node_id_map.clear()
        self.tree.delete(*self.tree.get_children())

        def insert_nodes(parent_tree_id, nodes):
            for node in nodes:
                title = node["title"]
                tree_id = self.tree.insert(parent_tree_id, END, text=title)
                self.node_id_map[tree_id] = node
                if node.get("children"):
                    insert_nodes(tree_id, node["children"])

        insert_nodes("", structure)

    def update_selected_node(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("提示", "请选择一个节点")
            return

        tree_id = selected[0]
        node = self.node_id_map.get(tree_id)
        if not node:
            return

        new_title = self.selected_title.get().strip()
        new_level = self.selected_level.get()
        if not new_title:
            messagebox.showwarning("提示", "请输入新标题")
            return

        node["title"] = new_title
        node["level"] = new_level
        self.tree.item(tree_id, text=new_title)

    def save_course_json(self):
        if not self.current_structure:
            messagebox.showerror("错误", "没有可保存的结构，请先加载解析内容")
            return

        output_dir = os.path.dirname(self.md_file_path)
        course_path = os.path.join(output_dir, "course.json")

        with open(course_path, "w", encoding="utf-8") as f:
            json.dump(self.current_structure, f, ensure_ascii=False, indent=2)

        messagebox.showinfo("成功", f"已保存 course.json 到 {output_dir}")

    def convert_file(self, input_path, output_root, max_level):
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()

        structure, file_map = self.parse_markdown(content, max_level)
        course_dir = output_root
        os.makedirs(course_dir, exist_ok=True)

        with open(os.path.join(course_dir, "course.json"), "w", encoding="utf-8") as f:
            json.dump(structure, f, ensure_ascii=False, indent=2)

        content_dir = os.path.join(course_dir, "content")
        os.makedirs(content_dir, exist_ok=True)

        def is_leaf(node):
            return not node.get("children")

        def write_files(nodes):
            for node in nodes:
                node_id = node["id"]
                if is_leaf(node) and node["level"] <= max_level:
                    item = file_map[node_id]
                    full_content = item["content"]
                    with open(os.path.join(content_dir, item["filename"]), "w", encoding="utf-8") as f:
                        f.write(full_content)
                if node.get("children"):
                    write_files(node["children"])

        write_files(structure)

    def update_categories_json(self, category_name, course_name):
        saved_dir_base = r'D:\project\vite-blog\public\assets\md'
        categories_path = r'D:\project\vite-blog\public\assets\categories.json'

        with open(categories_path, encoding='utf-8', mode='r+') as f:
            res = json.load(f)

            matched_category = None
            for cat in res:
                if cat['name'] == category_name:
                    matched_category = cat
                    break

            if not matched_category:
                matched_category = {'icon':'🏫',"name": category_name, "courses": []}
                res.append(matched_category)

            matched_course = None
            for course in matched_category['courses']:
                if course['name'] == course_name:
                    matched_course = course
                    saved_dir = os.path.join(saved_dir_base, course['dir'])
                    break

            if not matched_course:
                new_course = {"name": course_name, "dir": course_name}
                matched_category['courses'].append(new_course)
                saved_dir = os.path.join(saved_dir_base, course_name)

            f.seek(0)
            f.truncate()
            json.dump(res, f, ensure_ascii=False, indent=2)

        return saved_dir

    def convert_all(self):
        input_dir = self.input_dir.get()
        max_level = self.level.get()
        category_name = self.category_name.get().strip()
        course_name = self.course_name.get().strip()

        if not category_name or not course_name:
            messagebox.showerror("错误", "请输入分类名和课程名")
            return

        if not os.path.isfile(input_dir):
            messagebox.showerror("错误", "请选择一个有效的md文件")
            return

        try:
            saved_dir = self.update_categories_json(category_name, course_name)
        except Exception as e:
            messagebox.showerror("错误", f"更新 categories.json 失败: {str(e)}")
            return
        self.convert_file(input_dir, saved_dir, max_level)

        messagebox.showinfo("完成", f"已将所有{input_dir} 转换为 {course_name} 文件解析为目录结构（最多 {max_level} 级标题），结果保存在 {saved_dir}")


if __name__ == "__main__":
    root = Tk()
    app = MarkdownToCourseConverter(root)
    root.mainloop()