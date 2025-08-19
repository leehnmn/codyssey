"""
mission_computer_main.log 분석 스크립트 (전체 출력 버전)
"""

from __future__ import annotations

import argparse

import csv

import json

import re

from collections import Counter

from datetime import datetime

from pathlib import Path

from typing import Any, Iterable



RISK_KEYWORDS: tuple[str, ...] = ("폭발", "누출", "고온", "Oxygen")





def resolve_paths(log_arg: str | None, out_arg: str | None) -> tuple[Path, Path]:

    base = Path.cwd()

    log = Path(log_arg).expanduser().resolve() if log_arg else (base / "mission_computer_main.log")

    out = Path(out_arg).expanduser().resolve() if out_arg else (base / "result")

    return log, out

def read_log_csv(path: Path) -> list[dict[str, Any]]:

    if not path.exists():

        raise FileNotFoundError(f"로그 파일 없음: {path}")

    for enc in ("utf-8", "utf-8-sig"):

        try:

            with path.open("r", encoding=enc, newline="") as f:

                sample = f.read(4096)

                f.seek(0)

                try:

                    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")

                except csv.Error:

                    dialect = csv.get_dialect("excel")



                reader = csv.DictReader(f, dialect=dialect)

                rows: list[dict[str, Any]] = []

                for i, row in enumerate(reader, start=1):

                    cleaned = {

                        (k.strip() if isinstance(k, str) else k):

                        (v.strip() if isinstance(v, str) else v)

                        for k, v in row.items()

                    }

                    cleaned["orig_idx"] = i

                    rows.append(cleaned)

                return rows

        except UnicodeDecodeError:

            continue

    raise UnicodeDecodeError("utf-8/utf-8-sig", b"", 0, 1, "지원 인코딩으로 디코딩 실패")

def parse_ts_safe(s: Any) -> datetime | None:

    if isinstance(s, str):

        try:

            return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S")

        except ValueError:

            return None

    return None

def sort_desc_by_timestamp(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:

    def key(row: dict[str, Any]) -> datetime:

        return parse_ts_safe(row.get("timestamp")) or datetime.min

    return sorted(rows, key=key, reverse=True)

def list_to_indexed_dict(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:

    return {i: r for i, r in enumerate(rows, start=1)}

def timestamped_json_path(result_path: Path, *, stem: str) -> Path:

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    p = result_path

    if p.suffix.lower() == ".json":

        p = p.with_suffix(".json")

        p.parent.mkdir(parents=True, exist_ok=True)

        return p.with_name(f"{p.stem}_{ts}.json")

    p.mkdir(parents=True, exist_ok=True)

    return p / f"{stem}_{ts}.json"

def save_json(data: dict[int, dict[str, Any]] | list[dict[str, Any]], out: Path) -> Path:

    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def save_risk_only(rows: list[dict[str, Any]], out_dir: Path) -> Path:

    out_dir.mkdir(parents=True, exist_ok=True)

    pattern = re.compile("|".join(re.escape(k) for k in RISK_KEYWORDS), re.IGNORECASE)

    filtered = [

        row for row in rows

        if any(isinstance(v, str) and pattern.search(v) for v in row.values())

    ]
    out = out_dir / f"risk_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    out.write_text(json.dumps(filtered, ensure_ascii=False, indent=2), encoding="utf-8")

    return out

def search_in_json(json_path: Path, query: str) -> list[dict[str, Any]]:

    if not json_path.exists():

        print(f"[경고] JSON 없음: {json_path}")

        return []

    data = json.loads(json_path.read_text(encoding="utf-8"))

    if isinstance(data, dict):

        rows: Iterable[dict[str, Any]] = list(data.values())

    elif isinstance(data, list):

        rows = data

    else:

        print("[주의] 지원하지 않는 JSON 구조")

        return []

    q = query.lower()

    return [row for row in rows if any(isinstance(v, str) and q in v.lower() for v in row.values())]

def generate_md_report(rows: list[dict[str, Any]], out_path: Path) -> Path:

    total = len(rows)

    times = [t for r in rows if (t := parse_ts_safe(r.get("timestamp")))]

    start = min(times).strftime("%Y-%m-%d %H:%M:%S") if times else "N/A"

    end = max(times).strftime("%Y-%m-%d %H:%M:%S") if times else "N/A"

    level_counter: Counter[str] = Counter()

    for r in rows:

        level = r.get("level") or r.get("event")

        if isinstance(level, str) and level:

            level_counter[level] += 1

    lines: list[str] = []

    lines += [

        "# 사고 원인 분석 보고서(자동생성)",

        "",

        f"- 생성 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",

        f"- 로그 총 개수: **{total}**",

        f"- 관찰 구간: **{start} ~ {end}**",

        "",

        "## 1) 로그 수준(Level) 분포",

    ]

    if level_counter:

        for lvl, cnt in level_counter.most_common():

            lines.append(f"- {lvl}: {cnt}")

    else:

        lines.append("- 레벨 정보 없음")

    lines.append("")

    lines.append("## 2) 데이터 품질 메모")

    lines.append("- timestamp 포맷 미준수 시 정렬 정확도 저하")

    lines.append("- 스키마 불일치 시 필드 인식 제한")

    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")

    return out_path

def main() -> int:

    parser = argparse.ArgumentParser(description="mission_computer_main.log 분석기")

    parser.add_argument("log", nargs="?", help="로그 파일 경로 (기본: ./mission_computer_main.log)")

    parser.add_argument("out", nargs="?", help="결과 경로(디렉터리 또는 .json) (기본: ./result)")

    parser.add_argument("--search", default="", help="JSON 대상 검색어")

    args = parser.parse_args()



    log_path, out_path = resolve_paths(args.log, args.out)

    try:
        rows = read_log_csv(log_path)

    except Exception as e:

        print(f"[오류] {e}")

        return 1

    # ① 원본 전체 출력

    print("— 원본 로그 전체 —")

    for r in rows:

        print(r)

    # ② 역순 정렬 전체 출력

    sorted_rows = sort_desc_by_timestamp(rows)

    print("\n— timestamp 기준 역순 정렬 전체 —")

    for r in sorted_rows:

        print(r)

    # ③ 리스트→딕셔너리 전체 출력

    print("\n— 딕셔너리 변환 전체 —")

    indexed = list_to_indexed_dict(sorted_rows)

    for k, v in indexed.items():

        print(k, ":", v)

    # ④ JSON 저장

    json_path = timestamped_json_path(out_path, stem=log_path.stem)

    save_json(indexed, json_path)

    print(f"\n[OK] JSON 저장: {json_path}")

    md_path = generate_md_report(sorted_rows, Path("log_analysis.md"))

    print(f"[OK] 보고서 저장: {md_path.resolve()}")

    risk_path = save_risk_only(sorted_rows, json_path.parent)

    print(f"[OK] 위험 로그 저장: {risk_path}")

    query = args.search.strip() or input("검색어 입력(엔터=스킵): ").strip()

    if query:

        hits = search_in_json(json_path, query)

        print(f"— 검색 결과({len(hits)}건) —")

        for h in hits:

            print(h)

    return 0

if __name__ == "__main__":

    raise SystemExit(main())