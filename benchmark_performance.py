"""
Performance benchmark script untuk membandingkan speed berbagai konfigurasi.
"""
import time
import requests
import os

BASE_URL = "http://localhost:8000"

def benchmark_translation(video_path: str, language: str = "id", test_name: str = "Test"):
    """
    Upload video dan ukur waktu processing.
    """
    print(f"\n{'='*70}")
    print(f"🧪 {test_name}")
    print(f"{'='*70}")
    
    # Upload
    url = f"{BASE_URL}/translate-video/"
    
    with open(video_path, 'rb') as f:
        files = {'video_file': f}
        data = {'target_language': language}
        
        upload_start = time.time()
        response = requests.post(url, files=files, data=data)
        upload_time = time.time() - upload_start
        
        if response.status_code != 200:
            print(f"❌ Upload failed: {response.status_code}")
            return None
        
        result = response.json()
        job_id = result.get('job_id')
        print(f"✅ Upload: {upload_time:.2f}s | Job ID: {job_id}")
    
    # Poll until completed
    status_url = f"{BASE_URL}/translate-video/status/{job_id}"
    processing_start = time.time()
    
    while True:
        time.sleep(2)
        response = requests.get(status_url)
        
        if response.status_code != 200:
            print(f"❌ Status check failed")
            return None
        
        result = response.json()
        status = result.get('status')
        progress = result.get('progress', 0)
        
        elapsed = time.time() - processing_start
        print(f"   [{int(elapsed):3d}s] Status: {status:12s} | Progress: {progress:3d}%", end='\r')
        
        if status == 'completed':
            total_time = time.time() - upload_start
            print(f"\n✅ COMPLETED")
            print(f"   Upload time:     {upload_time:.2f}s")
            print(f"   Processing time: {elapsed:.2f}s")
            print(f"   Total time:      {total_time:.2f}s")
            return total_time
        
        elif status == 'failed':
            print(f"\n❌ FAILED: {result.get('error')}")
            return None
        
        if elapsed > 600:  # 10 min timeout
            print(f"\n⏰ Timeout after {elapsed:.0f}s")
            return None


def main():
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║       🚀 TRANSLATION PERFORMANCE BENCHMARK                           ║
║                                                                      ║
║  Test berbagai konfigurasi untuk menemukan setup tercepat          ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
""")
    
    video_path = input("\n📹 Enter path to test video: ").strip().strip('"')
    
    if not os.path.exists(video_path):
        print(f"❌ File not found: {video_path}")
        return
    
    language = input("🌐 Target language (default: id): ").strip() or "id"
    
    print(f"\n✅ Video: {os.path.basename(video_path)}")
    print(f"✅ Language: {language}")
    print(f"\n⚠️  Make sure server is running at {BASE_URL}")
    print(f"⚠️  Clear cache before benchmark: curl -X POST {BASE_URL}/translate-video/cache/clear")
    
    input("\n Press ENTER to start benchmark...")
    
    results = {}
    
    # Test 1: First upload (cache miss)
    print(f"\n{'#'*70}")
    print(f"# TEST 1: First Upload (Cache Miss)")
    print(f"{'#'*70}")
    time1 = benchmark_translation(video_path, language, "Test 1: Cache Miss")
    if time1:
        results["First Upload (Cache Miss)"] = time1
    
    # Test 2: Second upload (cache hit)
    print(f"\n{'#'*70}")
    print(f"# TEST 2: Second Upload (Cache Hit)")
    print(f"{'#'*70}")
    print("⏳ Waiting 3 seconds...")
    time.sleep(3)
    time2 = benchmark_translation(video_path, language, "Test 2: Cache Hit")
    if time2:
        results["Second Upload (Cache Hit)"] = time2
    
    # Results summary
    print(f"\n\n{'='*70}")
    print(f"📊 BENCHMARK RESULTS SUMMARY")
    print(f"{'='*70}")
    
    if results:
        for test_name, test_time in results.items():
            print(f"   {test_name:30s}: {test_time:6.2f}s")
        
        if len(results) == 2:
            cache_miss = results.get("First Upload (Cache Miss)", 0)
            cache_hit = results.get("Second Upload (Cache Hit)", 0)
            
            if cache_hit > 0:
                speedup = cache_miss / cache_hit
                print(f"\n   {'Cache Speedup':30s}: {speedup:6.1f}x faster! 🚀")
                
                time_saved = cache_miss - cache_hit
                print(f"   {'Time Saved':30s}: {time_saved:6.2f}s")
    
    print(f"{'='*70}")
    
    # Recommendations
    print(f"\n💡 OPTIMIZATION TIPS:")
    print(f"   1. Use WHISPER_MODEL=tiny for fastest transcription")
    print(f"   2. Batch translation is already enabled (automatic)")
    print(f"   3. Cache is working - second upload is instant!")
    print(f"   4. Enable GPU for 5-10x faster transcription (see docs)")
    
    print(f"\n✅ Benchmark completed!\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Benchmark interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
