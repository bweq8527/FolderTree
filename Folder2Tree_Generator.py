import os
import shutil
from pathlib import Path

# --- 配置：需要忽略的文件夹列表 (版本控制、缓存等) ---
IGNORE_DIRS = ['.git', '__pycache__', '.DS_Store', '.vscode', '.idea']


# --- 辅助函数：将内容同时打印到屏幕和收集到列表中 ---
def log_and_collect(line, tree_lines):
    """同时打印到终端并添加到内容收集列表"""
    print(line)
    tree_lines.append(line)


# --- 核心函数：遍历并生成树状图 (增强标记) ---
def generate_tree_content(start_path, tree_lines, max_depth=None):
    """
    遍历文件夹并生成树状图内容。
    【重要改进】：文件夹名称后添加 '/' 标记。
    """
    # 头部信息
    header_root = f"📂 根目录: {start_path.name}"
    header_path = f"📍 完整路径: {start_path.resolve()}\n"

    log_and_collect("\n" + "=" * 40, tree_lines)
    log_and_collect("项目文件夹架构树状图生成中...", tree_lines)
    log_and_collect("【注意】文件夹名称后带有 '/' 标记！", tree_lines)
    log_and_collect("-" * 40, tree_lines)
    log_and_collect(header_root, tree_lines)
    log_and_collect(header_path.strip(), tree_lines)

    # 递归生成内容
    def _create_tree_content(directory, prefix="", current_depth=0):
        if max_depth is not None and current_depth > max_depth:
            return

        try:
            items = sorted(list(directory.iterdir()), key=lambda x: (x.is_file(), x.name))
        except PermissionError:
            log_and_collect(f"{prefix}└── 🚫 [权限不足]", tree_lines)
            return

        items = [item for item in items if not item.name.startswith('.')]

        total_items = len(items)

        for index, item in enumerate(items):
            is_last = (index == total_items - 1)
            connector = "└── " if is_last else "├── "

            # 【核心改进】：根据类型添加标记
            name = item.name
            if item.is_dir():
                name += "/"  # 文件夹标记

            line = f"{prefix}{connector}{name}"

            log_and_collect(line, tree_lines)

            if item.is_dir():
                extension = "    " if is_last else "│   "
                _create_tree_content(item, prefix + extension, current_depth + 1)

    # 开始遍历
    _create_tree_content(start_path)


# --- 文件操作函数：平铺式文件复制（含忽略逻辑） ---
def flatten_copy_files(source_dir, destination_dir, tree_lines):
    """
    遍历源文件夹及其所有子文件夹，将所有文件平铺复制到指定的目标子文件夹。
    并自动忽略 IGNORE_DIRS 列表中的目录。
    """
    copied_count = 0

    log_and_collect("\n" + "=" * 40, tree_lines)
    log_and_collect("开始执行平铺式文件复制 (已启用 Git/缓存目录排除)...", tree_lines)
    log_and_collect(f"文件目标目录: {destination_dir.resolve()}", tree_lines)
    log_and_collect("-" * 40, tree_lines)

    # 确保目标文件夹存在
    destination_dir.mkdir(parents=True, exist_ok=True)

    for dirpath, dirnames, filenames in os.walk(source_dir):
        current_dir = Path(dirpath)

        # 【核心改进】排除目录：修改 dirnames 列表，os.walk 就会跳过这些目录
        dirnames[:] = [d for d in dirnames if d.lower() not in IGNORE_DIRS]

        # 复制所有文件
        for filename in filenames:
            source_file = current_dir / filename
            destination_file = destination_dir / filename

            # 跳过临时文件（如 Word 的 ~$ 文件）
            if filename.startswith('~$') or filename.endswith('.tmp'):
                log_and_collect(f"⚠️ 跳过临时文件: {filename}", tree_lines)
                continue

            try:
                shutil.copy2(source_file, destination_file)
                log_and_collect(f"✅ 复制: {source_file.relative_to(source_dir)}", tree_lines)
                copied_count += 1
            except Exception as e:
                log_and_collect(f"❌ 复制失败 ({filename}): {e}", tree_lines)

    log_and_collect("-" * 40, tree_lines)
    log_and_collect(f"🎉 复制完成。共计复制了 {copied_count} 个文件。", tree_lines)
    return copied_count


# --- 文件操作函数：写入文件 (性能优化) ---
def write_output(filepath, content_list):
    """一次性将所有内容写入文件，高效且安全"""
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content_list))

        print("-" * 40)
        print(f"📄 报告文件已成功保存到：")
        print(f"👉 {filepath.resolve()}")
        print("=" * 40)
        return True
    except Exception as e:
        print(f"\n❌ 写入文件时发生致命错误：{e}")
        return False


# --- 主程序逻辑 ---
def main_process():
    print("\n--- 文件夹架构工具 (查询/复制模式) ---")

    # 1. 询问源文件夹路径
    source_path_input = input("请【输入】要扫描的文件夹路径: ").strip().replace('"', '').replace("'", "")
    source_dir = Path(source_path_input)

    if not source_dir.exists() or not source_dir.is_dir():
        print(f"\n⚠️ 错误：路径 '{source_dir}' 不存在或不是一个文件夹。")
        input("\n按回车键退出...")
        return

    # 2. 询问模式选择
    while True:
        mode_choice = input("是否需要【生成副本】？(输入 'Y' 复制模式 / 'N' 查询模式): ").strip().upper()
        if mode_choice in ('Y', 'N'):
            break
        print("输入无效，请重新输入 'Y' 或 'N'。")

    tree_lines = []

    if mode_choice == 'N':
        # --- 查询模式 ---
        print("\n当前为【查询模式】(仅生成报告)")
        output_path_input = input("请输入要导出的文件完整路径 (例如: report.txt): ").strip().replace('"', '').replace(
            "'", "")
        output_filepath = Path(output_path_input)

        if not output_path_input:
            print("\n⚠️ 路径输入不能为空。")
            return

        generate_tree_content(source_dir, tree_lines)
        write_output(output_filepath, tree_lines)

    elif mode_choice == 'Y':
        # --- 复制模式 ---
        print("\n当前为【复制模式】(生成报告并平铺复制文件)")

        # 询问拷贝目标路径
        target_base_input = input("请输入所要拷贝的目标根文件夹路径: ").strip().replace('"', '').replace("'", "")
        target_base_dir = Path(target_base_input)

        if not target_base_input:
            print("\n⚠️ 路径输入不能为空。")
            return

        # 构造顶层 COPY__### 文件夹路径
        copy_folder_name = f"COPY__{source_dir.name}"
        top_copy_dir = target_base_dir / copy_folder_name

        # 构造内层 FILE__### 文件夹路径 (存放平铺文件)
        file_folder_name = f"FILE__{source_dir.name}"
        flat_file_dir = top_copy_dir / file_folder_name

        # 构造 Tree.txt 的完整路径
        tree_output_filepath = top_copy_dir / "Tree.txt"

        # 确保顶层文件夹存在
        print(f"\n创建顶层目标文件夹: {top_copy_dir.resolve()}")
        top_copy_dir.mkdir(parents=True, exist_ok=True)

        # A. 生成树状图内容 (带 '/' 标记)
        generate_tree_content(source_dir, tree_lines)

        # B. 执行平铺式文件复制到内层文件夹
        flatten_copy_files(source_dir, flat_file_dir, tree_lines)

        # C. 写入 Tree.txt (包含了带标记的树状图和复制日志)
        if write_output(tree_output_filepath, tree_lines):
            print(f"\n🎉 复制模式任务完成。所有文件已平铺复制到:")
            print(f"👉 {flat_file_dir.resolve()}")
            print(f"报告文件 Tree.txt (包含 '/' 标记) 位于: {tree_output_filepath.resolve()}")


# --- 运行主程序 ---
if __name__ == "__main__":
    try:
        main_process()
    except Exception as e:
        print(f"\n程序运行中发生未捕获的错误: {e}")

    input("\n按回车键退出...")