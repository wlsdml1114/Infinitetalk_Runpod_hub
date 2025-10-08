#!/usr/bin/env python3
"""
Infinitetalk API client with S3 upload functionality
Complete client that uploads files using RunPod Network Volume S3 and calls infinitetalk API
"""

import os
import requests
import json
import boto3
from botocore.client import Config
import time
import base64
from typing import Optional, Dict, Any, List, Union
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InfinitetalkS3Client:
    def __init__(
        self,
        runpod_endpoint_id: str,
        runpod_api_key: str,
        s3_endpoint_url: str,
        s3_access_key_id: str,
        s3_secret_access_key: str,
        s3_bucket_name: str,
        s3_region: str = 'eu-ro-1'
    ):
        """
        Initialize Infinitetalk S3 client
        
        Args:
            runpod_endpoint_id: RunPod endpoint ID
            runpod_api_key: RunPod API key
            s3_endpoint_url: S3 endpoint URL
            s3_access_key_id: S3 access key ID
            s3_secret_access_key: S3 secret access key
            s3_bucket_name: S3 bucket name
            s3_region: S3 region
        """
        self.runpod_endpoint_id = runpod_endpoint_id
        self.runpod_api_key = runpod_api_key
        self.runpod_api_endpoint = f"https://api.runpod.ai/v2/{runpod_endpoint_id}/run"
        self.status_url = f"https://api.runpod.ai/v2/{runpod_endpoint_id}/status"
        
        # S3 configuration
        self.s3_endpoint_url = s3_endpoint_url
        self.s3_access_key_id = s3_access_key_id
        self.s3_secret_access_key = s3_secret_access_key
        self.s3_bucket_name = s3_bucket_name
        self.s3_region = s3_region
        
        # Initialize S3 client
        self.s3_client = boto3.client(
            's3',
            endpoint_url=s3_endpoint_url,
            aws_access_key_id=s3_access_key_id,
            aws_secret_access_key=s3_secret_access_key,
            region_name=s3_region,
            config=Config(signature_version='s3v4')
        )
        
        # Initialize HTTP session
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {runpod_api_key}',
            'Content-Type': 'application/json'
        })
        
        logger.info(f"InfinitetalkS3Client initialized - Endpoint: {runpod_endpoint_id}")
    
    def upload_to_s3(self, file_path: str, s3_key: str) -> Optional[str]:
        """
        Upload file to S3
        
        Args:
            file_path: Local path of file to upload
            s3_key: Key (path) to store in S3
        
        Returns:
            S3 path or None (on failure)
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"File does not exist: {file_path}")
                return None
            
            logger.info(f"S3 upload started: {file_path} -> s3://{self.s3_bucket_name}/{s3_key}")
            
            self.s3_client.upload_file(file_path, self.s3_bucket_name, s3_key)
            
            s3_path = f"/runpod-volume/{s3_key}"
            logger.info(f"✅ S3 upload successful: {s3_path}")
            return s3_path
            
        except Exception as e:
            logger.error(f"❌ S3 upload failed: {e}")
            return None
    
    def upload_multiple_files(self, file_paths: List[str], s3_keys: List[str]) -> Dict[str, Optional[str]]:
        """
        Upload multiple files to S3
        
        Args:
            file_paths: List of local paths of files to upload
            s3_keys: List of keys to store in S3
        
        Returns:
            Dictionary with filename as key and S3 path as value
        """
        results = {}
        
        for file_path, s3_key in zip(file_paths, s3_keys):
            filename = os.path.basename(file_path)
            s3_path = self.upload_to_s3(file_path, s3_key)
            results[filename] = s3_path
        
        return results
    
    def submit_job(self, input_data: Dict[str, Any]) -> Optional[str]:
        """
        Submit job to RunPod
        
        Args:
            input_data: API input data
        
        Returns:
            Job ID or None (on failure)
        """
        payload = {"input": input_data}
        
        try:
            logger.info(f"Submitting job to RunPod: {self.runpod_api_endpoint}")
            logger.info(f"Input data: {json.dumps(input_data, indent=2, ensure_ascii=False)}")
            
            response = self.session.post(self.runpod_api_endpoint, json=payload, timeout=30)
            response.raise_for_status()
            
            response_data = response.json()
            job_id = response_data.get('id')
            
            if job_id:
                logger.info(f"✅ Job submission successful! Job ID: {job_id}")
                return job_id
            else:
                logger.error(f"❌ Failed to receive Job ID: {response_data}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Job submission failed: {e}")
            return None
    
    def wait_for_completion(self, job_id: str, check_interval: int = 10, max_wait_time: int = 1800) -> Dict[str, Any]:
        """
        Wait for job completion
        
        Args:
            job_id: Job ID
            check_interval: Status check interval (seconds)
            max_wait_time: Maximum wait time (seconds)
        
        Returns:
            Job result dictionary
        """
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            try:
                logger.info(f"⏱️ Checking job status... (Job ID: {job_id})")
                
                response = self.session.get(f"{self.status_url}/{job_id}", timeout=30)
                response.raise_for_status()
                
                status_data = response.json()
                status = status_data.get('status')
                
                if status == 'COMPLETED':
                    logger.info("✅ Job completed!")
                    return {
                        'status': 'COMPLETED',
                        'output': status_data.get('output'),
                        'job_id': job_id
                    }
                elif status == 'FAILED':
                    logger.error("❌ Job failed.")
                    return {
                        'status': 'FAILED',
                        'error': status_data.get('error', 'Unknown error'),
                        'job_id': job_id
                    }
                elif status in ['IN_QUEUE', 'IN_PROGRESS']:
                    logger.info(f"🏃 Job in progress... (status: {status})")
                    time.sleep(check_interval)
                else:
                    logger.warning(f"❓ Unknown status: {status}")
                    return {
                        'status': 'UNKNOWN',
                        'data': status_data,
                        'job_id': job_id
                    }
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Error checking status: {e}")
                time.sleep(check_interval)
        
        logger.error(f"❌ Job wait timeout ({max_wait_time} seconds)")
        return {
            'status': 'TIMEOUT',
            'job_id': job_id
        }
    
    def save_video_result(self, result: Dict[str, Any], output_path: str) -> bool:
        """
        Save video file from job result
        
        Args:
            result: Job result dictionary
            output_path: File path to save
        
        Returns:
            Save success status
        """
        try:
            if result.get('status') != 'COMPLETED':
                logger.error(f"Job not completed: {result.get('status')}")
                return False
            
            output = result.get('output', {})
            video_b64 = output.get('video_base64') or output.get('video')
            
            if not video_b64:
                logger.error("No video data available")
                return False
            
            # Create directory
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Decode and save video
            decoded_video = base64.b64decode(video_b64)
            
            with open(output_path, 'wb') as f:
                f.write(decoded_video)
            
            file_size = os.path.getsize(output_path)
            logger.info(f"✅ Video saved successfully: {output_path} ({file_size / (1024*1024):.1f}MB)")
            return True
            
        except Exception as e:
            logger.error(f"❌ Video save failed: {e}")
            return False
    
    def create_video_from_files(
        self,
        image_path: str,
        audio_path: str,
        audio_path_2: Optional[str] = None,
        prompt: str = "A person talking naturally",
        width: int = 512,
        height: int = 512,
        max_frame: Optional[int] = None,
        person_count: str = "single",
        input_type: str = "image"
    ) -> Dict[str, Any]:
        """
        Create video from local files (including S3 upload)
        
        Args:
            image_path: Image file path
            audio_path: Audio file path
            audio_path_2: Second audio file path (for multiple people)
            prompt: Prompt text
            width: Output width
            height: Output height
            max_frame: Maximum frame count
            person_count: Number of people ("single" or "multi")
            input_type: Input type ("image" or "video")
        
        Returns:
            Job result dictionary
        """
        # Check file existence
        if not os.path.exists(image_path):
            return {"error": f"Image file does not exist: {image_path}"}
        
        if not os.path.exists(audio_path):
            return {"error": f"Audio file does not exist: {audio_path}"}
        
        if person_count == "multi" and audio_path_2 and not os.path.exists(audio_path_2):
            return {"error": f"Second audio file does not exist: {audio_path_2}"}
        
        # Upload files to S3
        timestamp = int(time.time())
        
        # Upload image
        image_s3_key = f"input/infinitetalk/{timestamp}_{os.path.basename(image_path)}"
        image_s3_path = self.upload_to_s3(image_path, image_s3_key)
        if not image_s3_path:
            return {"error": "Image S3 upload failed"}
        
        # Upload audio
        audio_s3_key = f"input/infinitetalk/{timestamp}_{os.path.basename(audio_path)}"
        audio_s3_path = self.upload_to_s3(audio_path, audio_s3_key)
        if not audio_s3_path:
            return {"error": "Audio S3 upload failed"}
        
        # Upload second audio (for multiple people)
        audio_s3_path_2 = None
        if person_count == "multi" and audio_path_2:
            audio_s3_key_2 = f"input/infinitetalk/{timestamp}_{os.path.basename(audio_path_2)}"
            audio_s3_path_2 = self.upload_to_s3(audio_path_2, audio_s3_key_2)
            if not audio_s3_path_2:
                return {"error": "Second audio S3 upload failed"}
        
        # Configure API input data
        input_data = {
            "input_type": input_type,
            "person_count": person_count,
            "prompt": prompt,
            "width": width,
            "height": height
        }
        
        # Set media input
        if input_type == "image":
            input_data["image_path"] = image_s3_path
        else:
            input_data["video_path"] = image_s3_path
        
        # Set audio input
        input_data["wav_path"] = audio_s3_path
        
        # Set second audio (for multiple people)
        if person_count == "multi" and audio_s3_path_2:
            input_data["wav_path_2"] = audio_s3_path_2
        
        # Set max_frame
        if max_frame:
            input_data["max_frame"] = max_frame
        
        # Submit job and wait
        job_id = self.submit_job(input_data)
        if not job_id:
            return {"error": "Job submission failed"}
        
        result = self.wait_for_completion(job_id)
        return result
    
    def batch_process_audio_files(
        self,
        image_path: str,
        audio_folder_path: str,
        output_folder_path: str,
        valid_extensions: tuple = ('.wav', '.mp3', '.m4a', '.flac'),
        prompt: str = "A person talking naturally",
        width: int = 512,
        height: int = 512,
        max_frame: Optional[int] = None,
        person_count: str = "single",
        input_type: str = "image"
    ) -> Dict[str, Any]:
        """
        Batch process all audio files in folder
        
        Args:
            image_path: Common image file path to use
            audio_folder_path: Folder path containing audio files
            output_folder_path: Folder path to save results
            valid_extensions: Audio file extensions to process
            prompt: Prompt text
            width: Output width
            height: Output height
            max_frame: Maximum frame count
            person_count: Number of people
            input_type: Input type
        
        Returns:
            Batch processing result dictionary
        """
        # Check paths
        if not os.path.exists(image_path):
            return {"error": f"Image file does not exist: {image_path}"}
        
        if not os.path.isdir(audio_folder_path):
            return {"error": f"Audio folder does not exist: {audio_folder_path}"}
        
        # Create output folder
        os.makedirs(output_folder_path, exist_ok=True)
        
        # Get audio file list
        audio_files = [
            f for f in os.listdir(audio_folder_path)
            if f.lower().endswith(valid_extensions)
        ]
        
        if not audio_files:
            return {"error": f"No audio files to process: {audio_folder_path}"}
        
        logger.info(f"Batch processing started: {len(audio_files)} files")
        
        results = {
            "total_files": len(audio_files),
            "successful": 0,
            "failed": 0,
            "results": []
        }
        
        # Pre-upload common image to S3
        timestamp = int(time.time())
        image_s3_key = f"input/infinitetalk/batch_{timestamp}_{os.path.basename(image_path)}"
        image_s3_path = self.upload_to_s3(image_path, image_s3_key)
        
        if not image_s3_path:
            return {"error": "Common image S3 upload failed"}
        
        # Process each audio file
        for filename in audio_files:
            logger.info(f"\n==================== Processing started: {filename} ====================")
            
            audio_path = os.path.join(audio_folder_path, filename)
            
            # Upload audio file to S3
            audio_s3_key = f"input/infinitetalk/batch_{timestamp}_{filename}"
            audio_s3_path = self.upload_to_s3(audio_path, audio_s3_key)
            
            if not audio_s3_path:
                logger.error(f"[{filename}] S3 upload failed")
                results["failed"] += 1
                results["results"].append({
                    "filename": filename,
                    "status": "failed",
                    "error": "S3 upload failed"
                })
                continue
            
            # Configure API input data
            input_data = {
                "input_type": input_type,
                "person_count": person_count,
                "prompt": prompt,
                "width": width,
                "height": height
            }
            
            # Set media input
            if input_type == "image":
                input_data["image_path"] = image_s3_path
            else:
                input_data["video_path"] = image_s3_path
            
            # Set audio input
            input_data["wav_path"] = audio_s3_path
            
            # Set max_frame
            if max_frame:
                input_data["max_frame"] = max_frame
            
            # Submit job and wait
            job_id = self.submit_job(input_data)
            if not job_id:
                logger.error(f"[{filename}] Job submission failed")
                results["failed"] += 1
                results["results"].append({
                    "filename": filename,
                    "status": "failed",
                    "error": "Job submission failed"
                })
                continue
            
            result = self.wait_for_completion(job_id)
            
            if result.get('status') == 'COMPLETED':
                # Save result file
                base_filename = os.path.splitext(filename)[0]
                output_filename = os.path.join(output_folder_path, f"result_{base_filename}.mp4")
                
                if self.save_video_result(result, output_filename):
                    logger.info(f"✅ [{filename}] Processing completed")
                    results["successful"] += 1
                    results["results"].append({
                        "filename": filename,
                        "status": "success",
                        "output_file": output_filename,
                        "job_id": job_id
                    })
                else:
                    logger.error(f"[{filename}] Result save failed")
                    results["failed"] += 1
                    results["results"].append({
                        "filename": filename,
                        "status": "failed",
                        "error": "Result save failed",
                        "job_id": job_id
                    })
            else:
                logger.error(f"[{filename}] Job failed: {result.get('error', 'Unknown error')}")
                results["failed"] += 1
                results["results"].append({
                    "filename": filename,
                    "status": "failed",
                    "error": result.get('error', 'Unknown error'),
                    "job_id": job_id
                })
            
            logger.info(f"==================== Processing completed: {filename} ====================")
        
        logger.info(f"\n🎉 Batch processing completed: {results['successful']}/{results['total_files']} successful")
        return results


def main():
    """Usage example"""
    
    # Configuration (change to actual values)
    ENDPOINT_ID = "your-endpoint-id"
    RUNPOD_API_KEY = "your-runpod-api-key"
    
    # S3 configuration
    S3_ENDPOINT_URL = "https://s3api-eu-ro-1.runpod.io/"
    S3_ACCESS_KEY_ID = "your-s3-access-key"
    S3_SECRET_ACCESS_KEY = "your-s3-secret-key"
    S3_BUCKET_NAME = "your-bucket-name"
    S3_REGION = "eu-ro-1"
    
    # Initialize client
    client = InfinitetalkS3Client(
        runpod_endpoint_id=ENDPOINT_ID,
        runpod_api_key=RUNPOD_API_KEY,
        s3_endpoint_url=S3_ENDPOINT_URL,
        s3_access_key_id=S3_ACCESS_KEY_ID,
        s3_secret_access_key=S3_SECRET_ACCESS_KEY,
        s3_bucket_name=S3_BUCKET_NAME,
        s3_region=S3_REGION
    )
    
    print("=== Infinitetalk S3 Client Usage Example ===\n")
    
    # Example 1: Single file processing
    print("1. Single file processing")
    result1 = client.create_video_from_files(
        image_path="./examples/image.jpg",
        audio_path="./examples/audio.mp3",
        prompt="A person talking naturally",
        width=512,
        height=512
    )
    
    if result1.get('status') == 'COMPLETED':
        client.save_video_result(result1, "./output_single.mp4")
    else:
        print(f"Error: {result1.get('error')}")
    
    print("\n" + "-"*50 + "\n")
    
    # # Example 2: Batch processing
    # print("2. Batch processing")
    # batch_result = client.batch_process_audio_files(
    #     image_path="examples/image.jpg",
    #     audio_folder_path="examples/audio_files",
    #     output_folder_path="output/batch_results",
    #     prompt="A person talking naturally",
    #     width=512,
    #     height=512
    # )
    
    # print(f"Batch processing result: {batch_result}")
    
    # print("\n=== All examples completed ===")


if __name__ == "__main__":
    main()