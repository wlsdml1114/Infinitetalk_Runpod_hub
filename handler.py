import runpod
from runpod.serverless.utils import rp_upload
import os
import base64
import json
import uuid
import shutil
import subprocess # subprocess 모듈 추가
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def handler(job):
    """
    서버리스 워커의 메인 핸들러 함수입니다.
    (수정 불가능한 스크립트를 subprocess로 실행)
    """
    job_input = job.get("input", {})

    # 각 job에 대한 고유한 임시 작업 폴더 생성
    task_id = f"task_{uuid.uuid4()}"
    os.makedirs(task_id, exist_ok=True)
    
    try:
        # --- 1. 입력 데이터 파싱 ---
        prompt = job_input.get("prompt")
        image_path = job_input.get("image_path")
        audio_paths = job_input.get("audio_paths", {})
        audio_type = job_input.get("audio_type")

        if not all([prompt, image_path, audio_paths]):
            return {"error": "필수 입력값(prompt, image_path, audio_paths)이 누락되었습니다."}

        # --- 2. generate_multitalk를 위한 input.json 생성 ---
        input_data_for_script = {
            "prompt": prompt,
            "cond_image": image_path,
            "cond_audio": audio_paths
        }
        
        # audio_type 값이 있는 경우에만 딕셔너리에 추가합니다.
        if audio_type:
            input_data_for_script["audio_type"] = audio_type
        
        input_json_path = os.path.join(task_id, "input.json")
        with open(input_json_path, 'w', encoding='utf-8') as f:
            json.dump(input_data_for_script, f, ensure_ascii=False, indent=4)

        # --- 3. CLI 명령어 리스트 생성 ---
        
        output_filename = "generated_video.mp4"
        output_video_path = os.path.join(task_id, output_filename)

        # 실행할 CLI 명령어를 리스트 형태로 구성합니다.
        # 모든 인자 값은 문자열(string) 형태여야 합니다.
        # 작업 디렉토리를 /MultiTalk로 설정하고 절대 경로 사용
        command = [
            'python', '/MultiTalk/generate_multitalk.py',
            '--ckpt_dir', '/MultiTalk/weights/Wan2.1-I2V-14B-480P',
            '--wav2vec_dir', '/MultiTalk/weights/chinese-wav2vec2-base',
            '--input_json', input_json_path,
            '--quant', 'int8',
            '--quant_dir', '/MultiTalk/weights/MeiGen-MultiTalk',
            '--lora_dir', '/MultiTalk/weights/MeiGen-MultiTalk/quant_models/quant_model_int8_FusionX.safetensors',
            '--sample_text_guide_scale', str(job_input.get("sample_text_guide_scale", 1.0)),
            '--use_teacache', # 플래그 인자는 값 없이 이름만 추가
            '--sample_audio_guide_scale', str(job_input.get("sample_audio_guide_scale", 2.0)),
            '--sample_steps', str(job_input.get("sample_steps", 8)),
            '--mode', job_input.get("mode", "streaming"),
            '--num_persistent_param_in_dit', '0',
            '--save_file', output_video_path,
            '--sample_shift', '2'
        ]
        
        # --- 4. Subprocess를 사용하여 스크립트 실행 ---
        
        print(f"명령어 실행: {' '.join(command)}")
        
        # check=True: 명령 실행 실패 시 CalledProcessError 발생
        # capture_output=True: stdout, stderr 캡처
        # text=True: stdout, stderr를 텍스트로 디코딩
        # cwd='/MultiTalk': 작업 디렉토리를 /MultiTalk로 설정
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            check=True,
            cwd='/MultiTalk'
        )
        
        # 디버깅을 위해 자식 프로세스의 출력을 로깅
        print("--- Subprocess STDOUT ---")
        print(result.stdout)
        print("--- Subprocess STDERR ---")
        print(result.stderr)

        # --- 5. 결과 처리 및 반환 (이전과 동일) ---
        
        if not os.path.exists(output_video_path):
            return {"error": "비디오 파일 생성에 실패했습니다.", "details": result.stderr}
            
        with open(output_video_path, "rb") as video_file:
            video_b64 = base64.b64encode(video_file.read()).decode("utf-8")
        
        return {
            "status": "success",
            "video_base64": video_b64,
            "filename": output_filename
        }

    except subprocess.CalledProcessError as e:
        # 스크립트 실행이 0이 아닌 종료 코드를 반환한 경우 (에러 발생)
        print(f"스크립트 실행 중 에러 발생: {e}")
        return {
            "error": "generate_multitalk.py 스크립트 실행 실패",
            "stdout": e.stdout,
            "stderr": e.stderr
        }
    except Exception as e:
        print(f"핸들러에서 에러 발생: {e}")
        return {"error": str(e)}
        
    finally:
        # 작업 완료 후 임시 폴더 삭제
        if os.path.exists(task_id):
            shutil.rmtree(task_id)

runpod.serverless.start({"handler": handler})