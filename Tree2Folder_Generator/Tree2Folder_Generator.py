import os
import re
from pathlib import Path


def remove_comments(line):
    """
    剔除各种常见的注释格式。
    支持格式: #, //, --, 注：, (注:
    """
    comment_markers = [' #', ' //', ' --', '注：', '(注:']
    content = line
    for marker in comment_markers:
        if marker in content:
            content = content.split(marker)[0]
    return content.rstrip()


def recreate_structure_ultimate(tree_file_path_input, base_target_dir_input, gen_files, clean_comments):
    print("\n" + "=" * 50)
    print("--- 树状图逆向生成文件夹架构脚本 ---")
    print(f"📄 文件模式: {'包含空文件占位' if gen_files else '仅文件夹'}")
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

    # --- 2. 优化后的根目录识别逻辑 ---
    root_name = None
    start_index = 0

    for i, line in enumerate(lines):
        clean = line.strip()
        if not clean: continue

        # 识别格式：📂 根目录: MyTouchPad 或 📂 MyTouchPad
        if '根目录' in clean or clean.startswith('📂'):
            # 使用正则剔除 Emoji、前缀文字、冒号和空格
            root_name = re.sub(r'[📂根目录:：\s]', '', clean).rstrip('/')
            start_index = i + 1
            break
        # 兜底逻辑：识别第一行不带树状标记的行
        elif not any(m in clean for m in ['├──', '└──', '│']):
            root_name = clean.rstrip('/')
            start_index = i + 1
            break

    if not root_name:
        print("❌ 无法识别根目录，请检查 Tree.txt 格式。")
        return

    top_level_dir = base_target_dir / root_name
    top_level_dir.mkdir(parents=True, exist_ok=True)
    print(f"📂 根文件夹已就绪: {top_level_dir}")

    # --- 3. 核心解析循环 ---
    path_stack = {}  # 存储每一层的当前目录名
    f_count, d_count = 0, 0

    for line in lines[start_index:]:
        # 处理特殊空格 (ASCII 160) 并剔除注释
        working_line = line.replace(' ', ' ')
        if clean_comments:
            working_line = remove_comments(working_line)
        else:
            working_line = working_line.rstrip()

        if not working_line.strip() or working_line.strip().startswith(('---', '===')):
            continue

        # 寻找树状图标记位置
        marker_pos = -1
        marker_type = ""
        for m in ['├──', '└──']:
            if m in working_line:
                marker_pos = working_line.find(m)
                marker_type = m
                break

        if marker_pos == -1: continue

        # --- 4. 优化后的层级计算 ---
        # 步长通常为 4 (例如 "│   ├──")
        level = (marker_pos // 4) + 1

        # 提取纯名称 (去掉 ├── 或 └── 及其前缀)
        raw_name = working_line[marker_pos + len(marker_type):].strip()
        if not raw_name: continue

        # 判定是否为目录
        is_dir = raw_name.endswith('/')
        clean_name = raw_name.rstrip('/')

        # 构建父级路径
        current_parent = Path(".")
        for i in range(1, level):
            if i in path_stack:
                current_parent = current_parent / path_stack[i]

        target_path = top_level_dir / current_parent / clean_name

        if is_dir:
            path_stack[level] = clean_name
            if not target_path.exists():
                target_path.mkdir(parents=True, exist_ok=True)
                d_count += 1
        else:
            # 文件行不更新 path_stack
            if gen_files:
                if not target_path.exists():
                    target_path.parent.mkdir(parents=True, exist_ok=True)
                    target_path.touch()
                    f_count += 1

    print("-" * 50)
    print(f"✨ 任务完成！")
    print(f"📁 新建文件夹: {d_count}")
    print(f"📄 新建空文件: {f_count}")
    print(f"📍 根目录位置: {top_level_dir}")
    print("=" * 50)


if __name__ == "__main__":
    t_path = input("请输入树状图完整路径（如D:/Test/Tree.txt）: ").strip()
    b_dir = input("请输入目标存放目录 (如D:/Test/Result): ").strip()

    if t_path and b_dir:
        choice_f = input("是否生成空文件占位符？(Y/N): ").strip().upper()
        gen_files = (choice_f == 'Y')

        choice_c = input("是否尝试【剔除】行尾注释？(Y/N): ").strip().upper()
        clean_comments = (choice_c == 'Y')

        recreate_structure_ultimate(t_path, b_dir, gen_files, clean_comments)