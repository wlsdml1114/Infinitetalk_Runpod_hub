# MultiTalk for RunPod Serverless

이 프로젝트는 [MeiGen-AI/MultiTalk](https://github.com/MeiGen-AI/MultiTalk)를 RunPod의 Serverless 환경에 쉽게 배포하고 사용할 수 있도록 만든 템플릿입니다.

MultiTalk는 단일 인물 사진과 다국어 음성 오디오를 입력받아, 실시간으로 자연스러운 립싱크 영상을 생성하는 AI 모델입니다.

## ✨ 주요 기능

*   **다국어 지원**: 다양한 언어의 음성을 처리하여 영상에 반영합니다.
*   **실시간 영상 생성**: 빠른 속도로 입력된 오디오와 동기화된 영상을 만듭니다.
*   **고품질 립싱크**: 입력된 오디오에 맞춰 입술 움직임이 정교하게 동기화됩니다.

## 🚀 RunPod Serverless 템플릿

이 템플릿은 RunPod의 Serverless Worker로 MultiTalk를 실행하기 위해 필요한 모든 구성 요소를 포함하고 있습니다.

*   **Dockerfile**: 모델 실행에 필요한 모든 의존성을 설치하고 환경을 구성합니다.
*   **handler.py**: RunPod Serverless의 요청을 받아 처리하는 핸들러 함수가 구현되어 있습니다.
*   **builder/fetch_models.py**: 빌드 시점에 필요한 AI 모델 파일을 다운로드합니다.
*   **entrypoint.sh**: 워커 시작 시 필요한 초기화 작업을 수행합니다.

## 🛠️ 사용 방법

1.  이 리포지토리를 기반으로 RunPod에 Serverless Endpoint를 생성합니다.
2.  빌드가 완료되고 엔드포인트가 활성화되면, HTTP POST 요청을 통해 작업을 제출합니다.

### API 엔드포인트 (`handler.py`)

#### 입력 (Input)

요청의 `input` 객체는 다음 필드를 포함해야 합니다.

*   `image_url`: 립싱크를 적용할 인물 사진 이미지의 공개 URL
*   `audio_url`: 사용할 음성 파일의 공개 URL

**요청 예시:**

```json
{
  "input": {
    "image_url": "https://path/to/your/portrait.jpg",
    "audio_url": "https://path/to/your/speech.wav"
  }
}
```

#### 출력 (Output)

작업이 성공하면, 생성된 립싱크 비디오 파일의 URL 또는 Base64로 인코딩된 문자열을 반환합니다. (이는 `handler.py`의 최종 구현에 따라 달라질 수 있습니다.)

## 📂 프로젝트 구조

```
.
├── Dockerfile              # 컨테이너 빌드를 위한 Dockerfile
├── entrypoint.sh           # 워커 실행 스크립트
├── handler.py              # Serverless 요청/응답 핸들러
├── builder/
│   └── fetch_models.py     # 모델 다운로드 스크립트
└── ...
```

## 🙏 원본 프로젝트

이 프로젝트는 다음의 원본 저장소를 기반으로 합니다. 모델과 핵심 로직에 대한 모든 권한은 원본 저작자에게 있습니다.

*   **MeiGen-AI/MultiTalk:** [https://github.com/MeiGen-AI/MultiTalk](https://github.com/MeiGen-AI/MultiTalk)

## 📄 라이선스

원본 MultiTalk 프로젝트는 Apache 2.0 라이선스를 따릅니다. 이 템플릿 또한 해당 라이선스를 준수합니다.
