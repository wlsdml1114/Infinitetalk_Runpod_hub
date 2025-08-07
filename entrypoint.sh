#!/bin/bash
set -e # 스크립트 실행 중 에러가 발생하면 즉시 중단

export HF_HUB_ENABLE_HF_TRANSFER=1
export HF_HUB_DISABLE_PROGRESS_BARS=1

# 모든 설치가 완료되었는지 확인하는 플래그 파일 경로
INSTALL_FLAG="/opt/all_installed.flag"

# 플래그 파일이 없다면, 첫 실행으로 간주하고 모든 설치 및 다운로드 진행
if [ ! -f "$INSTALL_FLAG" ]; then
    echo ">>> First time running. Performing initial setup..."

    # SageAttention은 base 이미지에서 이미 설치됨
    echo ">>> SageAttention already installed in base image"

    # 1. 모델 가중치 및 파일 다운로드
    echo ">>> Downloading models... This may take a while."
    cd /MultiTalk

    hf download Wan-AI/Wan2.1-I2V-14B-480P --local-dir ./weights/Wan2.1-I2V-14B-480P
    hf download TencentGameMate/chinese-wav2vec2-base --local-dir ./weights/chinese-wav2vec2-base
    hf download TencentGameMate/chinese-wav2vec2-base model.safetensors --revision refs/pr/1 --local-dir ./weights/chinese-wav2vec2-base
    hf download hexgrad/Kokoro-82M --local-dir ./weights/Kokoro-82M
    hf download MeiGen-AI/MeiGen-MultiTalk --local-dir ./weights/MeiGen-MultiTalk
    
    mv ./weights/Wan2.1-I2V-14B-480P/diffusion_pytorch_model.safetensors.index.json ./weights/Wan2.1-I2V-14B-480P/diffusion_pytorch_model.safetensors.index.json_old
    wget -q https://huggingface.co/vrgamedevgirl84/Wan14BT2VFusioniX/resolve/main/FusionX_LoRa/Wan2.1_I2V_14B_FusionX_LoRA.safetensors -O ./weights/Wan2.1_I2V_14B_FusionX_LoRA.safetensors
    wget -q https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors -O ./weights/Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors

    # 2. 파일 이름 변경 및 심볼릭 링크 생성
    echo ">>> Setting up symbolic links for models..."
    ln -s /MultiTalk/weights/MeiGen-MultiTalk/diffusion_pytorch_model.safetensors.index.json /MultiTalk/weights/Wan2.1-I2V-14B-480P/
    ln -s /MultiTalk/weights/MeiGen-MultiTalk/multitalk.safetensors /MultiTalk/weights/Wan2.1-I2V-14B-480P/


    # 4. 모든 과정이 완료되었음을 알리는 플래그 파일 생성
    echo ">>> Initial setup complete."
    touch "$INSTALL_FLAG"
else
    echo ">>> Setup has already been completed. Skipping."
fi

# CMD로 전달된 원래 명령어를 실행 (예: python handler.py)
echo ">>> Starting application..."
cd /
python handler.py
