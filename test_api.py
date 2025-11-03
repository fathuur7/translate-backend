"""
Script testing untuk Video Translation API dengan fitur background jobs dan caching.
Jalankan server dulu dengan: uvicorn app.main:app --reload
"""

import requests
import time
import os
import sys

BASE_URL = "http://localhost:8000"

def test_upload_video(video_path: str, target_language: str = "id"):
    """Upload video dan dapatkan job_id"""
    print(f"\n{'='*60}")
    print(f"📤 Uploading video: {os.path.basename(video_path)}")
    print(f"   Target language: {target_language}")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/translate-video/"
    
    with open(video_path, 'rb') as f:
        files = {'video_file': f}
        data = {'target_language': target_language}
        
        start_time = time.time()
        response = requests.post(url, files=files, data=data)
        elapsed = time.time() - start_time
        
        print(f"⏱️  Upload time: {elapsed:.2f} seconds")
        
        if response.status_code == 200:
            result = response.json()
            job_id = result.get('job_id')
            print(f"✅ Upload successful!")
            print(f"   Job ID: {job_id}")
            print(f"   Status: {result.get('status')}")
            print(f"   Message: {result.get('message')}")
            return job_id
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None


def poll_job_status(job_id: str, poll_interval: int = 3, max_wait: int = 300):
    """Poll job status hingga selesai atau timeout"""
    print(f"\n{'='*60}")
    print(f"🔍 Polling job status: {job_id}")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/translate-video/status/{job_id}"
    start_time = time.time()
    
    while True:
        elapsed = time.time() - start_time
        
        if elapsed > max_wait:
            print(f"⏰ Timeout after {max_wait} seconds")
            return None
        
        response = requests.get(url)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status')
            progress = result.get('progress', 0)
            message = result.get('message', '')
            
            print(f"⏳ [{int(elapsed)}s] Status: {status} | Progress: {progress}% | {message}")
            
            if status == 'completed':
                print(f"\n✅ Job completed successfully!")
                print(f"   Total time: {elapsed:.2f} seconds")
                
                # Print hasil
                if 'result' in result:
                    res = result['result']
                    print(f"\n📊 Results:")
                    print(f"   Video URL: {res.get('video_url')}")
                    print(f"   Original SRT: {res.get('srt_original_url')}")
                    print(f"   Translated SRT: {res.get('srt_translated_url')}")
                    print(f"\n📝 Transcript preview:")
                    transcript = res.get('original_transcript', '')
                    print(f"   {transcript[:200]}...")
                
                return result
            
            elif status == 'failed':
                print(f"\n❌ Job failed!")
                print(f"   Error: {result.get('error')}")
                return None
            
            # Tunggu sebelum poll lagi
            time.sleep(poll_interval)
        
        else:
            print(f"❌ Error polling status: {response.status_code}")
            print(f"   {response.text}")
            return None


def get_cache_stats():
    """Dapatkan statistik cache"""
    print(f"\n{'='*60}")
    print(f"💾 Cache Statistics")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/translate-video/cache/stats"
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        print(f"   Cache size: {result.get('cache_size')}/{result.get('max_size')}")
        print(f"   Message: {result.get('message')}")
    else:
        print(f"❌ Error: {response.status_code}")


def list_all_jobs():
    """List semua jobs"""
    print(f"\n{'='*60}")
    print(f"📋 All Jobs")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/translate-video/jobs"
    response = requests.get(url)
    
    if response.status_code == 200:
        result = response.json()
        jobs = result.get('jobs', [])
        total = result.get('total', 0)
        
        print(f"   Total jobs: {total}")
        
        for idx, job in enumerate(jobs, 1):
            print(f"\n   [{idx}] Job ID: {job.get('job_id')}")
            print(f"       Status: {job.get('status')} ({job.get('progress')}%)")
            print(f"       File: {job.get('video_filename')}")
            print(f"       Language: {job.get('target_language')}")
            print(f"       Created: {job.get('created_at')}")
    else:
        print(f"❌ Error: {response.status_code}")


def clear_cache():
    """Clear cache"""
    print(f"\n{'='*60}")
    print(f"🗑️  Clearing Cache")
    print(f"{'='*60}")
    
    url = f"{BASE_URL}/translate-video/cache/clear"
    response = requests.post(url)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ {result.get('message')}")
    else:
        print(f"❌ Error: {response.status_code}")


def main():
    """Main test flow"""
    print(f"\n{'#'*60}")
    print(f"# 🎬 Video Translation API - Performance Test")
    print(f"{'#'*60}")
    
    # Check jika ada argument video file
    if len(sys.argv) < 2:
        print("\n⚠️  Usage: python test_api.py <video_file_path> [target_language]")
        print("   Example: python test_api.py test_video.mp4 id")
        sys.exit(1)
    
    video_path = sys.argv[1]
    target_language = sys.argv[2] if len(sys.argv) > 2 else "id"
    
    if not os.path.exists(video_path):
        print(f"❌ Error: File not found: {video_path}")
        sys.exit(1)
    
    # Test 1: Upload pertama (cache miss - harus diproses)
    print(f"\n🧪 TEST 1: First upload (cache miss)")
    job_id_1 = test_upload_video(video_path, target_language)
    
    if job_id_1:
        result_1 = poll_job_status(job_id_1)
        
        # Test 2: Upload file yang sama (cache hit - instant)
        print(f"\n🧪 TEST 2: Second upload of same file (cache hit)")
        time.sleep(2)  # Small delay
        
        job_id_2 = test_upload_video(video_path, target_language)
        
        if job_id_2:
            result_2 = poll_job_status(job_id_2, poll_interval=1)
            
            if result_2:
                print(f"\n⚡ Cache hit! Processing was instant.")
    
    # Show statistics
    get_cache_stats()
    list_all_jobs()
    
    print(f"\n{'#'*60}")
    print(f"# ✅ Test completed!")
    print(f"{'#'*60}\n")


if __name__ == "__main__":
    main()
