from __future__ import annotations

import argparse, csv, json, re

from datetime import datetime

from pathlib import Path

from typing import Any, Iterable

RISK_KEYWORDS = ("explosion", "누출", "고온", "Oxygen")

def resolve_paths(log_arg: str | None, out_arg: str | None) -> tuple[Path, Path]:

    base = Path.cwd()

    log = Path(log_arg).expanduser().resolve() if log_arg else (base / "mission_computer_main.log")

    out = Path(out_arg).expanduser().resolve() if out_arg else (base / "result")

    return log, out

def read_log_csv(path: Path) -> list[dict[str, Any]]:

    if not path.exists():

        raise FileNotFoundError(f"로그 파일 없음: {path}")


    with path.open("r", encoding="utf-8-sig", newline="") as f:

        rows: list[dict[str, Any]] = []

        for i, row in enumerate(csv.DictReader(f), 1):

            rows.append({(k.strip() if isinstance(k,str) else k):

                         (v.strip() if isinstance(v,str) else v)

                         for k, v in row.items()} | {"orig_idx": i})

    return rows

def parse_ts(s: Any) -> datetime | None:

    if isinstance(s, str):

        try: return datetime.strptime(s.strip(), "%Y-%m-%d %H:%M:%S")

        except ValueError: return None

    return None

def sort_desc_by_timestamp(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:

    key = lambda r: parse_ts(r.get("timestamp")) or datetime.min

    return sorted(rows, key=key, reverse=True)

def list_to_indexed_dict(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:

    return {i: r for i, r in enumerate(rows, 1)}

#----------------------------- save -------------------------------------------

def timestamped_json_path(result_path: Path, *, stem: str) -> Path:

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    p = result_path

    if p.suffix.lower() == ".json":
    
        p.parent.mkdir(parents=True, exist_ok=True)

        return p.with_name(f"{p.stem}_{ts}.json")

    p.mkdir(parents=True, exist_ok=True)

    return p / f"{stem}_{ts}.json"

def save_json(data: dict[int, dict[str, Any]] | list[dict[str, Any]], out: Path) -> Path:

    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    return out

def save_risk_only(rows: list[dict[str, Any]], out_dir: Path) -> Path:

    out_dir.mkdir(parents=True, exist_ok=True)

    pat = re.compile("|".join(re.escape(k) for k in RISK_KEYWORDS), re.IGNORECASE)

    filt = [r for r in rows if any(isinstance(v,str) and pat.search(v) for v in r.values())]

    out = out_dir / f"risk_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    return save_json(filt, out)

def search_in_json(json_path: Path, query: str) -> list[dict[str, Any]]:

    if not json_path.exists():

        print(f"[경고] JSON 없음: {json_path}"); return []

    data = json.loads(json_path.read_text(encoding="utf-8"))

    rows: Iterable[dict[str, Any]] = list(data.values()) if isinstance(data, dict) else (data if isinstance(data, list) else [])

    q = query.lower()

    return [r for r in rows if any(isinstance(v,str) and q in v.lower() for v in r.values())]

# ---------- main ----------------------------------------------------------------------

def main() -> int:

    ap = argparse.ArgumentParser(description="mission_computer_main.log 분석기 (경량)")

    ap.add_argument("log", nargs="?", help="로그 파일 경로 (기본: ./mission_computer_main.log)")

    ap.add_argument("out", nargs="?", help="결과 경로(폴더 또는 .json) (기본: ./result)")

    ap.add_argument("--search", default="", help="저장 JSON에서 부분 검색어")

    args = ap.parse_args()



    log_path, out_path = resolve_paths(args.log, args.out)

    try:

        rows = read_log_csv(log_path)

    except (FileNotFoundError, UnicodeDecodeError) as e:

        print(f"[오류] {e}"); return 1



    print("— 원본 (전체) —")

    for r in rows: print(r)

    sorted_rows = sort_desc_by_timestamp(rows)

    print("\n— timestamp 역순 (전체) —")

    for r in sorted_rows: print(r)

    indexed = list_to_indexed_dict(sorted_rows)

    print("\n— 리스트→딕셔너리 1-base (전체) —")

    for k, v in indexed.items(): print(k, ":", v)

    json_path = timestamped_json_path(out_path, stem=log_path.stem)

    save_json(indexed, json_path)

    print(f"\n[OK] JSON 저장: {json_path}")
    
    risk_path = save_risk_only(sorted_rows, json_path.parent)

    print(f"[OK] 위험 로그 저장: {risk_path}")

    if args.search.strip():

        hits = search_in_json(json_path, args.search.strip())

        print(f"— 검색 결과({len(hits)}건) —")

        for h in hits[:200]: print(h)

    return 0

if __name__ == "__main__":

    raise SystemExit(main())