import runpod
from runpod.serverless.utils import rp_upload
import os
import base64
import binascii # Base64 에러 처리를 위해 import
import json
import uuid
import shutil
import subprocess # subprocess 모듈 추가
import logging
import re

def save_data_if_base64(data_input, temp_dir, output_filename):
    """
    입력 데이터가 URL, Base64 문자열, 또는 파일 경로인지 확인하고,
    URL이면 다운로드, Base64이면 디코딩하여 파일로 저장 후 절대 경로를 반환합니다.
    """
    # 입력값이 문자열이 아니면 그대로 반환
    if not isinstance(data_input, str):
        return data_input

    # URL 형식인지 확인 (http:// 또는 https://로 시작)
    if data_input.startswith('http://') or data_input.startswith('https://'):
        try:
            # 임시 파일명 생성 (원본 파일 확장자 유지 시도)
            # 간단하게 uuid를 사용하거나, url에서 파일명을 파싱할 수 있습니다.
            temp_filename = f"{uuid.uuid4()}_{os.path.basename(data_input)}"
            file_path = os.path.abspath(os.path.join(temp_dir, temp_filename))
            
            # wget을 사용하여 파일 다운로드
            print(f"⬇️ URL에서 파일 다운로드 중: {data_input}")
            subprocess.run(['wget', '-O', file_path, data_input], check=True)
            
            print(f"✅ URL 입력을 '{file_path}' 파일로 저장했습니다.")
            return file_path
        except subprocess.CalledProcessError as e:
            print(f"❌ wget 실행 실패: {e}")
            # 에러 발생 시 None 또는 다른 방식으로 처리 가능
            return None 
        except Exception as e:
            print(f"❌ URL 처리 중 에러 발생: {e}")
            return None

    # Base64 문자열인지 확인
    base64_pattern = re.compile(r'^[A-Za-z0-9+/]*={0,2}$')

    if base64_pattern.fullmatch(data_input):
        print("✅ Base64 형식으로 판단되어 디코딩을 시도합니다.")
        try:
            # 2. 형식이 맞으면 디코딩 시도 (패딩 오류 등을 잡기 위함)
            decoded_data = base64.b64decode(data_input)
            file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
            with open(file_path, 'wb') as f:
                f.write(decoded_data)
            print(f"✅ Base64 입력을 '{file_path}' 파일로 저장했습니다.")
            return file_path
        except (binascii.Error, ValueError) as e:
            # 형식은 맞았으나 패딩 오류 등으로 디코딩 실패 시
            print(f"⚠️ Base64 형식이지만 디코딩에 실패했습니다: {e}. 파일 경로로 처리합니다.")
            return data_input
    else:
        # 1-1. 정규식 검사에서 실패하면 바로 파일 경로로 처리
        print(f"➡️ '{data_input}'은(는) 파일 경로로 처리합니다.")
        return data_input
    # try:
    #     decoded_data = base64.b64decode(data_input)
    #     file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
    #     with open(file_path, 'wb') as f:
    #         f.write(decoded_data)
    #     print(f"✅ Base64 입력을 '{file_path}' 파일로 저장했습니다.")
    #     return file_path

    # except (binascii.Error, ValueError):
    #     # 디코딩 실패 시, 일반 파일 경로로 간주
    #     print(f"➡️ '{data_input}'은(는) 파일 경로로 처리합니다.")
    #     return data_input
    
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
        # image_path = job_input.get("image_path")
        # audio_paths = job_input.get("audio_paths", {})
        # audio_type = job_input.get("audio_type")

        # image_path 처리
        image_input = job_input.get("image_path")
        # 헬퍼 함수를 사용해 이미지 파일 경로 확보 (Base64 또는 Path)
        # 이미지 확장자를 알 수 없으므로 .jpg로 가정하거나, 입력에서 받아야 합니다.
        image_path = save_data_if_base64(image_input, task_id, "input_image.jpg")

        # audio_paths 처리
        audio_inputs = job_input.get("audio_paths", {})
        audio_paths = {} # 최종 파일 경로를 저장할 새 딕셔너리
        for key, audio_data in audio_inputs.items():
            # 각 오디오 파일에 대해 헬퍼 함수 적용
            # 오디오 파일은 확장자가 중요할 수 있으므로 .wav로 가정
            audio_paths[key] = save_data_if_base64(audio_data, task_id, f"input_audio_{key}.wav")

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
        
        input_json_path = os.path.abspath(os.path.join(task_id, "input.json")) # ✨ 핵심 수정 부분
        with open(input_json_path, 'w', encoding='utf-8') as f:
            json.dump(input_data_for_script, f, ensure_ascii=False, indent=4)

        # --- 3. CLI 명령어 리스트 생성 ---
        
        output_filename = "generated_video"
        output_video_path = os.path.abspath(os.path.join(task_id, output_filename))
        

        # 실행할 CLI 명령어를 리스트 형태로 구성합니다.
        # 모든 인자 값은 문자열(string) 형태여야 합니다.
        # 작업 디렉토리를 /MultiTalk로 설정하고 절대 경로 사용
        command = [
            'python', '/InfiniteTalk/generate_infinitetalk.py',
            '--ckpt_dir', '/InfiniteTalk/weights/Wan2.1-I2V-14B-480P',
            '--wav2vec_dir', '/InfiniteTalk/weights/chinese-wav2vec2-base',
            '--input_json', input_json_path,
            '--lora_dir', '/InfiniteTalk/weights/Wan2.1_I2V_14B_FusionX_LoRA.safetensors',
            '--size', 'infinitetalk-480',
            '--sample_text_guide_scale', str(job_input.get("sample_text_guide_scale", 1.0)),
            '--use_teacache', # 플래그 인자는 값 없이 이름만 추가
            '--sample_audio_guide_scale', str(job_input.get("sample_audio_guide_scale", 2.0)),
            '--sample_steps', str(job_input.get("sample_steps", 8)),
            '--mode', job_input.get("mode", "streaming"),
            '--num_persistent_param_in_dit', '0',
            '--motion_frame', '9',
            '--lora_scale', '1.0',
            '--save_file', output_video_path,
            '--sample_shift', '2',
            '--max_frame_num', '10000'
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
            cwd='/InfiniteTalk'
        )
        
        # 디버깅을 위해 자식 프로세스의 출력을 로깅
        print("--- Subprocess STDOUT ---")
        print(result.stdout)
        print("--- Subprocess STDERR ---")
        print(result.stderr)

        # --- 5. 결과 처리 및 반환 (이전과 동일) ---
        real_output_video_path = output_video_path+".mp4"
        if not os.path.exists(real_output_video_path):
            return {"error": "비디오 파일 생성에 실패했습니다.", "details": result.stderr}
            
        with open(real_output_video_path, "rb") as video_file:
            video_b64 = base64.b64encode(video_file.read()).decode("utf-8")
        
        return {
            "status": "success",
            "video_base64": video_b64,
            "filename": output_filename
        }

    except subprocess.CalledProcessError as e:
        # 스크립트 실행이 0이 아닌 종료 코드를 반환한 경우 (에러 발생)
                # 스크립트 실행이 0이 아닌 종료 코드를 반환한 경우 (에러 발생)
        # -----------------------------------------------------
        # ✨ 수정된 부분: 상세 에러 로그를 직접 출력합니다.
        # -----------------------------------------------------
        logger.error("스크립트 실행 중 CalledProcessError 발생!")
        logger.error(f"Return Code: {e.returncode}")
        
        logger.error("--- Subprocess STDOUT ---")
        logger.error(e.stdout) # 캡처된 표준 출력을 로그로 남깁니다.
        
        logger.error("--- Subprocess STDERR ---")
        logger.error(e.stderr) # 캡처된 표준 에러를 로그로 남깁니다.

        print("스크립트 실행 중 CalledProcessError 발생!")
        print(f"Return Code: {e.returncode}")
        
        print("--- Subprocess STDOUT ---")
        print(e.stdout) # 캡처된 표준 출력을 로그로 남깁니다.
        
        print("--- Subprocess STDERR ---")
        print(e.stderr) # 캡처된 표준 에러를 로그로 남깁니다.
        # -----------------------------------------------------

        # API 호출자에게 반환될 응답 (기존과 동일)
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