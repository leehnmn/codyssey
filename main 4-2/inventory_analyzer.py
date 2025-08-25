from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple

from pathlib import Path

import csv

import pickle


SRC_CSV = Path('Mars_Base_Inventory_List.csv')

DANGER_CSV = Path('Mars_Base_Inventory_danger.csv')

BIN_FILE = Path('Mars_Base_Inventory_List.bin')

FI_CANDIDATE_KEYS = ('flammability', 'flammability_index', 'flammability idx', 'fi')


 #전체 목록 출력
def _find_fi_key(header: List[str]) -> Optional[str]:

    lower = [h.strip().lower() for h in header]

    for key in FI_CANDIDATE_KEYS:

        if key in lower:

            return header[lower.index(key)]

    for i, h in enumerate(lower):

        if 'flammability' in h:

            return header[i]

    return None


def _fmt_float(x: Any) -> str:

    try:

        return f'{float(x):.3f}'

    except Exception:

        return str(x)


#파싱하여 List[dict] 로 변환 후 인화성 지수 내림차순 정렬 출력
def read_inventory_csv(path: Path) -> Tuple[List[Dict[str, Any]], str]:

    if not path.exists():

        raise FileNotFoundError(f'입력 CSV를 찾을 수 없습니다: {path}')

    rows: List[Dict[str, Any]] = []

    with path.open('r', encoding='utf-8', newline='') as f:

        reader = csv.DictReader(f)

        if reader.fieldnames is None:

            raise ValueError('CSV 헤더를 찾을 수 없습니다. 헤더를 포함해 주세요.')

        fi_key = _find_fi_key(reader.fieldnames)

        if not fi_key:

            raise KeyError('인화성 지수 컬럼을 찾을 수 없습니다. 가능한 헤더: '

                           f"{', '.join(FI_CANDIDATE_KEYS)} 또는 '...flammability...' 포함 헤더")

        for line in reader:

            line = {k: (v.strip() if isinstance(v, str) else v) for k, v in line.items()}

            try:

                line['_fi'] = float(line[fi_key])

            except Exception:

                continue

            rows.append(line)

    return rows, fi_key


def sort_by_fi_desc(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    return sorted(rows, key=lambda d: d.get('_fi', -1.0), reverse=True)


#인화성 지수 >= 0.7 만 필터링하여 별도 출력
def filter_danger(rows: List[Dict[str, Any]], threshold: float = 0.7) -> List[Dict[str, Any]]:

    return [r for r in rows if isinstance(r.get('_fi'), float) and r['_fi'] >= threshold]


#Mars_Base_Inventory_danger.csv 저장
def save_csv(path: Path, rows: List[Dict[str, Any]]) -> None:

    if not rows:

        with path.open('w', encoding='utf-8', newline='') as f:

            f.write('')

        return

    keys = [k for k in rows[0].keys() if k != '_fi']

    with path.open('w', encoding='utf-8', newline='') as f:

        writer = csv.DictWriter(f, fieldnames=keys)

        writer.writeheader()

        for r in rows:

            out = {k: (f'{r[k]:.3f}' if isinstance(r.get(k), float) else r.get(k)) for k in keys}
            #모든 수치 출력은 소수점 3자리까지
            writer.writerow(out)


# 표준 라이브러리만 사용 (pickle 사용해 이진 저장)
def save_binary(path: Path, data: Any) -> None:

    with path.open('wb') as f:     #write binary

        pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

def load_binary(path: Path) -> Any:

    with path.open('rb') as f:      #read binary

        return pickle.load(f)


def print_table(rows: List[Dict[str, Any]], fi_key: str) -> None:

    if not rows:

        print('[정보] 출력할 데이터가 없습니다.')

        return

    headers = [k for k in rows[0].keys() if k != '_fi']

    print(' | '.join(headers + ['flammability']))

    print('-' * 80)

    for r in rows:

        vals = []

        for h in headers:

            v = r.get(h, '')

            if isinstance(v, float):

                vals.append(f'{v:.3f}')

            else:

                vals.append(str(v))

        fi_val = r.get('_fi', r.get(fi_key, ''))

        vals.append(_fmt_float(fi_val))

        print(' | '.join(vals))


def main() -> None:

    try:

        rows, fi_key = read_inventory_csv(SRC_CSV)

        print('[원본 전체 출력]')

        print_table(rows, fi_key)

    except Exception as e:

        print(f'[오류] CSV 읽기 실패: {e}')

        return



    sorted_rows = sort_by_fi_desc(rows)

    print('\n[인화성 지수 내림차순 정렬 출력]')

    print_table(sorted_rows, fi_key)


#인화성 지수 >= 0.7 만 필터링하여 별도 출력
    danger_rows = filter_danger(sorted_rows, threshold=0.7)

    print('\n[위험 항목(>=0.700) 출력]')

    print_table(danger_rows, fi_key)


#정렬 리스트를 이진 파일(Mars_Base_Inventory_List.bin)로 저장/재로딩/출력

    try:

        save_csv(DANGER_CSV, danger_rows)

        print(f'\n[저장 완료] {DANGER_CSV}')

    except Exception as e:

        print(f'[오류] 위험 CSV 저장 실패: {e}')



    try:

        save_binary(BIN_FILE, sorted_rows)

        print(f'[이진 저장 완료] {BIN_FILE}')

        reloaded = load_binary(BIN_FILE)

        print('[이진 파일 재로딩 출력]')

        print_table(reloaded, fi_key)

    except Exception as e:

        print(f'[오류] 이진 파일 저장/로드 실패: {e}')


if __name__ == '__main__':

    main()
