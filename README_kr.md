# InfiniteTalk for RunPod Serverless
[English README](README.md)

이 프로젝트는 [InfiniteTalk](https://github.com/Kijai/InfiniteTalk)을 RunPod Serverless 환경에서 쉽게 배포하고 사용할 수 있도록 설계된 템플릿입니다.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/InfiniteTalk_Runpod_hub)](https://console.runpod.io/hub/wlsdml1114/InfiniteTalk_Runpod_hub)

InfiniteTalk은 단일 인물 이미지와 음성 오디오를 입력으로 받아 무한 대화 기능을 갖춘 자연스러운 립싱크 비디오를 생성하는 AI 모델입니다.

## ✨ 주요 기능

*   **무한 대화**: 지속 시간에 제한 없이 연속적인 대화 비디오를 생성합니다.
*   **고품질 립싱크**: 입술 움직임이 입력 오디오와 정확하게 동기화됩니다.
*   **실시간 비디오 생성**: 입력 오디오와 동기화된 비디오를 고속으로 생성합니다.
*   **ComfyUI 통합**: 유연한 워크플로우 관리를 위해 ComfyUI 기반으로 구축되었습니다.

## 🚀 RunPod Serverless 템플릿

이 템플릿은 InfiniteTalk을 RunPod Serverless Worker로 실행하는 데 필요한 모든 구성 요소를 포함합니다.

*   **Dockerfile**: 모델 실행에 필요한 모든 종속성을 설치하고 환경을 구성합니다.
*   **handler.py**: RunPod Serverless용 요청을 처리하는 핸들러 함수를 구현합니다.
*   **entrypoint.sh**: 워커가 시작될 때 초기화 작업을 수행합니다.
*   **infinitetalk.json**: 단일 인물 대화 워크플로우 구성.
*   **infinitetalk_multi.json**: 다중 인물 대화 워크플로우 구성.

### 입력

`input` 객체는 다음 필드를 포함해야 합니다. 이미지와 오디오는 각각 **경로, URL 또는 Base64** 중 하나의 방식으로 입력할 수 있습니다.

#### 이미지 입력 (다음 중 하나만 사용)
| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `image_path` | `string` | 아니오 | `/examples/image.jpg` | 립싱크를 적용할 인물 이미지의 로컬 경로 |
| `image_url` | `string` | 아니오 | `/examples/image.jpg` | 립싱크를 적용할 인물 이미지의 URL |
| `image_base64` | `string` | 아니오 | `/examples/image.jpg` | 립싱크를 적용할 인물 이미지의 Base64 인코딩된 문자열 |

#### 오디오 입력 (다음 중 하나만 사용)
| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `wav_path` | `string` | 아니오 | `/examples/audio.mp3` | 오디오 파일의 로컬 경로 (WAV/MP3 형식 지원) |
| `wav_url` | `string` | 아니오 | `/examples/audio.mp3` | 오디오 파일의 URL (WAV/MP3 형식 지원) |
| `wav_base64` | `string` | 아니오 | `/examples/audio.mp3` | 오디오 파일의 Base64 인코딩된 문자열 (WAV/MP3 형식 지원) |

#### 기타 필수 매개변수
| 매개변수 | 타입 | 필수 | 기본값 | 설명 |
| --- | --- | --- | --- | --- |
| `prompt` | `string` | **예** | `N/A` | 생성할 비디오에 대한 설명 텍스트 |
| `width` | `integer` | **예** | `N/A` | 출력 비디오의 너비 (픽셀) |
| `height` | `integer` | **예** | `N/A` | 출력 비디오의 높이 (픽셀) |

**요청 예시:**

**경로 사용:**
```json
{
  "input": {
    "prompt": "사람이 자연스럽게 말하는 모습.",
    "image_path": "/my_volume/portrait.jpg",
    "wav_path": "/my_volume/audio.wav",
    "width": 512,
    "height": 512
  }
}
```

**URL 사용:**
```json
{
  "input": {
    "prompt": "사람이 자연스럽게 말하는 모습.",
    "image_url": "https://example.com/portrait.jpg",
    "wav_url": "https://example.com/audio.wav",
    "width": 512,
    "height": 512
  }
}
```

**Base64 사용:**
```json
{
  "input": {
    "prompt": "사람이 자연스럽게 말하는 모습.",
    "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
    "wav_base64": "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=",
    "width": 512,
    "height": 512
  }
}
```

**하이브리드 사용 (이미지는 URL, 오디오는 Base64):**
```json
{
  "input": {
    "prompt": "사람이 자연스럽게 말하는 모습.",
    "image_url": "https://example.com/portrait.jpg",
    "wav_base64": "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=",
    "width": 512,
    "height": 512
  }
}
```

### 출력

#### 성공

작업이 성공하면 생성된 비디오가 Base64로 인코딩된 JSON 객체를 반환합니다.

| 매개변수 | 타입 | 설명 |
| --- | --- | --- |
| `video` | `string` | Base64로 인코딩된 비디오 파일 데이터. |

**성공 응답 예시:**

```json
{
  "video": "data:video/mp4;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
}
```

#### 오류

작업이 실패하면 오류 메시지를 포함한 JSON 객체를 반환합니다.

| 매개변수 | 타입 | 설명 |
| --- | --- | --- |
| `error` | `string` | 발생한 오류에 대한 설명. |

**오류 응답 예시:**

```json
{
  "error": "비디오를 찾을 수 없습니다."
}
```

## 🛠️ 사용법 및 API 참조

1.  이 저장소를 기반으로 RunPod에서 Serverless Endpoint를 생성합니다.
2.  빌드가 완료되고 엔드포인트가 활성화되면 아래 API 참조에 따라 HTTP POST 요청을 통해 작업을 제출합니다.

### 📁 네트워크 볼륨 사용

Base64로 인코딩된 파일을 직접 전송하는 대신 RunPod의 Network Volumes를 사용하여 대용량 파일을 처리할 수 있습니다. 이는 특히 큰 이미지나 오디오 파일을 다룰 때 유용합니다.

1.  **네트워크 볼륨 생성 및 연결**: RunPod 대시보드에서 Network Volume(예: S3 기반 볼륨)을 생성하고 Serverless Endpoint 설정에 연결합니다.
2.  **파일 업로드**: 사용하려는 이미지와 오디오 파일을 생성된 Network Volume에 업로드합니다.
3.  **경로 지정**: API 요청 시 `image_path`와 `wav_path`에 대해 Network Volume 내의 파일 경로를 지정합니다. 예를 들어, 볼륨이 `/my_volume`에 마운트되고 `portrait.jpg`를 사용하는 경우 경로는 `"/my_volume/portrait.jpg"`가 됩니다.


## 🔧 워크플로우 구성

이 템플릿은 두 가지 워크플로우 구성을 포함합니다:

*   **infinitetalk.json**: 단일 인물 대화 워크플로우
*   **infinitetalk_multi.json**: 다중 인물 대화 워크플로우

워크플로우는 ComfyUI 기반이며 InfiniteTalk 처리에 필요한 모든 노드를 포함합니다.

## 🙏 원본 프로젝트

이 프로젝트는 다음 원본 저장소를 기반으로 합니다. 모델과 핵심 로직에 대한 모든 권리는 원본 저자에게 있습니다.

*   **InfiniteTalk:** [https://github.com/Kijai/InfiniteTalk](https://github.com/Kijai/InfiniteTalk)
*   **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
*   **WanVideoWrapper** [https://github.com/kijai/ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)

## 📄 라이선스

원본 InfiniteTalk 프로젝트는 Apache 2.0 라이선스를 따릅니다. 이 템플릿도 해당 라이선스를 준수합니다.
