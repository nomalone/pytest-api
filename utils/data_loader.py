import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / 'tests' / 'data'

def load_json_cases(filename: str) -> list[dict]:
    file_path = DATA_DIR / filename
    with file_path.open(encoding='utf-8') as f:
        cases = json.load(f)

    if not isinstance(cases, list):
        raise ValueError(f"测试数据文件的顶层必须是列表：{file_path}")

    if not cases:
        raise ValueError(f"测试数据文件至少需要一条用例：{file_path}")

    seen_ids = set()

    # 校验case格式和case_id
    for index, case in enumerate(cases, start=1):
        if not isinstance(case, dict):
            raise ValueError(f"测试数据第{index}项必须是对象：{file_path}")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"测试删数据第{index}项缺少有效id：{file_path}")
        if case_id in seen_ids:
            raise ValueError(f"测试数据存在重复id：{case_id}")
        seen_ids.add(case_id)
    return cases