from __future__ import annotations

import json

import random

import threading

import time

from collections import deque

from datetime import datetime, timezone

class DummySensor:

    def __init__(self, seed: int | None = None):    #시드를 찾을 수 없다면 시드를 만든다는 함수

        if seed is not None:

            random.seed(seed)



    def set_env(self) -> dict:

        env = {

            "mars_base_internal_temperature": round(random.uniform(18.0, 26.0), 2),   # °C

            "mars_base_external_temperature": round(random.uniform(-80.0, -10.0), 2), # °C

            "mars_base_internal_humidity": round(random.uniform(25.0, 55.0), 1),      # %

            "mars_base_external_illuminance": round(random.uniform(0.0, 120000.0), 1),# lux

            "mars_base_internal_co2": round(random.uniform(400.0, 1200.0), 1),        # ppm

            "mars_base_internal_oxygen": round(random.uniform(19.0, 23.0), 2),        # %

        }

        return env

class MissionComputer: #설계도

    def __init__(self):

        self.ds = DummySensor()      # 문제 3에서 제작한 DummySensor를 ds라는 이름으로 인스턴스화

        self.env_v: dict = {   # 환경값 저장 딕셔너리
            "mars_base_internal_temperature": None,

            "mars_base_external_temperature": None,

            "mars_base_internal_humidity": None,

            "mars_base_external_illuminance": None,

            "mars_base_internal_co2": None,

            "mars_base_internal_oxygen": None,
        }

        self._stop_event = threading.Event()    # 안전 종료용 이벤트

        # 최근 5분(300초) 윈도우 데이터를 보관 (timestamp, env dict)
        self._window_sec = 300

        self._readings = deque() 
        self._last_avg_print_ts = 0.0


    def stop(self): 

        self._stop_event.set()


    def _now_ts(self) -> float:

        return time.time()


    def _now_iso(self) -> str:


        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


    def _prune_old(self, now_ts: float):

        """윈도우(최근 5분) 밖의 오래된 데이터를 제거"""

        cutoff = now_ts - self._window_sec

        while self._readings and self._readings[0][0] < cutoff:

            self._readings.popleft()


    def _compute_window_averages(self) -> dict | None:

        if not self._readings:

            return None

        # 키 집합은 env_v의 키를 그대로 사용

        keys = list(self.env_v.keys())

        sums = {k: 0.0 for k in keys}

        cnt = 0

        for _, env in self._readings:

            cnt += 1

            for k in keys:

                v = env.get(k)

                if v is None:

                    # None이 있으면 평균에서 제외하려면 별도 처리 필요. 단순화: None이면 0 처리
                    v = 0.0

                sums[k] += float(v)

        if cnt == 0:

            return None

        avgs = {k: round(sums[k] / cnt, 4) for k in keys}

        return avgs


    def _print_json(self, payload: dict):

        print(json.dumps(payload, ensure_ascii=False, indent=2)) # 데이터 직렬화

    def _start_input_listener(self):    #콘솔 입력을 별도 스레드에서 대기하여 정지 명령을 받으면 stop.

        def _listen():      #입력문자 종료

            try:

                while not self._stop_event.is_set():

                    user_in = input().strip().lower()

                    if user_in in ("q", "quit", "stop", "s"):

                        print("System stoped....")

                        self.stop()

                        break

            except EOFError:
                # 입력 스트림이 닫힐 수 있는 환경(예: 파이프) 대비
                pass

        t = threading.Thread(target=_listen, daemon=True)

        t.start()


    def get_sensor_data(self, interval_seconds: int = 5):     #5초마다 센서값을 가져와 출력하는 행동 메서드

        self._start_input_listener()


        # 초기에 한 번 바로 찍을 수도 있도록

        self._last_avg_print_ts = 0.0

        while not self._stop_event.is_set():

            now_ts = self._now_ts()

            # 1) 센서값 읽기

            latest = self.ds.set_env()


            # 2) env_v 갱신

            self.env_v.update(latest)


            # 3) 현재 스냅샷 JSON 출력 (타임스탬프 포함)

            snapshot = {

                "timestamp": self._now_iso(),

                "env_values": self.env_v

            }

            self._print_json(snapshot)

            # 4) 5분 윈도우에 추가 + 오래된 값 제거

            self._readings.append((now_ts, dict(self.env_v)))

            self._prune_old(now_ts)

            # 5) 5분 평균 출력 (직전 출력 시점으로부터 300초 경과 시)

            if (now_ts - self._last_avg_print_ts) >= self._window_sec:

                avgs = self._compute_window_averages()

                if avgs:

                    avg_payload = {

                        "timestamp": self._now_iso(),

                        "window_seconds": self._window_sec,

                        "env_5min_avg": avgs

                    }

                    print("=== 5-minute rolling averages ===")

                    self._print_json(avg_payload)

                    self._last_avg_print_ts = now_ts

            # 6) interval 동안 sleep 하되, 0.1초 단위로 체크하여 빠른 종료 반응성 확보

            slept = 0.0

            while slept < interval_seconds and not self._stop_event.is_set():

                time.sleep(0.1)

                slept += 0.1

# 스크립트 실행부

if __name__ == "__main__":

    RunComputer = MissionComputer()

    RunComputer.get_sensor_data(interval_seconds=5)
