import runpod
from runpod.serverless.utils import rp_upload
import os
import websocket
import base64
import json
import uuid
import logging
import urllib.request
import urllib.parse
import binascii # Base64 에러 처리를 위해 import
import subprocess
import time
import librosa
# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


server_address = os.getenv('SERVER_ADDRESS', '127.0.0.1')
client_id = str(uuid.uuid4())

def download_file_from_url(url, output_path):
    """URL에서 파일을 다운로드하는 함수"""
    try:
        # wget을 사용하여 파일 다운로드
        result = subprocess.run([
            'wget', '-O', output_path, '--no-verbose', '--timeout=30', url
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            logger.info(f"✅ URL에서 파일을 성공적으로 다운로드했습니다: {url} -> {output_path}")
            return output_path
        else:
            logger.error(f"❌ wget 다운로드 실패: {result.stderr}")
            raise Exception(f"URL 다운로드 실패: {result.stderr}")
    except subprocess.TimeoutExpired:
        logger.error("❌ 다운로드 시간 초과")
        raise Exception("다운로드 시간 초과")
    except Exception as e:
        logger.error(f"❌ 다운로드 중 오류 발생: {e}")
        raise Exception(f"다운로드 중 오류 발생: {e}")

def save_base64_to_file(base64_data, temp_dir, output_filename):
    """Base64 데이터를 파일로 저장하는 함수"""
    try:
        # Base64 문자열 디코딩
        decoded_data = base64.b64decode(base64_data)
        
        # 디렉토리가 존재하지 않으면 생성
        os.makedirs(temp_dir, exist_ok=True)
        
        # 파일로 저장
        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        with open(file_path, 'wb') as f:
            f.write(decoded_data)
        
        logger.info(f"✅ Base64 입력을 '{file_path}' 파일로 저장했습니다.")
        return file_path
    except (binascii.Error, ValueError) as e:
        logger.error(f"❌ Base64 디코딩 실패: {e}")
        raise Exception(f"Base64 디코딩 실패: {e}")

def process_input(input_data, temp_dir, output_filename, input_type):
    """입력 데이터를 처리하여 파일 경로를 반환하는 함수"""
    if input_type == "path":
        # 경로인 경우 그대로 반환
        logger.info(f"📁 경로 입력 처리: {input_data}")
        return input_data
    elif input_type == "url":
        # URL인 경우 다운로드
        logger.info(f"🌐 URL 입력 처리: {input_data}")
        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        return download_file_from_url(input_data, file_path)
    elif input_type == "base64":
        # Base64인 경우 디코딩하여 저장
        logger.info(f"🔢 Base64 입력 처리")
        return save_base64_to_file(input_data, temp_dir, output_filename)
    else:
        raise Exception(f"지원하지 않는 입력 타입: {input_type}")

def queue_prompt(prompt, input_type="image", person_count="single"):
    url = f"http://{server_address}:8188/prompt"
    logger.info(f"Queueing prompt to: {url}")
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode('utf-8')
    
    # 디버깅을 위해 워크플로우 내용 로깅
    logger.info(f"워크플로우 노드 수: {len(prompt)}")
    if input_type == "image":
        logger.info(f"이미지 노드(284) 설정: {prompt.get('284', {}).get('inputs', {}).get('image', 'NOT_FOUND')}")
    else:
        logger.info(f"비디오 노드(228) 설정: {prompt.get('228', {}).get('inputs', {}).get('video', 'NOT_FOUND')}")
    logger.info(f"오디오 노드(125) 설정: {prompt.get('125', {}).get('inputs', {}).get('audio', 'NOT_FOUND')}")
    logger.info(f"텍스트 노드(241) 설정: {prompt.get('241', {}).get('inputs', {}).get('positive_prompt', 'NOT_FOUND')}")
    if person_count == "multi":
        if "307" in prompt:
            logger.info(f"두 번째 오디오 노드(307) 설정: {prompt.get('307', {}).get('inputs', {}).get('audio', 'NOT_FOUND')}")
        elif "313" in prompt:
            logger.info(f"두 번째 오디오 노드(313) 설정: {prompt.get('313', {}).get('inputs', {}).get('audio', 'NOT_FOUND')}")
    
    req = urllib.request.Request(url, data=data)
    req.add_header('Content-Type', 'application/json')
    
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read())
        logger.info(f"프롬프트 전송 성공: {result}")
        return result
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP 에러 발생: {e.code} - {e.reason}")
        logger.error(f"응답 내용: {e.read().decode('utf-8')}")
        raise
    except Exception as e:
        logger.error(f"프롬프트 전송 중 오류: {e}")
        raise

def get_image(filename, subfolder, folder_type):
    url = f"http://{server_address}:8188/view"
    logger.info(f"Getting image from: {url}")
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"{url}?{url_values}") as response:
        return response.read()

def get_history(prompt_id):
    url = f"http://{server_address}:8188/history/{prompt_id}"
    logger.info(f"Getting history from: {url}")
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())

def get_videos(ws, prompt, input_type="image", person_count="single"):
    prompt_id = queue_prompt(prompt, input_type, person_count)['prompt_id']
    output_videos = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message['type'] == 'executing':
                data = message['data']
                if data['node'] is None and data['prompt_id'] == prompt_id:
                    break
        else:
            continue

    history = get_history(prompt_id)[prompt_id]
    for node_id in history['outputs']:
        node_output = history['outputs'][node_id]
        videos_output = []
        if 'gifs' in node_output:
            for video in node_output['gifs']:
                # fullpath를 이용하여 직접 파일을 읽고 base64로 인코딩
                with open(video['fullpath'], 'rb') as f:
                    video_data = base64.b64encode(f.read()).decode('utf-8')
                videos_output.append(video_data)
        output_videos[node_id] = videos_output

    return output_videos

def load_workflow(workflow_path):
    with open(workflow_path, 'r') as file:
        return json.load(file)

def get_workflow_path(input_type, person_count):
    """input_type과 person_count에 따라 적절한 워크플로우 파일 경로를 반환"""
    if input_type == "image":
        if person_count == "single":
            return "/I2V_single.json"
        else:  # multi
            return "/I2V_multi.json"
    else:  # video
        if person_count == "single":
            return "/V2V_single.json"
        else:  # multi
            return "/V2V_multi.json"

def get_audio_duration(audio_path):
    """오디오 파일의 길이(초)를 반환"""
    try:
        duration = librosa.get_duration(path=audio_path)
        return duration
    except Exception as e:
        logger.warning(f"오디오 길이 계산 실패 ({audio_path}): {e}")
        return None

def calculate_max_frames_from_audio(wav_path, wav_path_2=None, fps=25):
    """오디오 길이를 기반으로 max_frames를 계산"""
    durations = []
    
    # 첫 번째 오디오 길이 계산
    duration1 = get_audio_duration(wav_path)
    if duration1 is not None:
        durations.append(duration1)
        logger.info(f"첫 번째 오디오 길이: {duration1:.2f}초")
    
    # 두 번째 오디오 길이 계산 (multi person인 경우)
    if wav_path_2:
        duration2 = get_audio_duration(wav_path_2)
        if duration2 is not None:
            durations.append(duration2)
            logger.info(f"두 번째 오디오 길이: {duration2:.2f}초")
    
    if not durations:
        logger.warning("오디오 길이를 계산할 수 없습니다. 기본값 81을 사용합니다.")
        return 81
    
    # 가장 긴 오디오 길이를 기준으로 max_frames 계산
    max_duration = max(durations)
    max_frames = int(max_duration * fps) + 81
    
    logger.info(f"가장 긴 오디오 길이: {max_duration:.2f}초, 계산된 max_frames: {max_frames}")
    return max_frames

def handler(job):
    job_input = job.get("input", {})

    logger.info(f"Received job input: {job_input}")
    task_id = f"task_{uuid.uuid4()}"

    # 입력 타입과 인물 수 확인
    input_type = job_input.get("input_type", "image")  # "image" 또는 "video"
    person_count = job_input.get("person_count", "single")  # "single" 또는 "multi"
    
    logger.info(f"워크플로우 타입: {input_type}, 인물 수: {person_count}")

    # 워크플로우 파일 경로 결정
    workflow_path = get_workflow_path(input_type, person_count)
    logger.info(f"사용할 워크플로우: {workflow_path}")

    # 이미지/비디오 입력 처리
    media_path = None
    if input_type == "image":
        # 이미지 입력 처리 (image_path, image_url, image_base64 중 하나만 사용)
        if "image_path" in job_input:
            media_path = process_input(job_input["image_path"], task_id, "input_image.jpg", "path")
        elif "image_url" in job_input:
            media_path = process_input(job_input["image_url"], task_id, "input_image.jpg", "url")
        elif "image_base64" in job_input:
            media_path = process_input(job_input["image_base64"], task_id, "input_image.jpg", "base64")
        else:
            # 기본값 사용
            media_path = "/examples/image.jpg"
            logger.info("기본 이미지 파일을 사용합니다: /examples/image.jpg")
    else:  # video
        # 비디오 입력 처리 (video_path, video_url, video_base64 중 하나만 사용)
        if "video_path" in job_input:
            media_path = process_input(job_input["video_path"], task_id, "input_video.mp4", "path")
        elif "video_url" in job_input:
            media_path = process_input(job_input["video_url"], task_id, "input_video.mp4", "url")
        elif "video_base64" in job_input:
            media_path = process_input(job_input["video_base64"], task_id, "input_video.mp4", "base64")
        else:
            # 기본값 사용 (비디오가 없는 경우 기본 이미지 사용)
            media_path = "/examples/image.jpg"
            logger.info("기본 이미지 파일을 사용합니다: /examples/image.jpg")

    # 오디오 입력 처리 (wav_path, wav_url, wav_base64 중 하나만 사용)
    wav_path = None
    wav_path_2 = None  # 다중 인물용 두 번째 오디오
    
    if "wav_path" in job_input:
        wav_path = process_input(job_input["wav_path"], task_id, "input_audio.wav", "path")
    elif "wav_url" in job_input:
        wav_path = process_input(job_input["wav_url"], task_id, "input_audio.wav", "url")
    elif "wav_base64" in job_input:
        wav_path = process_input(job_input["wav_base64"], task_id, "input_audio.wav", "base64")
    else:
        # 기본값 사용
        wav_path = "/examples/audio.mp3"
        logger.info("기본 오디오 파일을 사용합니다: /examples/audio.mp3")
    
    # 다중 인물용 두 번째 오디오 처리
    if person_count == "multi":
        if "wav_path_2" in job_input:
            wav_path_2 = process_input(job_input["wav_path_2"], task_id, "input_audio_2.wav", "path")
        elif "wav_url_2" in job_input:
            wav_path_2 = process_input(job_input["wav_url_2"], task_id, "input_audio_2.wav", "url")
        elif "wav_base64_2" in job_input:
            wav_path_2 = process_input(job_input["wav_base64_2"], task_id, "input_audio_2.wav", "base64")
        else:
            # 기본값 사용 (첫 번째 오디오와 동일)
            wav_path_2 = wav_path
            logger.info("두 번째 오디오가 없어 첫 번째 오디오를 사용합니다.")

    # 필수 필드 검증 및 기본값 설정
    prompt_text = job_input.get("prompt", "A person talking naturally")
    width = job_input.get("width", 512)
    height = job_input.get("height", 512)
    
    # max_frame 설정 (입력이 없으면 오디오 길이 기반으로 자동 계산)
    max_frame = job_input.get("max_frame")
    if max_frame is None:
        logger.info("max_frame이 입력되지 않았습니다. 오디오 길이를 기반으로 자동 계산합니다.")
        max_frame = calculate_max_frames_from_audio(wav_path, wav_path_2 if person_count == "multi" else None)
    else:
        logger.info(f"사용자 지정 max_frame: {max_frame}")
    
    logger.info(f"워크플로우 설정: prompt='{prompt_text}', width={width}, height={height}, max_frame={max_frame}")
    logger.info(f"미디어 경로: {media_path}")
    logger.info(f"오디오 경로: {wav_path}")
    if person_count == "multi":
        logger.info(f"두 번째 오디오 경로: {wav_path_2}")

    prompt = load_workflow(workflow_path)

    # 파일 존재 여부 확인
    if not os.path.exists(media_path):
        logger.error(f"미디어 파일이 존재하지 않습니다: {media_path}")
        return {"error": f"미디어 파일을 찾을 수 없습니다: {media_path}"}
    
    if not os.path.exists(wav_path):
        logger.error(f"오디오 파일이 존재하지 않습니다: {wav_path}")
        return {"error": f"오디오 파일을 찾을 수 없습니다: {wav_path}"}
    
    if person_count == "multi" and wav_path_2 and not os.path.exists(wav_path_2):
        logger.error(f"두 번째 오디오 파일이 존재하지 않습니다: {wav_path_2}")
        return {"error": f"두 번째 오디오 파일을 찾을 수 없습니다: {wav_path_2}"}
    
    logger.info(f"미디어 파일 크기: {os.path.getsize(media_path)} bytes")
    logger.info(f"오디오 파일 크기: {os.path.getsize(wav_path)} bytes")
    if person_count == "multi" and wav_path_2:
        logger.info(f"두 번째 오디오 파일 크기: {os.path.getsize(wav_path_2)} bytes")

    # 워크플로우 노드 설정
    if input_type == "image":
        # I2V 워크플로우: 이미지 입력 설정
        prompt["284"]["inputs"]["image"] = media_path
    else:
        # V2V 워크플로우: 비디오 입력 설정
        prompt["228"]["inputs"]["video"] = media_path
    
    # 공통 설정
    prompt["125"]["inputs"]["audio"] = wav_path
    prompt["241"]["inputs"]["positive_prompt"] = prompt_text
    prompt["245"]["inputs"]["value"] = width
    prompt["246"]["inputs"]["value"] = height
    
    prompt["270"]["inputs"]["value"] = max_frame
    
    # 다중 인물용 두 번째 오디오 설정
    if person_count == "multi":
        # 워크플로우 타입에 따라 두 번째 오디오 노드 설정
        if input_type == "image":  # I2V_multi.json의 경우
            if "307" in prompt:
                prompt["307"]["inputs"]["audio"] = wav_path_2
        else:  # V2V_multi.json의 경우
            if "313" in prompt:
                prompt["313"]["inputs"]["audio"] = wav_path_2

    ws_url = f"ws://{server_address}:8188/ws?clientId={client_id}"
    logger.info(f"Connecting to WebSocket: {ws_url}")
    
    # 먼저 HTTP 연결이 가능한지 확인
    http_url = f"http://{server_address}:8188/"
    logger.info(f"Checking HTTP connection to: {http_url}")
    
    # HTTP 연결 확인 (최대 1분)
    max_http_attempts = 180
    for http_attempt in range(max_http_attempts):
        try:
            import urllib.request
            response = urllib.request.urlopen(http_url, timeout=5)
            logger.info(f"HTTP 연결 성공 (시도 {http_attempt+1})")
            break
        except Exception as e:
            logger.warning(f"HTTP 연결 실패 (시도 {http_attempt+1}/{max_http_attempts}): {e}")
            if http_attempt == max_http_attempts - 1:
                raise Exception("ComfyUI 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
            time.sleep(1)
    
    ws = websocket.WebSocket()
    # 웹소켓 연결 시도 (최대 3분)
    max_attempts = int(180/5)  # 3분 (1초에 한 번씩 시도)
    for attempt in range(max_attempts):
        import time
        try:
            ws.connect(ws_url)
            logger.info(f"웹소켓 연결 성공 (시도 {attempt+1})")
            break
        except Exception as e:
            logger.warning(f"웹소켓 연결 실패 (시도 {attempt+1}/{max_attempts}): {e}")
            if attempt == max_attempts - 1:
                raise Exception("웹소켓 연결 시간 초과 (3분)")
            time.sleep(5)
    videos = get_videos(ws, prompt, input_type, person_count)
    ws.close()

    # 이미지가 없는 경우 처리
    for node_id in videos:
        if videos[node_id]:
            return {"video": videos[node_id][0]}
    
    return {"error": "비디오를를 찾을 수 없습니다."}

runpod.serverless.start({"handler": handler})