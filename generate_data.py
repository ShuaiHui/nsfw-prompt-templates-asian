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

def extract_phrases_from_md(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            text = f.read()
    except:
        return []
    phrases = set()
    lines = text.splitlines()
    for line in lines:
        if not re.search(r'[a-zA-Z]', line):
            continue
        cells = line.split('|')
        for cell in cells:
            cell = cell.strip()
            if not re.search(r'[\u4e00-\u9fff]', cell) and len(cell) > 2 and re.search(r'[a-zA-Z]', cell):
                clean = re.sub(r'\*\*|__|~~|`|\[|\]|\(|\)', '', cell).strip()
                if re.match(r'^[\w\-\.\+\(\)\:\;\,\'\"\s]{3,}$', clean):
                    phrases.add(clean.lower())
    list_pattern = re.findall(r'^[\-\*]\s+([\w\-\.\+\(\)\:\;\,\'\"\s]{3,})$', text, re.MULTILINE)
    for item in list_pattern:
        clean = item.strip()
        if not re.search(r'[\u4e00-\u9fff]', clean) and len(clean) > 2:
            phrases.add(clean.lower())
    code_blocks = re.findall(r'```[\s\S]*?```', text)
    for block in code_blocks:
        content = re.sub(r'```\w*', '', block).replace('```', '')
        for part in re.split(r'[,\n]', content):
            part = part.strip()
            if part and not re.search(r'[\u4e00-\u9fff]', part) and len(part) > 2:
                phrases.add(part.lower())
    eng_snippets = re.findall(r'\b([a-zA-Z][\w\-\.\+\(\)\:\;\,\'\"\s]{2,50})\b', text)
    for snippet in eng_snippets:
        snippet = snippet.strip()
        if snippet and len(snippet) > 2 and not re.search(r'[\u4e00-\u9fff]', snippet):
            if snippet.lower() not in ('the','and','for','with','from','that','this','have','has','had','not','but','are','was','were','been','can','may','will','would','could','should','make','made','making'):
                phrases.add(snippet.lower())
    final = sorted(list(phrases))
    final = [p for p in final if 2 < len(p) < 80 and re.search(r'[a-zA-Z]{2,}', p)]
    return final

def build_module_from_files(prefix, mod_id, label, icon):
    candidates = [f for f in os.listdir(MD_DIR) if f.startswith(prefix) and f.endswith('.md')]
    if not candidates:
        return None
    filepath = os.path.join(MD_DIR, candidates[0])
    phrases = extract_phrases_from_md(filepath)
    if not phrases:
        return None
    categories = [{"id": f"{mod_id}-01", "label": f"{label}通用", "phrases": phrases}]
    return {"id": mod_id, "label": label, "icon": icon, "categories": categories}

def main():
    data = []
    for prefix, (mod_id, label, icon) in MODULE_MAP.items():
        module = build_module_from_files(prefix, mod_id, label, icon)
        if module:
            data.append(module)
    js_code = "// 自动生成，请勿手动编辑\n"
    js_code += f"// 生成日期: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}\n"
    js_code += "const DEFAULT_DATA = "
    js_code += json.dumps(data, ensure_ascii=False, indent=2)
    js_code += ";\n"
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(js_code)
    print(f"生成完成，短语总数：{sum(len(m['categories'][0]['phrases']) for m in data)}")

if __name__ == "__main__":
    main()