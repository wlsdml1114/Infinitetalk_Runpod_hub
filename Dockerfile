# Use specific version of nvidia cuda image
FROM nvidia/cuda:12.8.1-cudnn-devel-ubuntu22.04 as runtime

# Remove any third-party apt sources to avoid issues with expiring keys.
RUN rm -f /etc/apt/sources.list.d/*.list

# Set shell and noninteractive environment variables
SHELL ["/bin/bash", "-c"]
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV SHELL=/bin/bash
ENV CUDA_HOME=/usr/local/cuda
ENV PATH="/usr/local/cuda/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"

# Set working directory
WORKDIR /

# Update and upgrade the system packages (Worker Template)
RUN apt-get update --yes && \
    apt-get upgrade --yes && \
    apt install --yes --no-install-recommends git wget curl bash libgl1 software-properties-common openssh-server nginx rsync ffmpeg && \
    apt-get install --yes --no-install-recommends build-essential libssl-dev libffi-dev libxml2-dev libxslt1-dev zlib1g-dev git-lfs && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt install python3.10-dev python3.10-venv -y --no-install-recommends && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    echo "en_US.UTF-8 UTF-8" > /etc/locale.gen

# Download and install pip
RUN ln -s /usr/bin/python3.10 /usr/bin/python && \
    rm /usr/bin/python3 && \
    ln -s /usr/bin/python3.10 /usr/bin/python3 && \
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python get-pip.py

RUN git clone https://github.com/MeiGen-AI/MultiTalk.git
WORKDIR /MultiTalk
    

ENV TORCH_CUDA_ARCH_LIST="8.6;8.9"
ENV MAX_JOBS=8
ENV EXT_PARALLEL=4
ENV NVCC_APPEND_FLAGS="--threads 8"

RUN pip install torch==2.7.0 torchvision torchaudio xformers --index-url https://download.pytorch.org/whl/cu128
RUN pip install misaki[en]
RUN pip install ninja 
RUN pip install psutil 
RUN pip install packaging 
RUN pip install flash_attn==2.7.4.post1 --no-build-isolation
RUN pip install -r requirements.txt
RUN pip install librosa ffmpeg
RUN pip uninstall -y transformers
RUN pip install transformers==4.48.2

WORKDIR /
RUN git clone https://github.com/thu-ml/SageAttention.git


RUN HF_HUB_DISABLE_PROGRESS_BARS=1 huggingface-cli download Wan-AI/Wan2.1-I2V-14B-480P --local-dir ./weights/Wan2.1-I2V-14B-480P
RUN HF_HUB_DISABLE_PROGRESS_BARS=1 huggingface-cli download TencentGameMate/chinese-wav2vec2-base --local-dir ./weights/chinese-wav2vec2-base
RUN HF_HUB_DISABLE_PROGRESS_BARS=1 huggingface-cli download TencentGameMate/chinese-wav2vec2-base model.safetensors --revision refs/pr/1 --local-dir ./weights/chinese-wav2vec2-base
RUN HF_HUB_DISABLE_PROGRESS_BARS=1 huggingface-cli download hexgrad/Kokoro-82M --local-dir ./weights/Kokoro-82M
RUN HF_HUB_DISABLE_PROGRESS_BARS=1 huggingface-cli download MeiGen-AI/MeiGen-MultiTalk --local-dir ./weights/MeiGen-MultiTalk
    
RUN mv weights/Wan2.1-I2V-14B-480P/diffusion_pytorch_model.safetensors.index.json weights/Wan2.1-I2V-14B-480P/diffusion_pytorch_model.safetensors.index.json_old
RUN ln -s /MultiTalk/weights/MeiGen-MultiTalk/diffusion_pytorch_model.safetensors.index.json weights/Wan2.1-I2V-14B-480P/
RUN ln -s /MultiTalk/weights/MeiGen-MultiTalk/multitalk.safetensors weights/Wan2.1-I2V-14B-480P/
    
RUN wget https://huggingface.co/vrgamedevgirl84/Wan14BT2VFusioniX/resolve/main/FusionX_LoRa/Wan2.1_I2V_14B_FusionX_LoRA.safetensors -O ./weights/Wan2.1_I2V_14B_FusionX_LoRA.safetensors
RUN wget https://huggingface.co/Kijai/WanVideo_comfy/resolve/main/Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors -O ./weights/Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors

COPY . .

RUN pip install runpod websocket-client

RUN chmod +x ./entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]

CMD ["python", "handler.py"] 