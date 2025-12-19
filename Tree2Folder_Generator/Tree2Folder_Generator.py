import os
from pathlib import Path


def recreate_structure_from_marked_tree(tree_file_path_input, base_target_dir_input, generate_files_flag):
    """
    基于带有 '/' 标记的 Tree.txt 还原架构。
    根据 generate_files_flag 决定是否生成空文件。
    """
    print("\n" + "=" * 50)
    print("--- 目录架构反向生成脚本 (最终版) ---")
    print(f"📄 模式: {'包含空文件' if generate_files_flag else '仅生成文件夹'}")
    print("=" * 50)

    # --- 1. 路径清理与准备 ---
    try:
        tree_file_path = Path(tree_file_path_input.replace('"', '').replace("'", "")).resolve()
        base_target_dir = Path(base_target_dir_input.replace('"', '').replace("'", "")).resolve()
    except Exception as e:
        print(f"❌ 路径格式错误: {e}")
        return

    if not tree_file_path.exists():
        print(f"❌ 找不到 Tree 文件: {tree_file_path}")
        return

    try:
        base_target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"❌ 无法创建基准目录: {e}")
        return

    # --- 2. 读取文件 ---
    try:
        with open(tree_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return

    # --- 3. 解析与生成 ---
    root_name = None
    structure_lines = []
    parsing_started = False

    # A. 提取根目录和树状图行
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        # 提取根目录名
        if '根目录:' in line_clean and not root_name:
            parts = line_clean.split('根目录:', 1)
            if len(parts) > 1:
                root_name = parts[-1].strip()
                print(f"✅ 识别到根目录: {root_name}")
            continue

        # 遇到分隔线或日志区停止
        if parsing_started and (
                line_clean.startswith('---') or line_clean.startswith('=' * 10) or "开始执行平铺式" in line_clean):
            break

        # 收集树状图行
        if '├──' in line or '└──' in line:
            parsing_started = True
            structure_lines.append(line)

    if not root_name:
        print("❌ 错误: 无法解析根目录名称，请检查 Tree.txt 格式。")
        return

    # 创建顶层根目录
    top_level_dir = base_target_dir / root_name
    top_level_dir.mkdir(parents=True, exist_ok=True)
    print(f"📂 创建根文件夹: {top_level_dir}")

    # B. 遍历并创建
    path_stack = {}  # Key: Level, Value: Folder Name
    folder_count = 0
    file_count = 0

    for line in structure_lines:
        line_original = line.rstrip('\r\n')

        # 1. 计算层级
        marker_pos = -1
        if '├──' in line_original:
            marker_pos = line_original.find('├──')
        elif '└──' in line_original:
            marker_pos = line_original.find('└──')

        if marker_pos == -1: continue

        level = (marker_pos // 4) + 1

        # 2. 提取名称并判断类型
        raw_name = line_original[marker_pos:].replace('├── ', '').replace('└── ', '').strip()

        if not raw_name: continue

        # 【核心逻辑】：根据 '/' 判断
        is_directory = raw_name.endswith('/')

        # 去掉最后的 '/' 用于路径构建
        clean_name = raw_name[:-1] if is_directory else raw_name

        # 3. 构建路径 (从 stack 中获取父级)
        parents_path = Path(".")
        for i in range(1, level):
            if i in path_stack:
                parents_path = parents_path / path_stack[i]

        full_target_path = top_level_dir / parents_path / clean_name

        # 4. 执行创建操作
        if is_directory:
            # --- 处理文件夹 ---
            path_stack[level] = clean_name  # 入栈
            if not full_target_path.exists():
                full_target_path.mkdir(parents=True, exist_ok=True)
                folder_count += 1
        else:
            # --- 处理文件 ---
            # 只有当用户选择了 "Y" (generate_files_flag 为 True) 时才执行
            if generate_files_flag:
                if not full_target_path.exists():
                    full_target_path.parent.mkdir(parents=True, exist_ok=True)  # 确保父目录存在
                    full_target_path.touch()  # 创建空文件
                    file_count += 1

    print("-" * 50)
    print(f"🎉 重建完成!")
    print(f"📂 新建文件夹: {folder_count}")
    if generate_files_flag:
        print(f"📄 新建空文件: {file_count}")
    else:
        print(f"📄 新建空文件: 0 (用户选择跳过)")
    print(f"📍 存放位置: {top_level_dir.resolve()}")
    print("=" * 50)


if __name__ == "__main__":
    # 1. 获取 Tree 文件路径
    t_path = input("请输入带 '/' 标记的 Tree.txt 路径: ").strip()

    if t_path:
        # 2. 获取目标路径
        b_dir = input("请输入目标基准目录: ").strip()

        if b_dir:
            # 3. 获取模式选项 (新增功能)
            while True:
                choice = input("是否生成空文件占位符？(Y: 生成 / N: 仅生成文件夹): ").strip().upper()
                if choice in ['Y', 'N']:
                    generate_files = (choice == 'Y')
                    break
                print("输入无效，请输入 Y 或 N。")

            # 4. 执行
            recreate_structure_from_marked_tree(t_path, b_dir, generate_files)
        else:
            print("❌ 目标目录不能为空")
    else:
        print("❌ Tree 文件路径不能为空")