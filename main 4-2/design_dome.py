from __future__ import annotations

from typing import Tuple, Dict

from math import pi


LAST_RESULT: Dict[str, float | str] = {}

DENSITY_G_CM3 = {
    'glass': 2.4,

    'aluminum': 2.7,

    'carbon_steel': 7.85,

    '유리': 2.4,

    '알루미늄': 2.7,

    '탄소강': 7.85,
}
VALID_MATERIALS = ('glass', 'aluminum', 'carbon_steel', '유리', '알루미늄', '탄소강')

#밀도 입력표 단위: g/cm^3  →  kg/m^3 로 변환( * 1000 )
def to_kg_per_m3(rho_g_cm3: float) -> float:

    return rho_g_cm3 * 1000.0


#반구체(hemisphere) 곡면적: 2 * pi * r^2  [m^2]
def sphere_area(diameter: float) -> float:

    if diameter <= 0:

        raise ValueError('지름은 0보다 커야 합니다.')

    r = diameter / 2.0

    return 2.0 * pi * (r ** 2)


def compute_weight_mars(area_m2: float, thickness_cm: float, material: str) -> Tuple[float, float]:

    if thickness_cm <= 0:

        raise ValueError('두께는 0보다 커야 합니다.')

    key = material.strip()

    if key not in DENSITY_G_CM3:

        raise ValueError(f'지원하지 않는 재질입니다: {material}')

    rho_kg_m3 = to_kg_per_m3(DENSITY_G_CM3[key])

    thickness_m = thickness_cm / 100.0

    volume_m3 = area_m2 * thickness_m

    mass_kg = rho_kg_m3 * volume_m3
    #"무게"는 요구사항에 맞춰 화성 중력(지구의 0.38배)을 반영한 kg 등가값으로 표기
    weight_mars_kg_equiv = mass_kg * 0.38  

    return mass_kg, weight_mars_kg_equiv


def run_once() -> None:

    global LAST_RESULT

    try:

        raw_d = input('지름(m)을 입력하세요 (예: 10): ').strip()

        diameter = float(raw_d)

        raw_material = input('재질(glass/aluminum/carbon_steel 또는 유리/알루미늄/탄소강): ').strip()

        raw_t = input('두께(cm)를 입력하세요 (기본 1, 엔터 시 1): ').strip()
        # 얇은 껍질 가정: 체적 ≈ 면적 * 두께  [m^3], 두께 기본 1 cm
        thickness = float(raw_t) if raw_t else 1.0


        if raw_material not in VALID_MATERIALS:

            raise ValueError('재질은 glass, aluminum, carbon_steel 또는 유리/알루미늄/탄소강 중 하나여야 합니다.')


        area_m2 = sphere_area(diameter)
    
        mass_kg, weight_mars_kg = compute_weight_mars(area_m2, thickness, raw_material)


        LAST_RESULT = {

            'material': raw_material,

            'diameter_m': diameter,

            'thickness_cm': thickness,

            'area_m2': area_m2,

            'weight_mars_kg': weight_mars_kg,
        }


        print(f'재질 ⇒ {raw_material}, 지름 ⇒ {diameter:.3f}, 두께 ⇒ {thickness:.3f}, '

              f'면적 ⇒ {area_m2:.3f}, 무게 ⇒ {weight_mars_kg:.3f} kg')



    except ValueError as ve:

        print(f'[입력 오류] {ve}')

    except Exception as e:

        print(f'[오류] 처리 중 문제가 발생했습니다: {e}')


def main() -> None:

    print('=== Mars 돔 구조물 설계 프로그램 ===')

    while True:

        run_once()

        ans = input('계속하시겠습니까? (Y/N): ').strip().lower()

        if ans in ('n'):

            print('프로그램을 종료합니다.')

            break


if __name__ == '__main__':

    main()