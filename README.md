# InfiniteTalk for RunPod Serverless
[한국어 README 보기](README_kr.md)

This project is a template designed to easily deploy and use [InfiniteTalk](https://github.com/Kijai/InfiniteTalk) in the RunPod Serverless environment.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/InfiniteTalk_Runpod_hub)](https://console.runpod.io/hub/wlsdml1114/InfiniteTalk_Runpod_hub)

InfiniteTalk is an AI model that takes a single portrait image and speech audio as input to generate natural lip-sync videos with infinite talking capabilities.

## ✨ Key Features

*   **Infinite Talking**: Generates continuous talking videos without limitations on duration.
*   **High-Quality Lip-sync**: Lip movements are precisely synchronized with the input audio.
*   **Real-time Video Generation**: Creates videos synchronized with input audio at high speed.
*   **ComfyUI Integration**: Built on top of ComfyUI for flexible workflow management.

## 🚀 RunPod Serverless Template

This template includes all the necessary components to run InfiniteTalk as a RunPod Serverless Worker.

*   **Dockerfile**: Configures the environment and installs all dependencies required for model execution.
*   **handler.py**: Implements the handler function that processes requests for RunPod Serverless.
*   **entrypoint.sh**: Performs initialization tasks when the worker starts.
*   **infinitetalk.json**: Single-person workflow configuration.
*   **infinitetalk_multi.json**: Multi-person workflow configuration.

### Input

The `input` object must contain the following fields. `image_path` and `wav_path` support **URL, file path, or Base64 encoded string**.

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `prompt` | `string` | **Yes** | `N/A` | Description text for the video to be generated. |
| `image_path` | `string` | **Yes** | `N/A` | Path, URL, or Base64 string of the portrait image to apply lip-sync to. |
| `wav_path` | `string` | **Yes** | `N/A` | Path, URL, or Base64 string of the audio file (WAV format recommended). |
| `width` | `integer` | **Yes** | `N/A` | Width of the output video in pixels. |
| `height` | `integer` | **Yes** | `N/A` | Height of the output video in pixels. |

**Request Example:**

```json
{
  "input": {
    "prompt": "A person is talking in a natural way.",
    "image_path": "https://path/to/your/portrait.jpg",
    "wav_path": "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=",
    "width": 512,
    "height": 512
  }
}
```

### Output

#### Success

If the job is successful, it returns a JSON object with the generated video Base64 encoded.

| Parameter | Type | Description |
| --- | --- | --- |
| `video` | `string` | Base64 encoded video file data. |

**Success Response Example:**

```json
{
  "video": "data:video/mp4;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
}
```

#### Error

If the job fails, it returns a JSON object containing an error message.

| Parameter | Type | Description |
| --- | --- | --- |
| `error` | `string` | Description of the error that occurred. |

**Error Response Example:**

```json
{
  "error": "비디오를 찾을 수 없습니다."
}
```

## 🛠️ Usage and API Reference

1.  Create a Serverless Endpoint on RunPod based on this repository.
2.  Once the build is complete and the endpoint is active, submit jobs via HTTP POST requests according to the API Reference below.

### 📁 Using Network Volumes

Instead of directly transmitting Base64 encoded files, you can use RunPod's Network Volumes to handle large files. This is especially useful when dealing with large image or audio files.

1.  **Create and Connect Network Volume**: Create a Network Volume (e.g., S3-based volume) from the RunPod dashboard and connect it to your Serverless Endpoint settings.
2.  **Upload Files**: Upload the image and audio files you want to use to the created Network Volume.
3.  **Specify Paths**: When making an API request, specify the file paths within the Network Volume for `image_path` and `wav_path`. For example, if the volume is mounted at `/my_volume` and you use `portrait.jpg`, the path would be `"/my_volume/portrait.jpg"`.

## 🔧 Workflow Configuration

This template includes two workflow configurations:

*   **infinitetalk.json**: Single-person talking workflow
*   **infinitetalk_multi.json**: Multi-person talking workflow

The workflows are based on ComfyUI and include all necessary nodes for InfiniteTalk processing.

## 🙏 Original Project

This project is based on the following original repository. All rights to the model and core logic belong to the original authors.

*   **InfiniteTalk:** [https://github.com/MeiGen-AI/InfiniteTalk](https://github.com/MeiGen-AI/InfiniteTalk)
*   **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
*   **WanVideoWrapper** [https://github.com/kijai/ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)

## 📄 License

The original InfiniteTalk project follows the Apache 2.0 License. This template also adheres to that license.
