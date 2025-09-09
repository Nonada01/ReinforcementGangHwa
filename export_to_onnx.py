import torch
from stable_baselines3 import PPO
import numpy as np

# 1. 학습된 모델 불러오기
model = PPO.load("whac_a_mole_model_v2.zip")

# 2. 모델의 정책 네트워크만 추출 (이 부분이 실제 의사결정을 하는 AI)
policy = model.policy

# 3. ONNX로 변환하기 위한 더미 입력 데이터 생성
#    관찰 공간(observation space)의 모양과 일치해야 함: (9,)
#    (배치 크기 1을 추가하여 [1, 9] 모양으로 만듦)
dummy_input = torch.randn(1, 9)

# 4. ONNX 파일로 내보내기
onnx_file_path = "whac-a-mole.onnx"
torch.onnx.export(
    policy,
    dummy_input,
    onnx_file_path,
    opset_version=11,
    input_names=['observation'],  # JavaScript에서 사용할 입력 이름
    output_names=['action'],     # JavaScript에서 사용할 출력 이름
)

print(f"✅ 모델이 성공적으로 '{onnx_file_path}' 파일로 변환되었습니다!")
print("이제 이 파일을 웹 프로젝트 폴더로 옮겨주세요.")