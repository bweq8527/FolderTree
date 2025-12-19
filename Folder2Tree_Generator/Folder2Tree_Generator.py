import os
import shutil
from pathlib import Path

# --- 配置：需要忽略的文件夹列表 ---
IGNORE_DIRS = ['.git', '__pycache__', '.DS_Store', '.vscode', '.idea']


def log_and_collect(line, tree_lines, tree_only_lines=None, is_tree_structure=False):
    """
    同时打印到终端并添加到内容收集列表。
    tree_lines: 用于控制台显示的完整内容（含日志）。
    tree_only_lines: 专门用于写入 Tree.txt 的纯净结构。
    """
    print(line)
    tree_lines.append(line)
    # 如果是纯树状图行，且提供了独立列表，则添加
    if is_tree_structure and tree_only_lines is not None:
        tree_only_lines.append(line)


def generate_tree_content(start_path, tree_lines, tree_only_lines, max_depth=None):
    """
    生成纯净树状图内容。文件夹后带 '/'。
    """
    # 控制台显示的页眉（不加入 tree_only_lines）
    print("\n" + "=" * 40)
    print("项目文件夹架构树状图生成中...")
    print("-" * 40)

    # 树状图起始行
    root_line = f"📂 根目录: {start_path.name}"
    log_and_collect(root_line, tree_lines, tree_only_lines, is_tree_structure=True)

    def _create_tree_content(directory, prefix="", current_depth=0):
        if max_depth is not None and current_depth > max_depth:
            return

        try:
            items = sorted(list(directory.iterdir()), key=lambda x: (x.is_file(), x.name))
        except PermissionError:
            log_and_collect(f"{prefix}└── 🚫 [权限不足]", tree_lines, tree_only_lines, True)
            return

        # 过滤隐藏文件
        items = [item for item in items if not item.name.startswith('.')]

        total_items = len(items)

        for index, item in enumerate(items):
            is_last = (index == total_items - 1)
            connector = "└── " if is_last else "├── "

            name = item.name
            if item.is_dir():
                name += "/"

            line = f"{prefix}{connector}{name}"

            # 标记为结构行，存入 tree_only_lines
            log_and_collect(line, tree_lines, tree_only_lines, is_tree_structure=True)

            if item.is_dir():
                extension = "    " if is_last else "│   "
                _create_tree_content(item, prefix + extension, current_depth + 1)

    _create_tree_content(start_path)


def flatten_copy_files(source_dir, destination_dir, tree_lines):
    """
    执行平铺复制。日志只显示在屏幕和 tree_lines 中，不进入 Tree.txt。
    """
    copied_count = 0
    print("\n" + "=" * 40)
    print("开始执行扁平式文件复制 (已启用过滤)...")
    print(f"目标目录: {destination_dir.resolve()}")
    print("-" * 40)

    destination_dir.mkdir(parents=True, exist_ok=True)

    for dirpath, dirnames, filenames in os.walk(source_dir):
        dirnames[:] = [d for d in dirnames if d.lower() not in IGNORE_DIRS]
        for filename in filenames:
            source_file = Path(dirpath) / filename
            destination_file = destination_dir / filename

            if filename.startswith('~$') or filename.endswith('.tmp'):
                continue

            try:
                shutil.copy2(source_file, destination_file)
                # 日志只传 tree_lines，不传 tree_only_lines
                log_and_collect(f"✅ 复制: {source_file.relative_to(source_dir)}", tree_lines)
                copied_count += 1
            except Exception as e:
                log_and_collect(f"❌ 复制失败 ({filename}): {e}", tree_lines)

    print("-" * 40)
    print(f"🎉 复制完成。共计: {copied_count} 个文件。")


def write_output(filepath, content_list):
    """高效写入文件"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_list))
        print(f"\n📄 树状图已保存至: {filepath.resolve()}")
        return True
    except Exception as e:
        print(f"\n❌ 写入失败: {e}")
        return False


def main_process():
    print("\n--- [文件夹] 树状图生成 & 扁平拷贝工具 ---")

    source_path_input = input("请[输入]要扫描的文件夹路径: ").strip().replace('"', '').replace("'", "")
    source_dir = Path(source_path_input)

    if not source_dir.exists() or not source_dir.is_dir():
        print(f"\n⚠️ 路径错误。")
        return

    while True:
        mode_choice = input("是否需要[扁平拷贝]？(Y/N): ").strip().upper()
        if mode_choice in ('Y', 'N'): break

    tree_lines = []  # 用于控制台完整显示
    tree_only_lines = []  # 专门存放纯净树状图

    if mode_choice == 'N':
        output_path_input = input("请输入树状图导出路径: ").strip().replace('"', '').replace("'", "")
        generate_tree_content(source_dir, tree_lines, tree_only_lines)
        write_output(Path(output_path_input), tree_only_lines)

    elif mode_choice == 'Y':
        target_base_input = input("请输入拷贝目标路径: ").strip().replace('"', '').replace("'", "")
        target_base_dir = Path(target_base_input)

        top_copy_dir = target_base_dir / f"COPY__{source_dir.name}"
        flat_file_dir = top_copy_dir / f"FILE__{source_dir.name}"
        tree_output_filepath = top_copy_dir / "Tree.txt"

        top_copy_dir.mkdir(parents=True, exist_ok=True)

        # 1. 生成树状图内容 (只把结构存入 tree_only_lines)
        generate_tree_content(source_dir, tree_lines, tree_only_lines)

        # 2. 执行复制 (不影响 tree_only_lines)
        flatten_copy_files(source_dir, flat_file_dir, tree_lines)

        # 3. 写入文件 (只写入 tree_only_lines)
        write_output(tree_output_filepath, tree_only_lines)


if __name__ == "__main__":
    try:
        main_process()
    except Exception as e:
        print(f"\n运行时错误: {e}")
    input("\n按回车键退出...")