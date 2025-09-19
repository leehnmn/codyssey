import csv

import random

from dataclasses import dataclass, field    

from datetime import datetime

from pathlib import Path

from typing import Dict, Any

# 로그 파일 이름 지정 (현재 스크립트와 동일한 폴더에 저장됨)

LOG_FILE = Path(__file__).with_name("mars_env_log.csv")

@dataclass
# dataclass 클래스를 만들때 데이터 담는 클래스를 쉽게 정의
class DummySensor:

    env_v: Dict[str, Any] = field(default_factory=dict)
    #field 사용 여기선 각 센서값을 저장할 env value 딕셔너리를 인스턴스 마다 독립적으로 갖게 하려고 사용


    def set_env(self) -> None:

    #환경 값을 무작위로 생성하여 env_v에 저장한다.

        self.env_v = {

            # 화성 기지 내부 온도: 18~30℃

            "mars_base_internal_temperature": round(random.uniform(18.0, 30.0), 1),

            # 화성 기지 외부 온도: 0~21℃

            "mars_base_external_temperature": round(random.uniform(0.0, 21.0), 1),

            # 화성 기지 내부 습도: 50~60%

            "mars_base_internal_humidity": round(random.uniform(50.0, 60.0), 1),

            # 화성 기지 외부 광량: 500~715 W/m^2

            "mars_base_external_illuminance": int(random.uniform(500, 715)),

            # 화성 기지 내부 이산화탄소 농도: 0.02~0.10%

            "mars_base_internal_co2": round(random.uniform(0.02, 0.10), 4),

            # 화성 기지 내부 산소 농도: 4~7%

            "mars_base_internal_oxygen": round(random.uniform(4.0, 7.0), 2),

        }

    def get_env(self) -> Dict[str, Any]:

        #env_v를 반환하고, 동시에 로그 파일에 기록한다.
        timestamp = datetime.now().strftime("%Y-%m-%D_%H:%M:%S")  # 현재 시간(초 단위까지) 기록

        with LOG_FILE.open("a", encoding="utf-8") as f:    #로그는 timestamp과 함께 저장된다.
            f.write(f"[{timestamp}] 화성 기지 환경값\n")
            for key, value in self.env_v.items():
                f.write(f" {key} : {value}\n")
            f.write("\n")

        
        return self.env_v

def main() -> None:

    """프로그램 실행 진입점"""

    ds = DummySensor()      # DummySensor 인스턴스 생성

    ds.set_env()            # 무작위 환경 값 생성

    current_env = ds.get_env()  # 현재 환경 값 + 로그 기록(보너스)

    print("현재 화성 기지 환경 값:")

    for k, v in current_env.items():

        print(f"  - {k}: {v}")

    print(f"로그가 저장되었습니다 → {LOG_FILE.name}")


if __name__ == "__main__":

    main()