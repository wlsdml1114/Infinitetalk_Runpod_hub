# Use specific version of nvidia cuda image
FROM wlsdml1114/multitalk-base:1.0 as runtime

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