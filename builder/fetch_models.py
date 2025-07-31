# from faster_whisper import WhisperModel
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
# from runpod.serverless.utils import rp_cuda
# model_names = ["tiny", "base", "small", "medium", "large-v1", "large-v2", "large-v3"]


def load_model():
    '''
    Load and cache models in parallel
    '''
    # device="cuda" if rp_cuda.is_available() else "cpu",
    # torch_dtype="float16" if rp_cuda.is_available() else "float32"

    # device = "cuda:0" if torch.cuda.is_available() else "cpu"
    # torch_dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    # # model_id = "openai/whisper-large-v2"
    # model_id = "openai/whisper-large-v3-turbo"

    # model = AutoModelForSpeechSeq2Seq.from_pretrained(
    #     model_id, torch_dtype=torch_dtype, low_cpu_mem_usage=True, use_safetensors=True
    # )
    # model.to(device)

    # processor = AutoProcessor.from_pretrained(model_id)

    # pipe = pipeline(
    #     "automatic-speech-recognition",
    #     model=model,
    #     tokenizer=processor.tokenizer,
    #     feature_extractor=processor.feature_extractor,
    #     max_new_tokens=128,
    #     chunk_length_s=30,
    #     batch_size=1,
    #     return_timestamps=True,
    #     torch_dtype=torch_dtype,
    #     device=device,
    # )


load_model()