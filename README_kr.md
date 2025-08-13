# MultiTalk for RunPod Serverless

이 프로젝트는 [MeiGen-AI/MultiTalk](https://github.com/MeiGen-AI/MultiTalk)를 RunPod의 Serverless 환경에 쉽게 배포하고 사용할 수 있도록 만든 템플릿입니다.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/Multitalk_Runpod_hub)](https://console.runpod.io/hub/wlsdml1114/Multitalk_Runpod_hub)

MultiTalk는 단일 인물 사진과 다국어 음성 오디오를 입력받아, 실시간으로 자연스러운 립싱크 영상을 생성하는 AI 모델입니다.

## ✨ 주요 기능

*   **다국어 지원**: 다양한 언어의 음성을 처리하여 영상에 반영합니다.
*   **실시간 영상 생성**: 빠른 속도로 입력된 오디오와 동기화된 영상을 만듭니다.
*   **고품질 립싱크**: 입력된 오디오에 맞춰 입술 움직임이 정교하게 동기화됩니다.

## 🚀 RunPod Serverless 템플릿

이 템플릿은 RunPod의 Serverless Worker로 MultiTalk를 실행하기 위해 필요한 모든 구성 요소를 포함하고 있습니다.

*   **Dockerfile**: 모델 실행에 필요한 모든 의존성을 설치하고 환경을 구성합니다.
*   **handler.py**: RunPod Serverless의 요청을 받아 처리하는 핸들러 함수가 구현되어 있습니다.
*   **entrypoint.sh**: 워커 시작 시 필요한 초기화 작업을 수행합니다.

### 입력

`input` 객체는 다음 필드를 포함해야 합니다. `image_path`와 `audio_paths`는 **URL, 파일 경로, 또는 Base64로 인코딩된 문자열**을 모두 지원합니다.

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `prompt` | `string` | **Yes** | `N/A` | 생성될 비디오에 대한 설명 텍스트입니다. |
| `image_path` | `string` | **Yes** | `N/A` | 립싱크를 적용할 인물 사진 이미지의 경로, URL 또는 Base64 문자열입니다. |
| `audio_paths` | `object` | **Yes** | `N/A` | `{ "person1": "오디오 경로/URL/Base64" }`, 또는 `{ "person1": "audio_path/URL/Base64", "person2": "audio_path/URL/Base64" }` 형식의 object 입니다. |

**요청 예시:**

```json
{
  "input": {
    "prompt": "A person is talking in a natural way.",
    "image_path": "https://path/to/your/portrait.jpg",
    "audio_paths": {
      "person1": "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA="
    }
  }
}
```

### 출력 (Output)

#### 성공 (Success)

작업이 성공하면, 생성된 비디오가 Base64로 인코딩된 JSON 객체를 반환합니다.

| 파라미터 | 타입 | 설명 |
| --- | --- | --- |
| `status` | `string` | `"success"`를 반환합니다. |
| `video_base64` | `string` | Base64로 인코딩된 비디오 파일 데이터입니다. |
| `filename` | `string` | 생성된 비디오 파일의 이름입니다. (`.mp4` 확장자 제외) |

**성공 응답 예시:**

```json
{
  "status": "success",
  "video_base64": "...",
  "filename": "generated_video"
}
```

#### 오류 (Error)

작업이 실패하면, 오류 메시지를 포함한 JSON 객체를 반환합니다.

| 파라미터 | 타입 | 설명 |
| --- | --- | --- |
| `error` | `string` | 발생한 오류에 대한 설명입니다. |
| `stdout` | `string` | (선택) 스크립트 실행 중 발생한 표준 출력 로그입니다. |
| `stderr` | `string` | (선택) 스크립트 실행 중 발생한 표준 에러 로그입니다. |

**오류 응답 예시:**

```json
{
  "error": "generate_multitalk.py 스크립트 실행 실패",
  "stdout": "...",
  "stderr": "..."
}
```

## 🛠️ 사용 방법 및 API Reference

1.  이 리포지토리를 기반으로 RunPod에 Serverless Endpoint를 생성합니다.
2.  빌드가 완료되고 엔드포인트가 활성화되면, 아래 API Reference에 따라 HTTP POST 요청을 통해 작업을 제출합니다.

### 📁 네트워크 볼륨 사용하기 (Using Network Volumes)

Base64 인코딩된 파일을 직접 전송하는 대신, RunPod의 네트워크 볼륨(Network Volume)을 사용하여 대용량 파일을 처리할 수 있습니다. 이는 특히 용량이 큰 이미지나 오디오 파일을 다룰 때 유용합니다.

1.  **네트워크 볼륨 생성 및 연결**: RunPod 대시보드에서 네트워크 볼륨(예: S3 기반 볼륨)을 생성하고, 여러분의 Serverless Endpoint 설정에 연결합니다.
2.  **파일 업로드**: 사용할 이미지와 오디오 파일을 생성된 네트워크 볼륨에 업로드합니다.
3.  **경로 지정**: API 요청 시 `image_path`와 `audio_paths`에 네트워크 볼륨 내의 파일 경로를 지정합니다. 예를 들어, 볼륨이 `/my_volume`에 마운트되고 `portrait.jpg` 파일을 사용한다면, 경로는 `"/my_volume/portrait.jpg"`가 됩니다.

### Usage Example (Python)

single_examples.ipynb의 코드를 참고하여 작성되었습니다.

#### 1. 설정

```python
import os
import requests
import json
import boto3
from botocore.client import Config
import time
import base64

# RunPod Serverless API 정보
ENDPOINT_ID = ""    # 실제 serverless endpoint id로 변경해주세요
RUN_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run"
RUNPOD_API_ENDPOINT = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run"
RUNPOD_API_KEY = '' # 실제 키로 교체하세요

# RunPod Network Volume S3 정보 (RunPod 대시보드에서 확인) 실제 세팅에 맞게 변경해주세요 
S3_ENDPOINT_URL = 'https://s3api-eu-ro-1.runpod.io/'  # 예: https://us-east-1.runpod.cloud
S3_ACCESS_KEY_ID = ''
S3_SECRET_ACCESS_KEY = ''
S3_BUCKET_NAME = '' 
S3_REGION = ''

# 업로드할 로컬 파일 경로
IMAGE_PATH = ""
AUDIO_PATH = ""

# S3에 업로드될 파일 이름 (경로 포함 가능)
S3_IMAGE_KEY = f"input/multitalk/{os.path.basename(IMAGE_PATH)}"
S3_AUDIO_KEY = f"input/multitalk/{os.path.basename(AUDIO_PATH)}"
```

#### 2. S3에 파일 업로드

```python
def upload_to_s3(file_path, bucket, object_name):
    """지정된 파일을 S3 호환 스토리지에 업로드합니다."""
    print(f"S3 클라이언트를 생성합니다... (Endpoint: {S3_ENDPOINT_URL})")
    s3_client = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=S3_ACCESS_KEY_ID,
        aws_secret_access_key=S3_SECRET_ACCESS_KEY,
        region_name=S3_REGION,
        config=Config(signature_version='s3v4')
    )
    
    try:
        print(f"'{file_path}' 파일을 S3 버킷 '{bucket}'에 '{object_name}'으로 업로드 시작...")
        s3_client.upload_file(file_path, bucket, object_name)
        print(f"✅ 파일 업로드 성공: s3://{bucket}/{object_name}")
        return f"/runpod-volume/{object_name}"
    except Exception as e:
        print(f"❌ 파일 업로드 실패: {e}")
        return None

# 파일 존재 여부 확인
if not all(map(os.path.exists, [IMAGE_PATH, AUDIO_PATH])):
    raise FileNotFoundError("입력 파일 경로를 확인하세요. 파일이 존재하지 않습니다.")

# 각 파일을 S3에 업로드
image_s3_path = upload_to_s3(IMAGE_PATH, S3_BUCKET_NAME, S3_IMAGE_KEY)
audio_s3_path = upload_to_s3(AUDIO_PATH, S3_BUCKET_NAME, S3_AUDIO_KEY)

if not all([image_s3_path, audio_s3_path]):
    raise RuntimeError("S3 파일 업로드에 실패하여 작업을 중단합니다.")
```

#### 3. 작업 요청

```python
# HTTP 요청 헤더
headers = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json"
}

# API에 전송할 데이터 (Base64 대신 S3 경로 사용)
# 중요: 서버의 핸들러 코드가 'cond_image_s3_path'와 같은 키를 예상하도록 수정해야 합니다.
payload = {
    "input": {
        "prompt": "a man talking",
        "image_path": image_s3_path,
        "audio_paths": {
            "person1": audio_s3_path
        }
    }
}

# API에 POST 요청 보내기
print(f"\n🚀 RunPod Serverless 엔드포인트 [{RUNPOD_API_ENDPOINT}]에 작업을 요청합니다...")
try:
    response = requests.post(RUNPOD_API_ENDPOINT, headers=headers, json=payload)
    response.raise_for_status()  # 2xx가 아니면 오류 발생

    # 응답 확인
    print("✅ 요청 성공!")
    print(f"📄 상태 코드: {response.status_code}")
    
    response_data = response.json()
    print("\n[RunPod API 응답 내용]")
    print(json.dumps(response_data, indent=4))
    
    job_id = response_data.get('id')
    print(f"\n✨ 작업이 성공적으로 제출되었습니다. Job ID: {job_id}")
    print("결과는 /status 엔드포인트를 통해 확인할 수 있습니다.")

except requests.exceptions.HTTPError as errh:
    print(f"❌ HTTP 오류 발생: {errh}")
    print(f"응답 내용: {errh.response.text}")
except requests.exceptions.RequestException as err:
    print(f"❌ 요청 중 오류 발생: {err}")
```

#### 4. 결과 확인

```python
job_output = None

STATUS_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status"
while True:
    print(f"⏱️ 작업 상태를 확인합니다... (Job ID: {job_id})")
    status_response = requests.get(f"{STATUS_URL}/{job_id}", headers=headers)
    status_response.raise_for_status()
    
    status_data = status_response.json()
    status = status_data.get('status')
    
    if status == 'COMPLETED':
        print("✅ 작업이 완료되었습니다!")
        job_output = status_data.get('output')
        break
    elif status == 'FAILED':
        print("❌ 작업이 실패했습니다.")
        job_output = status_data.get('error', '알 수 없는 오류')
        break
    elif status in ['IN_QUEUE', 'IN_PROGRESS']:
        print(f"🏃 작업이 진행 중입니다... (상태: {status})")
        time.sleep(5)  # 5초 대기 후 다시 확인
    else:
        print(f"❓ 알 수 없는 상태입니다: {status}")
        job_output = status_data
        break

# --- Part 3: 결과물 다운로드 및 디코딩 ---
if job_output and status == 'COMPLETED':
    # 핸들러의 반환값에 따라 'video_b64' 키를 적절히 수정해야 할 수 있습니다.
    video_b64 = job_output.get('video_base64')
    
    if video_b64:
        print("🎨 결과물을 디코딩하고 파일로 저장합니다...")
        try:
            decoded_video = base64.b64decode(video_b64)
            output_filename = f"./result_{job_id}.mp4" # 경로 변경경
            
            with open(output_filename, 'wb') as f:
                f.write(decoded_video)
                
            print(f"✨ 최종 결과물이 '{output_filename}' 파일로 저장되었습니다!")
        except Exception as e:
            print(f"❌ 결과물 디코딩 또는 저장 중 오류 발생: {e}")
    else:
        print("⚠️ 결과물(video_b64)이 반환되지 않았습니다. 핸들러의 반환값을 확인하세요.")
elif status == 'FAILED':
        print(f"실패 원인: {job_output}")

```




## 🙏 원본 프로젝트

이 프로젝트는 다음의 원본 저장소를 기반으로 합니다. 모델과 핵심 로직에 대한 모든 권한은 원본 저작자에게 있습니다.

*   **MeiGen-AI/MultiTalk:** [https://github.com/MeiGen-AI/MultiTalk](https://github.com/MeiGen-AI/MultiTalk)

## 📄 라이선스

원본 MultiTalk 프로젝트는 Apache 2.0 라이선스를 따릅니다. 이 템플릿 또한 해당 라이선스를 준수합니다.
