import os
import re
import json

MD_DIR = "."
OUTPUT_FILE = "nprom_data.js"

MODULE_MAP = {
    "01-场景主题": ("01", "01-场景主题", "🏠"),
    "02-景别构图": ("02", "02-景别构图", "🎞"),
    "03-裸露液体": ("03", "03-裸露液体", "💧"),
    "04-服装专项": ("04", "04-服装专项", "👗"),
    "05-光影氛围": ("05", "05-光影氛围", "☀️"),
    "06-姿势动作": ("06", "06-姿势动作", "🧍"),
    "07-表情眼神": ("07", "07-表情眼神", "😊"),
    "08-风格胶片": ("08", "08-风格胶片", "🎨"),
    "09-妆容专项": ("09", "09-妆容专项", "💄"),
    "10-发型饰品": ("10", "10-发型饰品", "💇"),
    "11-瑕疵细节": ("11", "11-瑕疵细节", "🔍"),
    "12-纹身标记": ("12", "12-纹身标记", "🖋️"),
    "13-道具宠物": ("13", "13-道具宠物", "🧸"),
    "14-人格卡片": ("14", "14-人格卡片", "🪪"),
}

def extract_phrases_from_segment(text):
    """
    从一段文本中提取英文短语，并附带可能的中文注解。
    返回 [{ "t": 短语, "n": 注解或空字符串 }]
    """
    results = []
    # 1. 尝试解析表格：假设有两列或三列，第一列为英文，第二列为中文
    table_rows = re.findall(r'^\|(.+)\|$', text, re.MULTILINE)
    for row in table_rows:
        cells = [c.strip() for c in row.split('|')]
        # 过滤掉表头分隔行（如 |---|---|）
        if all(re.fullmatch(r'[-:\s]+', c) for c in cells if c):
            continue
        eng = None
        zh = ""
        for cell in cells:
            if re.search(r'[a-zA-Z]', cell) and not re.search(r'[\u4e00-\u9fff]', cell):
                eng = cell.strip()
            elif re.search(r'[\u4e00-\u9fff]', cell):
                zh = cell.strip()
        if eng and len(eng) > 2:
            results.append({"t": eng, "n": zh})

    # 2. 解析列表项：- english phrase 中文解释
    list_items = re.findall(r'^[\-\*]\s+(.+)$', text, re.MULTILINE)
    for item in list_items:
        # 尝试按中文分隔符分割
        parts = re.split(r'(?<=[a-zA-Z])\s+(?=[\u4e00-\u9fff])', item, maxsplit=1)
        eng = parts[0].strip()
        zh = parts[1].strip() if len(parts) > 1 else ""
        if re.search(r'[a-zA-Z]', eng) and len(eng) > 2:
            results.append({"t": eng, "n": zh})

    # 3. 普通文本中的英文单词（去重，没有注解）
    if not results:  # 仅当上面没提取到时回退
        words = re.findall(r'\b[a-zA-Z][\w\-\.\+\(\)\:\;\,\'\"\s]{2,60}\b', text)
        for w in words:
            w = w.strip()
            if w.lower() not in ('the','and','for','with','from','that','this','have','has','had','not','but','are','was','were','been','can','may','will','would','could','should','make','made','making'):
                results.append({"t": w, "n": ""})

    # 去重，保留首次出现的注解
    seen = {}
    final = []
    for item in results:
        t = item["t"].lower()
        if t not in seen:
            seen[t] = True
            final.append(item)
    return final

def build_module(filepath, mod_id, label, icon):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    # 按二级标题分割
    sections = re.split(r'^##\s+(.+)', text, flags=re.MULTILINE)
    # 第一段是标题前的引言（忽略），后面成对出现标题+内容
    categories = []
    cat_id = 1
    for i in range(1, len(sections), 2):
        title = sections[i].strip()
        content = sections[i+1] if (i+1) < len(sections) else ""
        phrases = extract_phrases_from_segment(content)
        if phrases:
            categories.append({
                "id": f"{mod_id}-{cat_id:02d}",
                "label": title,  # 保留中文标题作为分类名
                "phrases": phrases
            })
            cat_id += 1

    # 如果没有二级标题，则整个文件作为一个分类
    if not categories:
        phrases = extract_phrases_from_segment(text)
        if phrases:
            categories = [{
                "id": f"{mod_id}-01",
                "label": "通用",
                "phrases": phrases
            }]

    return {
        "id": mod_id,
        "label": label,
        "icon": icon,
        "categories": categories
    } if categories else None

def main():
    data = []
    for prefix, (mod_id, label, icon) in MODULE_MAP.items():
        candidates = [f for f in os.listdir(MD_DIR) if f.startswith(prefix) and f.endswith('.md')]
        if candidates:
            filepath = os.path.join(MD_DIR, candidates[0])
            module = build_module(filepath, mod_id, label, icon)
            if module:
                data.append(module)
                total = sum(len(c['phrases']) for c in module['categories'])
                print(f"✓ {label}: {len(module['categories'])} 分类, {total} 短语")

    # 生成 JS
    js_code = "// 自动生成，请勿手动编辑\n"
    js_code += f"// 生成日期: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}\n"
    js_code += "const DEFAULT_DATA = "
    js_code += json.dumps(data, ensure_ascii=False, indent=2)
    js_code += ";\n"

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(js_code)

    print(f"\n数据已生成: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()