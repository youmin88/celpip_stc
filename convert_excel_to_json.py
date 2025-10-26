# -*- coding: utf-8 -*-
import pandas as pd
import json
import os

# 같은 폴더 내 엑셀 파일 이름
EXCEL_FILE = "celpip_script.xlsx"
OUTPUT_FILE = "data.json"

def excel_to_json(excel_path, output_path):
    # 1 엑셀 파일 읽기
    df = pd.read_excel(excel_path)

    # 2 필요한 컬럼만 추출 (en, ko, en_sample)
    required_cols = ["en", "ko", "en_sample"]
    df = df[required_cols]

    # 3 결측치(NaN)는 빈 문자열로
    df = df.fillna("")

    # 4 JSON 변환
    records = df.to_dict(orient="records")

    # 5 파일로 저장 (UTF-8, 한글 그대로)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f" 변환 완료: {output_path} ({len(records)}개 문장)")

if __name__ == "__main__":
    base_dir = os.path.dirname(__file__) or "."
    excel_path = os.path.join(base_dir, EXCEL_FILE)
    output_path = os.path.join(base_dir, OUTPUT_FILE)
    excel_to_json(excel_path, output_path)
