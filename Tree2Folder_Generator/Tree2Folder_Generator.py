import os
from pathlib import Path


def remove_comments(line):
    """
    剔除各种常见的注释格式。
    支持格式: #, //, --, 注：, (注:
    """
    # 定义可能的注释起始符
    comment_markers = [' #', ' //', ' --', ' #', '//', '--', '注：', '(注:']

    content = line
    for marker in comment_markers:
        if marker in content:
            # 只取标记之前的内容
            content = content.split(marker)[0]

    return content.rstrip()


def recreate_structure_ultimate(tree_file_path_input, base_target_dir_input, gen_files, clean_comments):
    print("\n" + "=" * 50)
    print("--- 目录架构反向生成脚本 (究极兼容版) ---")
    print(f"📄 文件模式: {'包含空文件' if gen_files else '仅文件夹'}")
    print(f"✂️ 剔除注释: {'开启' if clean_comments else '关闭'}")
    print("=" * 50)

    # --- 1. 路径准备 ---
    try:
        tree_file_path = Path(tree_file_path_input.replace('"', '').replace("'", "")).resolve()
        base_target_dir = Path(base_target_dir_input.replace('"', '').replace("'", "")).resolve()

        with open(tree_file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"❌ 准备阶段出错: {e}")
        return

    # --- 2. 根目录识别 ---
    root_name = None
    start_index = 0

    for i, line in enumerate(lines):
        # 如果开启了剔除注释，则预处理
        processed_line = remove_comments(line) if clean_comments else line
        clean = processed_line.strip()

        if not clean: continue

        # 兼容“根目录:”标签或直接第一行
        if '根目录:' in clean:
            root_name = clean.split('根目录:', 1)[-1].strip()
            start_index = i + 1
            break
        elif '├──' not in clean and '└──' not in clean and '│' not in clean:
            root_name = clean.rstrip('/')
            start_index = i + 1
            break

    if not root_name:
        print("❌ 无法识别根目录。")
        return

    top_level_dir = base_target_dir / root_name
    top_level_dir.mkdir(parents=True, exist_ok=True)
    print(f"📂 创建根文件夹: {top_level_dir}")

    # --- 3. 核心解析循环 ---
    path_stack = {}
    f_count, d_count = 0, 0

    for line in lines[start_index:]:
        # 处理注释
        working_line = remove_comments(line) if clean_comments else line.rstrip()

        # 跳过空行和装饰线
        if not working_line.strip() or working_line.strip().startswith(('---', '===')):
            continue

        # 寻找树状图标记
        marker_pos = -1
        for m in ['├──', '└──']:
            if m in working_line:
                marker_pos = working_line.find(m)
                marker_type = m
                break

        if marker_pos == -1: continue  # 不是有效的架构行

        # 提取层级
        level = (marker_pos // 4) + 1

        # 提取纯名称
        raw_name = working_line[marker_pos:].replace('├── ', '').replace('└── ', '').strip()
        if not raw_name: continue

        # 判定类型
        is_dir = raw_name.endswith('/')
        clean_name = raw_name.rstrip('/')

        # 构建路径
        parents = Path(".")
        for i in range(1, level):
            if i in path_stack:
                parents = parents / path_stack[i]

        target_path = top_level_dir / parents / clean_name

        if is_dir:
            path_stack[level] = clean_name
            if not target_path.exists():
                target_path.mkdir(parents=True, exist_ok=True)
                d_count += 1
        else:
            if gen_files:
                if not target_path.exists():
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    target_path.touch()
                    f_count += 1

    print("-" * 50)
    print(f"✨ 任务完成！\n新建文件夹: {d_count}\n新建空文件: {f_count}\n位置: {top_level_dir}")
    print("=" * 50)


if __name__ == "__main__":
    t_path = input("请输入 Tree.txt 路径: ").strip()
    b_dir = input("请输入目标存放目录: ").strip()

    if t_path and b_dir:
        # 功能 1: 文件创建开关
        choice_f = input("是否生成空文件占位符？(Y/N): ").strip().upper()
        gen_files = (choice_f == 'Y')

        # 功能 2: 注释剔除开关 (新增)
        choice_c = input("是否尝试【剔除】行尾注释？(Y: 仅保留文件名 / N: 保持原样): ").strip().upper()
        clean_comments = (choice_c == 'Y')

        recreate_structure_ultimate(t_path, b_dir, gen_files, clean_comments)