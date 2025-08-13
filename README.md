

# MultiTalk for RunPod Serverless
[한국어 README 보기](README_kr.md)

This project is a template designed to easily deploy and use [MeiGen-AI/MultiTalk](https://github.com/MeiGen-AI/MultiTalk) in the RunPod Serverless environment.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/Multitalk_Runpod_hub)](https://console.runpod.io/hub/wlsdml1114/Multitalk_Runpod_hub)

MultiTalk is an AI model that takes a single portrait image and multilingual speech audio as input to generate natural lip-sync videos in real-time.

## ✨ Key Features

*   **Multilingual Support**: Processes speech in various languages and reflects it in the video.
*   **Real-time Video Generation**: Creates videos synchronized with input audio at high speed.
*   **High-Quality Lip-sync**: Lip movements are precisely synchronized with the input audio.

## 🚀 RunPod Serverless Template

This template includes all the necessary components to run MultiTalk as a RunPod Serverless Worker.

*   **Dockerfile**: Configures the environment and installs all dependencies required for model execution.
*   **handler.py**: Implements the handler function that processes requests for RunPod Serverless.
*   **entrypoint.sh**: Performs initialization tasks when the worker starts.

### Input

The `input` object must contain the following fields. `image_path` and `audio_paths` support **URL, file path, or Base64 encoded string**.

| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `prompt` | `string` | **Yes** | `N/A` | Description text for the video to be generated. |
| `image_path` | `string` | **Yes** | `N/A` | Path, URL, or Base64 string of the portrait image to apply lip-sync to. |
| `audio_paths` | `object` | **Yes** | `N/A` | Map of audio files in the format `{ "person1": "audio_path/URL/Base64" }`, or `{ "person1": "audio_path/URL/Base64", "person2": "audio_path/URL/Base64" }` |


**Request Example:**

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

### Output

#### Success

If the job is successful, it returns a JSON object with the generated video Base64 encoded.

| Parameter | Type | Description |
| --- | --- | --- |
| `status` | `string` | Returns `"success"`. |
| `video_base64` | `string` | Base64 encoded video file data. |
| `filename` | `string` | Name of the generated video file (excluding `.mp4` extension). |

**Success Response Example:**

```json
{
  "status": "success",
  "video_base64": "...",
  "filename": "generated_video"
}
```

#### Error

If the job fails, it returns a JSON object containing an error message.

| Parameter | Type | Description |
| --- | --- | --- |
| `error` | `string` | Description of the error that occurred. |
| `stdout` | `string` | (Optional) Standard output logs generated during script execution. |
| `stderr` | `string` | (Optional) Standard error logs generated during script execution. |

**Error Response Example:**

```json
{
  "error": "Failed to execute generate_multitalk.py script",
  "stdout": "...",
  "stderr": "..."
}
```

## 🛠️ Usage and API Reference

1.  Create a Serverless Endpoint on RunPod based on this repository.
2.  Once the build is complete and the endpoint is active, submit jobs via HTTP POST requests according to the API Reference below.

### 📁 Using Network Volumes

Instead of directly transmitting Base64 encoded files, you can use RunPod's Network Volumes to handle large files. This is especially useful when dealing with large image or audio files.

1.  **Create and Connect Network Volume**: Create a Network Volume (e.g., S3-based volume) from the RunPod dashboard and connect it to your Serverless Endpoint settings.
2.  **Upload Files**: Upload the image and audio files you want to use to the created Network Volume.
3.  **Specify Paths**: When making an API request, specify the file paths within the Network Volume for `image_path` and `audio_paths`. For example, if the volume is mounted at `/my_volume` and you use `portrait.jpg`, the path would be `"/my_volume/portrait.jpg"`.

### Usage Example (Python)

This example is based on the code in `single_examples.ipynb`.

#### 1. Configuration

```python
import os
import requests
import json
import boto3
from botocore.client import Config
import time
import base64

# RunPod Serverless API Information
ENDPOINT_ID = ""    # Replace with your actual serverless endpoint ID
RUN_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run"
RUNPOD_API_ENDPOINT = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run"
RUNPOD_API_KEY = '' # Replace with your actual key

# RunPod Network Volume S3 Information (Check RunPod Dashboard) Adjust to your actual settings
S3_ENDPOINT_URL = 'https://s3api-eu-ro-1.runpod.io/'  # e.g., https://us-east-1.runpod.cloud
S3_ACCESS_KEY_ID = ''
S3_SECRET_ACCESS_KEY = ''
S3_BUCKET_NAME = '' 
S3_REGION = ''

# Local file paths to upload
IMAGE_PATH = ""
AUDIO_PATH = ""

# File names to be uploaded to S3 (can include path)
S3_IMAGE_KEY = f"input/multitalk/{os.path.basename(IMAGE_PATH)}"
S3_AUDIO_KEY = f"input/multitalk/{os.path.basename(AUDIO_PATH)}"
```

#### 2. Upload Files to S3

```python
def upload_to_s3(file_path, bucket, object_name):
    """Uploads the specified file to S3-compatible storage."""
    print(f"Creating S3 client... (Endpoint: {S3_ENDPOINT_URL})")
    s3_client = boto3.client(
        's3',
        endpoint_url=S3_ENDPOINT_URL,
        aws_access_key_id=S3_ACCESS_KEY_ID,
        aws_secret_access_key=S3_SECRET_ACCESS_KEY,
        region_name=S3_REGION,
        config=Config(signature_version='s3v4')
    )
    
    try:
        print(f"Starting upload of '{file_path}' to S3 bucket '{bucket}' as '{object_name}'...")
        s3_client.upload_file(file_path, bucket, object_name)
        print(f"✅ File upload successful: s3://{bucket}/{object_name}")
        return f"/runpod-volume/{object_name}"
    except Exception as e:
        print(f"❌ File upload failed: {e}")
        return None

# Check if files exist
if not all(map(os.path.exists, [IMAGE_PATH, AUDIO_PATH])):
    raise FileNotFoundError("Check input file paths. Files do not exist.")

# Upload each file to S3
image_s3_path = upload_to_s3(IMAGE_PATH, S3_BUCKET_NAME, S3_IMAGE_KEY)
audio_s3_path = upload_to_s3(AUDIO_PATH, S3_BUCKET_NAME, S3_AUDIO_KEY)

if not all([image_s3_path, audio_s3_path]):
    raise RuntimeError("S3 file upload failed, stopping operation.")
```

#### 3. Submit Job Request

```python
# HTTP Request Headers
headers = {
    "Authorization": f"Bearer {RUNPOD_API_KEY}",
    "Content-Type": "application/json"
}

# Data to send to the API (using S3 paths instead of Base64)
# Important: The server's handler code must be modified to expect keys like 'cond_image_s3_path'.
payload = {
    "input": {
        "prompt": "a man talking",
        "image_path": image_s3_path,
        "audio_paths": {
            "person1": audio_s3_path
        }
    }
}

# Send POST request to the API
print(f"\n🚀 Submitting job to RunPod Serverless endpoint [{RUNPOD_API_ENDPOINT}]...")
try:
    response = requests.post(RUNPOD_API_ENDPOINT, headers=headers, json=payload)
    response.raise_for_status()  # Raise an error for bad status codes (4xx or 5xx)

    # Check response
    print("✅ Request successful!")
    print(f"📄 Status Code: {response.status_code}")
    
    response_data = response.json()
    print("\n[RunPod API Response Content]")
    print(json.dumps(response_data, indent=4))
    
    job_id = response_data.get('id')
    print(f"\n✨ Job successfully submitted. Job ID: {job_id}")
    print("You can check the result via the /status endpoint.")

except requests.exceptions.HTTPError as errh:
    print(f"❌ HTTP Error occurred: {errh}")
    print(f"Response content: {errh.response.text}")
except requests.exceptions.RequestException as err:
    print(f"❌ Error during request: {err}")
```

#### 4. Check Result

```python
job_output = None

STATUS_URL = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status"
while True:
    print(f"⏱️ Checking job status... (Job ID: {job_id})")
    status_response = requests.get(f"{STATUS_URL}/{job_id}", headers=headers)
    status_response.raise_for_status()
    
    status_data = status_response.json()
    status = status_data.get('status')
    
    if status == 'COMPLETED':
        print("✅ Job completed!")
        job_output = status_data.get('output')
        break
    elif status == 'FAILED':
        print("❌ Job failed.")
        job_output = status_data.get('error', 'Unknown error')
        break
    elif status in ['IN_QUEUE', 'IN_PROGRESS']:
        print(f"🏃 Job in progress... (Status: {status})")
        time.sleep(5)  # Wait 5 seconds and check again
    else:
        print(f"❓ Unknown status: {status}")
        job_output = status_data
        break

# --- Part 3: Download and Decode Result ---
if job_output and status == 'COMPLETED':
    # You may need to adjust the 'video_b64' key depending on the handler's return value.
    video_b64 = job_output.get('video_base64')
    
    if video_b64:
        print("🎨 Decoding and saving result to file...")
        try:
            decoded_video = base64.b64decode(video_b64)
            output_filename = f"./result_{job_id}.mp4" # change path
            
            with open(output_filename, 'wb') as f:
                f.write(decoded_video)
                
            print(f"✨ Final result saved to '{output_filename}'!")
        except Exception as e:
            print(f"❌ Error decoding or saving result: {e}")
    else:
        print("⚠️ Result (video_b64) not returned. Check handler's return value.")
elif status == 'FAILED':
        print(f"Failure reason: {job_output}")
```



## 🙏 Original Project

This project is based on the following original repository. All rights to the model and core logic belong to the original authors.

*   **MeiGen-AI/MultiTalk:** [https://github.com/MeiGen-AI/MultiTalk](https://github.com/MeiGen-AI/MultiTalk)

## 📄 License

The original MultiTalk project follows the Apache 2.0 License. This template also adheres to that license.
