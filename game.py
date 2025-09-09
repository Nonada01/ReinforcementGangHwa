# ===============================================================
# 1단계: 라이브러리 설치
# ===============================================================
# VS Code 터미널에 아래 명령어를 한 줄씩 입력하여 라이브러리를 설치하세요.
# pip install stable-baselines3[extra] pygame moviepy
# pip install gymnasium
# pip install tensorboard

# ===============================================================
# 2단계: 게임 환경 코드 (보상 로직 수정 완료)
# ===============================================================
import pygame
import random
import sys
import numpy as np
import gymnasium as gym
from gymnasium import spaces

# --- 게임 상수 ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (50, 205, 50)
BROWN = (139, 69, 19)

class Mole:
    def __init__(self, mole_image):
        self.image = mole_image
        self.rect = self.image.get_rect()
        self.is_up = False
        self.timer = 0
        self.hide_time = 60
        self.current_hole_pos = None

    def pop(self, position, score):
        if not self.is_up:
            self.is_up = True
            self.rect.center = position
            self.current_hole_pos = position
            self.hide_time = max(20, 60 - score // 5)
            self.timer = 0
            return True
        return False

    def hide(self):
        self.is_up = False
        self.current_hole_pos = None

    def update(self):
        if self.is_up:
            self.timer += 1
            if self.timer > self.hide_time:
                self.hide()
                return True  # 놓쳤다는 신호
        return False

    def draw(self, surface):
        if self.is_up:
            surface.blit(self.image, self.rect)

class WhacAMoleEnv(gym.Env):
    metadata = {'render_modes': ['human', 'rgb_array'], 'render_fps': FPS}

    def __init__(self, render_mode=None):
        super().__init__()
        self.render_mode = render_mode
        self.screen = None
        self.clock = None
        self.font = None
        
        # 두더지 구멍 9개 위치 설정
        self.hole_positions = [(160 + c * 200, 150 + r * 150) for r in range(3) for c in range(3)]
        
        # 관찰 공간: 9개 구멍의 상태 (0: 비어있음, 0~1: 두더지가 있고 남은 시간)
        self.observation_space = spaces.Box(low=0.0, high=1.0, shape=(9,), dtype=np.float32)
        
        # 행동 공간: 0 (아무것도 안 함), 1~9 (각 구멍 때리기)
        self.action_space = spaces.Discrete(10)

    def _get_obs(self):
        obs = np.zeros(9, dtype=np.float32)
        active_moles = {mole.current_hole_pos: mole for mole in self.moles if mole.is_up}
        for i, pos in enumerate(self.hole_positions):
            if pos in active_moles:
                mole = active_moles[pos]
                # 두더지가 사라지기까지 남은 시간을 0과 1 사이 값으로 정규화
                obs[i] = max(0.0, (mole.hide_time - mole.timer) / mole.hide_time)
        return obs

    def _get_info(self):
        return {"score": self.score, "missed_moles": self.missed_moles}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.score = 0
        self.missed_moles = 0
        self._init_mole_image()
        self.moles = [Mole(self.mole_image) for _ in range(3)] # 동시에 최대 3마리
        self.mole_spawn_timer = 0
        
        if self.render_mode == "human":
            self._render_init()
            
        return self._get_obs(), self._get_info()

    def step(self, action):
        reward = 0

        if action > 0:
            hit_pos = self.hole_positions[action - 1]
            hit_success = False
            for mole in self.moles:
                if mole.is_up and mole.rect.center == hit_pos:
                    mole.hide()
                    self.score += 1
                    # [수정] 성공 보상을 +1.0에서 +10.0으로 대폭 상향
                    reward += 10.0
                    hit_success = True
                    break
            # [수정] 헛스윙(-0.1) 페널티를 제거하여 적극적인 탐색 유도
        
        self.mole_spawn_timer += 1
        spawn_rate = max(15, 60 - self.score)
        if self.mole_spawn_timer > spawn_rate:
            self.mole_spawn_timer = 0
            inactive_moles = [m for m in self.moles if not m.is_up]
            available_holes = list(set(self.hole_positions) - {m.current_hole_pos for m in self.moles if m.is_up})
            if inactive_moles and available_holes:
                random.choice(inactive_moles).pop(random.choice(available_holes), self.score)

        for mole in self.moles:
            if mole.update():  # 두더지가 스스로 숨었다면 (놓쳤다면)
                self.missed_moles += 1
                # [수정] 놓쳤을 때 페널티를 -1.0에서 -5.0으로 조정
                reward -= 5.0

        terminated = self.missed_moles >= 10
        if terminated:
            reward -= 5.0 # 게임 종료 페널티는 유지

        if self.render_mode == "human":
            self.render()
            
        return self._get_obs(), reward, terminated, False, self._get_info()

    def _init_mole_image(self):
        self.mole_image = pygame.Surface((100, 80))
        self.mole_image.fill(BROWN)
        pygame.draw.circle(self.mole_image, BLACK, (30, 30), 10)
        pygame.draw.circle(self.mole_image, BLACK, (70, 30), 10)

    def _render_init(self):
        if self.screen is None:
            pygame.init()
            pygame.display.init()
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        if self.clock is None:
            self.clock = pygame.time.Clock()
        if self.font is None:
            self.font = pygame.font.Font(None, 48)

    def render(self):
        # human 모드일 때 Pygame 창을 통해 게임 상태를 시각화 (현재는 비어있음)
        # 게임 플레이를 직접 보려면 이 함수 내부에 그리기 코드를 추가해야 합니다.
        pass

    def close(self):
        if self.screen is not None:
            pygame.display.quit()
            pygame.quit()
            self.screen = None

# ===============================================================
# 3단계: AI 에이전트 학습
# ===============================================================
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
import os

if __name__ == '__main__':
    # 로그를 저장할 디렉터리 이름
    log_dir = "./tensorboard_logs/"
    os.makedirs(log_dir, exist_ok=True)

    # 환경 불러오기 (병렬 처리를 위해 4개 환경 동시 실행)
    vec_env = make_vec_env(WhacAMoleEnv, n_envs=4)

    # PPO 모델 생성 및 텐서보드 로그 경로 지정
    model = PPO('MlpPolicy',
                vec_env,
                verbose=1,
                tensorboard_log=log_dir)

    # 모델 학습 (학습 횟수를 늘려 더 나은 성능 기대)
    print("🤖 모델 학습을 시작합니다...")
    model.learn(total_timesteps=1000000,
                tb_log_name="PPO_WhacAMole_v2") # 로그 이름 변경

    # 학습된 모델 저장
    model_path = "whac_a_mole_model_v2.zip"
    model.save(model_path)

    print("\n✅ 모델 학습 및 저장이 성공적으로 완료되었습니다!")
    print(f"텐서보드 로그는 '{log_dir}' 디렉터리에 저장되었습니다.")
    print(f"학습된 모델은 '{model_path}' 파일로 저장되었습니다.")
    print("\nℹ️ 텐서보드를 실행하려면 터미널에 다음 명령어를 입력하세요:")
    print(f"tensorboard --logdir {log_dir}")