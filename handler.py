import runpod
import os
import websocket
import base64
import json
import uuid
import logging
import urllib.request
import urllib.parse
import binascii  # Base64 에러 처리를 위해 import
import subprocess
import librosa
import shutil
import mimetypes
import boto3
from botocore.exceptions import NoCredentialsError

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def truncate_base64_for_log(base64_str, max_length=50):
    """Base64 문자열을 로깅용으로 앞부분만 잘라서 반환"""
    if not base64_str:
        return "None"
    if len(base64_str) <= max_length:
        return base64_str
    return f"{base64_str[:max_length]}... (총 {len(base64_str)} 문자)"


server_address = os.getenv("SERVER_ADDRESS", "127.0.0.1")
client_id = str(uuid.uuid4())


def download_file_from_url(url, output_path):
    """URL에서 파일을 다운로드하는 함수"""
    try:
        # wget을 사용하여 파일 다운로드
        result = subprocess.run(
            ["wget", "-O", output_path, "--no-verbose", "--timeout=30", url],
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            logger.info(
                f"✅ URL에서 파일을 성공적으로 다운로드했습니다: {url} -> {output_path}"
            )
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


def detect_file_type(data):
    """바이트 데이터에서 파일 타입 감지"""
    if data.startswith(b'\xff\xd8'):
        return '.jpg'
    if data.startswith(b'\x89PNG\r\n\x1a\n'):
        return '.png'
    if data.startswith(b'RIFF') and data[8:12] == b'WEBP':
        return '.webp'
    if data.startswith(b'RIFF') and data[8:12] == b'WAVE':
        return '.wav'
    if data.startswith(b'ID3') or data.startswith(b'\xff\xfb') or data.startswith(b'\xff\xf3') or data.startswith(b'\xff\xf2'):
        return '.mp3'
    if data.startswith(b'\x00\x00\x00\x18ftypmp42') or data.startswith(b'\x00\x00\x00\x20ftypmp42'):
        return '.mp4'
    if data.startswith(b'\x00\x00\x00\x14ftypm4a') or data.startswith(b'\x00\x00\x00\x20ftypM4A'):
         return '.m4a'
    return None

def save_base64_to_file(base64_data, temp_dir, output_filename):
    """Base64 데이터를 파일로 저장하는 함수"""
    try:
        original_output_filename = output_filename
        # data URI 스킴 처리 (예: data:image/png;base64,...)
        is_data_uri = False
        if ',' in base64_data[:100]: # Heuristic to check for data URI header
            parts = base64_data.split(',', 1)
            if len(parts) == 2:
                header, base64_data_content = parts
                if 'data:' in header and ';base64' in header:
                    is_data_uri = True
                    # 헤더에서 확장자 추출 시도
                    mime_type = header.split(':')[1].split(';')[0]
                    ext = mimetypes.guess_extension(mime_type)
                    if ext:
                        base_name = os.path.splitext(output_filename)[0]
                        # .jpe -> .jpg 변환 처리
                        if ext == '.jpe': ext = '.jpg'
                        output_filename = f"{base_name}{ext}"
                        logger.info(f"Base64 헤더에서 확장자 감지: {ext}")
                    base64_data = base64_data_content # Update base64_data to just the content

        # Base64 문자열 디코딩
        decoded_data = base64.b64decode(base64_data)
        
        # 헤더가 없었거나 헤더에서 확장자를 찾지 못했다면 매직 넘버로 확장자 감지 시도
        if not is_data_uri or output_filename == original_output_filename:
             detected_ext = detect_file_type(decoded_data)
             if detected_ext:
                 base_name = os.path.splitext(output_filename)[0]
                 new_filename = f"{base_name}{detected_ext}"
                 if new_filename != output_filename:
                     logger.info(f"Base64 데이터에서 확장자 감지: {original_output_filename} -> {new_filename}")
                     output_filename = new_filename

        # 디렉토리가 존재하지 않으면 생성
        os.makedirs(temp_dir, exist_ok=True)

        # 파일로 저장
        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        with open(file_path, "wb") as f:
            f.write(decoded_data)

        logger.info(f"✅ Base64 입력을 '{file_path}' 파일로 저장했습니다.")
        return file_path
    except (binascii.Error, ValueError) as e:
        logger.error(f"❌ Base64 디코딩 실패: {e}")
        raise Exception(f"Base64 디코딩 실패: {e}")



def get_extension_from_url(url):
    """URL에서 파일 확장자를 감지하는 함수"""
    try:
        # 1. URL 경로에서 확장자 추출 시도
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.mp3', '.wav', '.m4a', '.mp4']:
            return ext
        
        # 2. 헤더에서 Content-Type 확인 (HEAD 요청)
        req = urllib.request.Request(url, method='HEAD')
        req.add_header('User-Agent', 'Mozilla/5.0')
        with urllib.request.urlopen(req, timeout=5) as response:
            content_type = response.info().get_content_type()
            ext = mimetypes.guess_extension(content_type)
            if ext == '.jpe': 
                return '.jpg'
            if ext: 
                return ext
            
    except Exception as e:
        logger.warning(f"확장자 감지 실패: {e}")
    
    return None


def process_input(input_data, temp_dir, output_filename, input_type):
    """입력 데이터를 처리하여 파일 경로를 반환하는 함수"""
    if input_type == "path":
        # 경로인 경우 그대로 반환
        logger.info(f"📁 경로 입력 처리: {input_data}")
        return input_data
    elif input_type == "url":
        # URL인 경우 다운로드
        logger.info(f"🌐 URL 입력 처리: {input_data}")
        
        # 확장자 감지 및 적용
        detected_ext = get_extension_from_url(input_data)
        if detected_ext:
            base_name = os.path.splitext(output_filename)[0]
            new_filename = f"{base_name}{detected_ext}"
            if new_filename != output_filename:
                logger.info(f"감지된 확장자 적용: {output_filename} -> {new_filename}")
                output_filename = new_filename

        os.makedirs(temp_dir, exist_ok=True)
        file_path = os.path.abspath(os.path.join(temp_dir, output_filename))
        return download_file_from_url(input_data, file_path)
    elif input_type == "base64":
        # Base64인 경우 디코딩하여 저장
        logger.info(f"🔢 Base64 입력 처리")
        return save_base64_to_file(input_data, temp_dir, output_filename)
    else:
        raise Exception(f"지원하지 않는 입력 타입: {input_type}")


def queue_prompt(prompt):
    url = f"http://{server_address}:8188/prompt"
    logger.info(f"Queueing prompt to: {url}")
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode("utf-8")

    # 디버깅을 위해 워크플로우 내용 로깅
    logger.info(f"워크플로우 노드 수: {len(prompt)}")
    logger.info(
        f"이미지 노드(284) 설정: {prompt.get('284', {}).get('inputs', {}).get('image', 'NOT_FOUND')}"
    )
    logger.info(
        f"오디오 노드(125) 설정: {prompt.get('125', {}).get('inputs', {}).get('audio', 'NOT_FOUND')}"
    )
    logger.info(
        f"텍스트 노드(241) 설정: {prompt.get('241', {}).get('inputs', {}).get('positive_prompt', 'NOT_FOUND')}"
    )

    req = urllib.request.Request(url, data=data)
    req.add_header("Content-Type", "application/json")

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


def get_videos(ws, prompt):
    prompt_id = queue_prompt(prompt)["prompt_id"]
    logger.info(f"워크플로우 실행 시작: prompt_id={prompt_id}")

    output_videos = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message["type"] == "executing":
                data = message["data"]
                if data["node"] is not None:
                    logger.info(f"노드 실행 중: {data['node']}")
                if data["node"] is None and data["prompt_id"] == prompt_id:
                    logger.info("워크플로우 실행 완료")
                    break
        else:
            continue

    logger.info(f"히스토리 조회 중: prompt_id={prompt_id}")
    history = get_history(prompt_id)[prompt_id]
    logger.info(f"출력 노드 수: {len(history['outputs'])}")

    for node_id in history["outputs"]:
        node_output = history["outputs"][node_id]
        videos_output = []
        if "gifs" in node_output:
            logger.info(
                f"노드 {node_id}에서 {len(node_output['gifs'])}개의 비디오 발견"
            )
            for idx, video in enumerate(node_output["gifs"]):
                # fullpath를 그대로 반환 (base64 인코딩하지 않음)
                video_path = video["fullpath"]
                logger.info(f"비디오 파일 경로: {video_path}")

                # 파일 존재 여부 및 크기 확인
                if os.path.exists(video_path):
                    file_size = os.path.getsize(video_path)
                    logger.info(
                        f"비디오 {idx+1} 발견: {video_path} (크기: {file_size} bytes)"
                    )
                else:
                    logger.warning(f"비디오 파일이 존재하지 않습니다: {video_path}")

                videos_output.append(video_path)
        else:
            logger.info(f"노드 {node_id}에 비디오 출력 없음")
        output_videos[node_id] = videos_output

    logger.info(f"총 {len(output_videos)}개 노드에서 비디오 파일 경로 수집 완료")
    return output_videos


def load_workflow(workflow_path):
    with open(workflow_path, "r") as file:
        return json.load(file)


def get_workflow_path():
    """워크플로우 파일 경로를 반환"""
    return "workflow/i2v.json"


def get_audio_duration(audio_path):
    """오디오 파일의 길이(초)를 반환"""
    try:
        duration = librosa.get_duration(path=audio_path)
        return duration
    except Exception as e:
        logger.warning(f"오디오 길이 계산 실패 ({audio_path}): {e}")
        return None


def calculate_max_frames_from_audio(wav_path, fps=25):
    """오디오 길이를 기반으로 max_frames를 계산"""
    # 오디오 길이 계산
    duration = get_audio_duration(wav_path)
    if duration is None:
        logger.warning("오디오 길이를 계산할 수 없습니다. 기본값 81을 사용합니다.")
        return 81

    # 오디오 길이를 기준으로 max_frames 계산
    max_frames = int(duration * fps) + 81

    logger.info(
        f"오디오 길이: {duration:.2f}초, 계산된 max_frames: {max_frames}"
    )
    return max_frames


def upload_to_r2(video_data, file_name):
    """
    비디오 데이터를 Cloudflare R2에 업로드하고 URL을 반환합니다.
    환경변수 R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, R2_BUCKET_NAME이 필요합니다.
    """
    try:
        account_id = os.environ.get('R2_ACCOUNT_ID')
        access_key = os.environ.get('R2_ACCESS_KEY_ID')
        secret_key = os.environ.get('R2_SECRET_ACCESS_KEY')
        bucket_name = os.environ.get('R2_BUCKET_NAME')
        custom_domain = os.environ.get('R2_CUSTOM_DOMAIN')

        if not all([account_id, access_key, secret_key, bucket_name]):
            logger.error("R2 업로드를 위한 환경변수가 설정되지 않았습니다.")
            return None

        s3_client = boto3.client(
            's3',
            endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key
        )

        # Base64 디코딩 (이미 바이트로 넘어오면 그대로 사용)
        if isinstance(video_data, str):
            try:
                video_bytes = base64.b64decode(video_data)
            except binascii.Error:
                video_bytes = video_data.encode('utf-8')
        else:
            video_bytes = video_data

        s3_client.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=video_bytes,
            ContentType='video/mp4'
        )
        
        if custom_domain:
            url = f"{custom_domain}/{file_name}"
            # http/https prefix check
            if not url.startswith("http"):
                 url = f"https://{url}"
            logger.info(f"✅ R2 업로드 성공 (Public URL): {url}")
            return url
        else:
            # Custom Domain이 없는 경우 Presigned URL 생성 (1시간 유효)
            try:
                url = s3_client.generate_presigned_url(
                    ClientMethod='get_object',
                    Params={'Bucket': bucket_name, 'Key': file_name},
                    ExpiresIn=3600
                )
                logger.info(f"✅ R2 업로드 성공 (Presigned URL): {url}")
                return url
            except Exception as e:
                logger.error(f"❌ Presigned URL 생성 실패: {e}")
                return None

    except Exception as e:
        logger.error(f"❌ R2 업로드 중 오류 발생: {e}")
        return None


def handler(job):
    job_input = job.get("input", {})

    # job_input을 로깅할 때 base64 데이터는 truncate해서 출력
    log_input = job_input.copy()
    for key in ["image_base64", "video_base64", "wav_base64"]:
        if key in log_input:
            log_input[key] = truncate_base64_for_log(log_input[key])

    logger.info(f"Received job input: {log_input}")
    task_id = f"task_{uuid.uuid4()}"

    # 워크플로우 파일 경로 결정
    workflow_path = get_workflow_path()
    logger.info(f"사용할 워크플로우: {workflow_path}")

    # 이미지 입력 처리 (image_path, image_url, image_base64 중 하나만 사용)
    media_path = None
    if "image_path" in job_input:
        media_path = process_input(
            job_input["image_path"], task_id, "input_image.jpg", "path"
        )
    elif "image_url" in job_input:
        media_path = process_input(
            job_input["image_url"], task_id, "input_image.jpg", "url"
        )
    elif "image_base64" in job_input:
        media_path = process_input(
            job_input["image_base64"], task_id, "input_image.jpg", "base64"
        )
    else:
        # 기본값 사용
        media_path = "/examples/image.jpg"
        logger.info("기본 이미지 파일을 사용합니다: /examples/image.jpg")

    # 오디오 입력 처리 (wav_path, wav_url, wav_base64 중 하나만 사용)
    wav_path = None
    if "wav_path" in job_input:
        wav_path = process_input(
            job_input["wav_path"], task_id, "input_audio.wav", "path"
        )
    elif "wav_url" in job_input:
        wav_path = process_input(
            job_input["wav_url"], task_id, "input_audio.wav", "url"
        )
    elif "wav_base64" in job_input:
        wav_path = process_input(
            job_input["wav_base64"], task_id, "input_audio.wav", "base64"
        )
    else:
        # 기본값 사용
        wav_path = "/examples/audio.mp3"
        logger.info("기본 오디오 파일을 사용합니다: /examples/audio.mp3")

    # 필수 필드 검증 및 기본값 설정
    prompt_text = job_input.get("prompt", "A person talking naturally")
    width = job_input.get("width", 512)
    height = job_input.get("height", 512)

    # max_frame 설정 (입력이 없으면 오디오 길이 기반으로 자동 계산)
    max_frame = job_input.get("max_frame")
    if max_frame is None:
        logger.info(
            "max_frame이 입력되지 않았습니다. 오디오 길이를 기반으로 자동 계산합니다."
        )
        max_frame = calculate_max_frames_from_audio(wav_path)
    else:
        logger.info(f"사용자 지정 max_frame: {max_frame}")

    logger.info(
        f"워크플로우 설정: prompt='{prompt_text}', width={width}, height={height}, max_frame={max_frame}"
    )
    logger.info(f"미디어 경로: {media_path}")
    logger.info(f"오디오 경로: {wav_path}")


    prompt = load_workflow(workflow_path)

    # ------------------------------------------------------------------
    # 동적 Force Offload 설정
    # ------------------------------------------------------------------
    # 1. 입력에서 force_offload 읽기 (기본값 True: 작은 GPU에서 OOM 방지)
    force_offload = job_input.get("force_offload", True)
    logger.info(f"🔧 설정: force_offload={force_offload}")

    # 2. WanVideoSampler 노드에 force_offload 파라미터 주입
    sampler_nodes = []
    
    # 모든 WanVideoSampler 노드 찾기
    for node_id, node_data in prompt.items():
        if node_data.get("class_type") in ["WanVideoSampler", "WanVideoSamplerv2"]:
            sampler_nodes.append(node_id)

    if sampler_nodes:
        for node_id in sampler_nodes:
            inputs = prompt[node_id].setdefault("inputs", {})
            inputs["force_offload"] = force_offload
            logger.info(f"✅ 노드 {node_id} ({prompt[node_id].get('class_type')}) 업데이트됨: force_offload={force_offload}")
    else:
        logger.warning("⚠️ 경고: WanVideoSampler 노드를 찾을 수 없습니다. 워크플로우 기본값을 사용합니다.")
    # ------------------------------------------------------------------

    # 파일 존재 여부 확인
    if not os.path.exists(media_path):
        logger.error(f"미디어 파일이 존재하지 않습니다: {media_path}")
        return {"error": f"미디어 파일을 찾을 수 없습니다: {media_path}"}

    if not os.path.exists(wav_path):
        logger.error(f"오디오 파일이 존재하지 않습니다: {wav_path}")
        return {"error": f"오디오 파일을 찾을 수 없습니다: {wav_path}"}



    logger.info(f"미디어 파일 크기: {os.path.getsize(media_path)} bytes")
    logger.info(f"오디오 파일 크기: {os.path.getsize(wav_path)} bytes")


    # 워크플로우 노드 설정
    prompt["284"]["inputs"]["image"] = media_path

    # 공통 설정
    prompt["125"]["inputs"]["audio"] = wav_path
    prompt["241"]["inputs"]["positive_prompt"] = prompt_text
    prompt["245"]["inputs"]["value"] = width
    prompt["246"]["inputs"]["value"] = height

    prompt["270"]["inputs"]["value"] = max_frame

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
            logger.warning(
                f"HTTP 연결 실패 (시도 {http_attempt+1}/{max_http_attempts}): {e}"
            )
            if http_attempt == max_http_attempts - 1:
                raise Exception(
                    "ComfyUI 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요."
                )
            time.sleep(1)

    ws = websocket.WebSocket()
    # 웹소켓 연결 시도 (최대 3분)
    max_attempts = int(180 / 5)  # 3분 (1초에 한 번씩 시도)
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
    videos = get_videos(ws, prompt)
    ws.close()
    logger.info("웹소켓 연결 종료")

    # 비디오가 없는 경우 처리
    output_video_path = None
    logger.info("출력 비디오 검색 중...")

    for node_id in videos:
        if videos[node_id]:
            output_video_path = videos[node_id][0]
            logger.info(f"노드 {node_id}에서 출력 비디오 발견: {output_video_path}")
            break
        else:
            logger.info(f"노드 {node_id}는 비어있음")

    if not output_video_path:
        logger.error("출력 비디오를 찾을 수 없습니다. 모든 노드가 비어있습니다.")
        return {"error": "비디오를 찾을 수 없습니다."}

    # 비디오 파일 존재 여부 확인
    if not os.path.exists(output_video_path):
        logger.error(f"출력 비디오 파일이 존재하지 않습니다: {output_video_path}")
        return {"error": f"비디오 파일을 찾을 수 없습니다: {output_video_path}"}

    # network_volume 파라미터 확인
    use_network_volume = job_input.get("network_volume", False)
    logger.info(f"네트워크 볼륨 사용 여부: {use_network_volume}")

    if use_network_volume:
        # 네트워크 볼륨 사용: 파일 복사
        logger.info("네트워크 볼륨에 비디오 복사 시작")
        try:
            # 결과 비디오 파일 경로 생성
            output_filename = f"infinitetalk_{task_id}.mp4"
            output_path = f"/runpod-volume/{output_filename}"
            logger.info(f"원본 파일: {output_video_path}")
            logger.info(f"대상 경로: {output_path}")

            # 원본 파일 크기 확인
            source_file_size = os.path.getsize(output_video_path)
            logger.info(f"원본 파일 크기: {source_file_size} bytes")

            # 파일 복사 (shutil.copy2는 메타데이터도 함께 복사)
            shutil.copy2(output_video_path, output_path)
            logger.info("파일 복사 완료")

            # 복사된 파일 크기 확인
            copied_file_size = os.path.getsize(output_path)
            logger.info(f"복사된 파일 크기: {copied_file_size} bytes")

            if source_file_size == copied_file_size:
                logger.info(
                    f"✅ 결과 비디오를 '{output_path}'에 성공적으로 복사했습니다"
                )
            else:
                logger.warning(
                    f"⚠️ 파일 크기가 일치하지 않습니다: 원본={source_file_size}, 복사본={copied_file_size}"
                )

            return {"video_path": output_path}

        except Exception as e:
            logger.error(f"❌ 비디오 복사 실패: {e}")
            return {"error": f"비디오 복사 실패: {e}"}

    elif job_input.get("return_url", False):
        # R2 업로드: Base64 인코딩 대신 R2에 업로드하고 URL 반환
        logger.info("R2 업로드 시작")
        logger.info(f"비디오 파일 경로: {output_video_path}")

        try:
            # 파일 읽기
            with open(output_video_path, "rb") as f:
                video_bytes = f.read()

            file_name = f"{task_id}.mp4"
            video_url = upload_to_r2(video_bytes, file_name)

            if video_url:
                return {"video_url": video_url}
            else:
                logger.warning("R2 업로드 실패, Base64 비디오를 반환합니다.")
                # 업로드 실패 시 아래 Base64 반환 로직으로 진행 (fall-through)
        except Exception as e:
             logger.error(f"❌ R2 업로드 실패: {e}")
             # 에러 발생 시 아래 Base64 반환 로직으로 진행

    # 네트워크 볼륨 미사용 및 R2 업로드 미사용/실패: Base64 인코딩하여 반환
    logger.info("Base64 인코딩 시작")
    logger.info(f"비디오 파일 경로: {output_video_path}")

    try:
        # 파일 크기 확인
        file_size = os.path.getsize(output_video_path)
        logger.info(f"원본 파일 크기: {file_size} bytes")

        # 파일을 읽어 base64 인코딩
        with open(output_video_path, "rb") as f:
            video_data = base64.b64encode(f.read()).decode("utf-8")

        encoded_size = len(video_data)
        logger.info(f"Base64 인코딩 완료: {encoded_size} 문자")
        logger.info(
            f"✅ Base64 인코딩된 비디오 반환: {truncate_base64_for_log(video_data)}"
        )
        return {"video": video_data}

    except Exception as e:
        logger.error(f"❌ Base64 인코딩 실패: {e}")
        return {"error": f"Base64 인코딩 실패: {e}"}


runpod.serverless.start({"handler": handler})
