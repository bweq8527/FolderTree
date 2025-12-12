import os
from pathlib import Path

# 定义会被识别为文件的扩展名列表 (全部使用小写，不要带点)
FILE_EXTENSIONS = {
    # 常用文档和媒体
    'txt', 'json', 'm4s', 'mpd', 'pb', 'log', 'py', 'dat', 'ini', 'cfg',
    'jpg', 'png', 'gif', 'mp4', 'avi', 'mov', 'dll', 'exe', 'bin', 'pdb', 'xml',
    'pdf', 'docx', 'xlsx', 'pptx', 'zip', 'rar', '7z', 'tmp', 'bak', 'md',

    # === 工程/CAD文件格式 (已修正为小写) ===
    'step', 'stp',  # STEP 文件
    'sldprt', 'prt',  # SolidWorks 零件
    'sldasm', 'asm',  # SolidWorks 装配体
    'slddrw', 'drw',  # SolidWorks 工程图
    'dwg', 'dxf',  # CAD 图纸
    'igs', 'iges',  # IGES 中间格式
    'x_t', 'x_b',  # Parasolid 格式
    '3mf'       # 3D打印文件格式
}

def restore_folders_only(tree_file_path_input, base_target_dir_input):
    """
    仅重建文件夹结构，忽略所有文件。
    """
    print("\n" + "=" * 40)
    print("--- 纯文件夹架构还原脚本 ---")
    print("=" * 40)

    # --- 1. 路径处理 ---
    try:
        tree_file_path = Path(tree_file_path_input.replace('\"', '').replace('\'', '')).resolve()
        base_target_dir = Path(base_target_dir_input.replace('\"', '').replace('\'', '')).resolve()
    except Exception as e:
        print(f"❌ 路径格式错误: {e}")
        return

    if not tree_file_path.exists():
        print(f"❌ 找不到文件: {tree_file_path}")
        return

    try:
        base_target_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"❌ 无法创建基准目录: {e}")
        return

    # --- 2. 读取并解析 ---
    try:
        with open(tree_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ 读取 Tree.txt 失败: {e}")
        return

    root_name = None
    structure_lines = []
    parsing_started = False

    # 提取根目录和树状图部分
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        # 智能匹配根目录名称
        if '根目录:' in line_clean:
            parts = line_clean.split('根目录:', 1)
            if len(parts) > 1:
                root_name = parts[-1].strip()
                print(f"✅ 识别到根目录: {root_name}")
            continue

        if '├──' in line_clean or '└──' in line_clean:
            parsing_started = True
            structure_lines.append(line)  # 保留原始缩进
        elif parsing_started:
            # 遇到分隔线停止
            if line_clean.startswith('---') or line_clean.startswith('==='):
                break

    if not root_name:
        print("❌ 错误：无法从文件中找到“根目录:”信息，请检查 Tree.txt 格式。")
        return

    # 创建顶层根目录
    top_level_dir = base_target_dir / root_name
    top_level_dir.mkdir(parents=True, exist_ok=True)
    print(f"📂 创建根文件夹: {top_level_dir}")

    # --- 3. 循环创建子文件夹 ---
    path_stack = {}  # 记录每一层级的文件夹名称
    folder_count = 0

    for line in structure_lines:
        line_strip = line.rstrip('\r\n')

        # 1. 提取名称
        name = line_strip.split('├──')[-1].split('└──')[-1].strip()
        if not name:
            continue

        # 2. 计算层级 (每4个字符为一级)
        # ├── (pos 0) -> Level 1
        # │   ├── (pos 4) -> Level 2
        marker_pos = -1
        if '├──' in line_strip:
            marker_pos = line_strip.rfind('├──')
        elif '└──' in line_strip:
            marker_pos = line_strip.rfind('└──')

        level = (marker_pos // 4) + 1

        # 3. 判断是否为文件 (核心逻辑)
        # 如果包含点号且后缀在忽略列表中，则视为文件 -> 跳过
        is_file = False
        if '.' in name:
            ext = name.split('.')[-1].lower()
            if ext in FILE_EXTENSIONS:
                is_file = True

        # 4. 执行操作
        if is_file:
            # 是文件：跳过，不创建，也不记录到路径栈中(通常文件是叶子节点)
            # print(f"   [跳过文件] {name}")
            pass
        else:
            # 是文件夹：记录并创建
            path_stack[level] = name

            # 构建从根目录开始的路径
            # 注意：我们要把 level 之前的所有父目录都拼起来
            parents = [path_stack[i] for i in range(1, level)]
            current_relative_path = Path(*parents) / name
            full_path = top_level_dir / current_relative_path

            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                folder_count += 1
                # print(f"📂 创建目录: {current_relative_path}")

    print("\n" + "=" * 40)
    print(f"✨ 完成！共新建了 {folder_count} 个文件夹。")
    print(f"位置: {top_level_dir.resolve()}")
    print("=" * 40)


if __name__ == "__main__":
    t_path = input("请输入 Tree.txt 路径: ").strip()
    if t_path:
        b_dir = input("请输入目标基准目录: ").strip()
        if b_dir:
            restore_folders_only(t_path, b_dir)