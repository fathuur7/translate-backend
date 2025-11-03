# 📖 Frontend Integration Guide - Video Translation API

## 🚀 Base URL
```
Development: http://localhost:8000
Production: https://your-domain.com
```

---

## 📋 Table of Contents
1. [Quick Start](#quick-start)
2. [API Endpoints](#api-endpoints)
3. [Integration Examples](#integration-examples)
4. [Frontend Implementation](#frontend-implementation)
5. [WebSocket Alternative](#websocket-alternative)
6. [Error Handling](#error-handling)

---

## 🎯 Quick Start

### Architecture Overview
```
Frontend (React/Vue/etc)
    ↓ Upload Video
API Backend (FastAPI)
    ↓ Return job_id immediately
Background Processing
    ↓ Transcription + Translation
Frontend polls /status/{job_id}
    ↓ Get results when completed
Display results to user
```

---

## 🔌 API Endpoints

### 1. **POST `/translate-video/`** - Upload Video for Processing

**Description:** Upload video file untuk diproses di background. Return `job_id` untuk tracking.

**Request:**
```http
POST /translate-video/
Content-Type: multipart/form-data

Fields:
- video_file: File (required)
- target_language: string (required, e.g., "id", "en", "ja")
```

**Response (Immediate):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "video.mp4",
  "target_language": "id",
  "status": "pending",
  "message": "Video sedang diproses di background. Gunakan endpoint /status/{job_id} untuk cek progress."
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/translate-video/" \
  -F "video_file=@/path/to/video.mp4" \
  -F "target_language=id"
```

**JavaScript (Fetch) Example:**
```javascript
const formData = new FormData();
formData.append('video_file', videoFile); // File object from input
formData.append('target_language', 'id');

const response = await fetch('http://localhost:8000/translate-video/', {
  method: 'POST',
  body: formData
});

const data = await response.json();
console.log('Job ID:', data.job_id);
```

---

### 2. **GET `/translate-video/status/{job_id}`** - Check Processing Status

**Description:** Cek status dan progress dari job yang sedang diproses.

**Request:**
```http
GET /translate-video/status/{job_id}
```

**Response (Processing):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 60,
  "message": "Mengekstrak audio...",
  "video_filename": "video.mp4",
  "target_language": "id",
  "created_at": "2025-11-02T10:30:00",
  "updated_at": "2025-11-02T10:30:45"
}
```

**Response (Completed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "message": "Pemrosesan selesai!",
  "video_filename": "video.mp4",
  "target_language": "id",
  "created_at": "2025-11-02T10:30:00",
  "updated_at": "2025-11-02T10:31:30",
  "result": {
    "original_transcript": "Hello world, this is a test...",
    "original_srt": "1\n00:00:00,000 --> 00:00:02,000\nHello world...",
    "translated_srt": "1\n00:00:00,000 --> 00:00:02,000\nHalo dunia...",
    "video_url": "/static/uploads/videos/abc123_video.mp4",
    "srt_original_url": "/static/uploads/subtitles/def456_original.srt",
    "srt_translated_url": "/static/uploads/subtitles/ghi789_id.srt"
  }
}
```

**Response (Failed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "progress": 0,
  "message": "Error saat memproses",
  "error": "FFmpeg not found. Please install FFmpeg.",
  "video_filename": "video.mp4",
  "target_language": "id",
  "created_at": "2025-11-02T10:30:00",
  "updated_at": "2025-11-02T10:30:15"
}
```

**Status Values:**
- `pending` - Job created, waiting to start
- `processing` - Currently being processed
- `completed` - Successfully completed
- `failed` - Processing failed

---

### 3. **GET `/translate-video/jobs`** - List All Jobs

**Description:** List semua jobs (untuk admin/monitoring).

**Request:**
```http
GET /translate-video/jobs
```

**Response:**
```json
{
  "total": 10,
  "jobs": [
    {
      "job_id": "uuid-1",
      "status": "completed",
      "progress": 100,
      "video_filename": "video1.mp4",
      "target_language": "id",
      "created_at": "2025-11-02T10:00:00"
    },
    {
      "job_id": "uuid-2",
      "status": "processing",
      "progress": 45,
      "video_filename": "video2.mp4",
      "target_language": "en",
      "created_at": "2025-11-02T10:15:00"
    }
  ]
}
```

---

### 4. **GET `/translate-video/cache/stats`** - Cache Statistics

**Description:** Lihat statistik cache (berapa file yang di-cache).

**Request:**
```http
GET /translate-video/cache/stats
```

**Response:**
```json
{
  "cache_size": 15,
  "max_size": 100,
  "message": "Cache berisi 15 item"
}
```

---

### 5. **POST `/translate-video/cache/clear`** - Clear Cache

**Description:** Clear semua cache (untuk maintenance/testing).

**Request:**
```http
POST /translate-video/cache/clear
```

**Response:**
```json
{
  "message": "Cache berhasil dihapus",
  "cache_size": 0
}
```

---

### 6. **GET `/static/uploads/{folder}/{filename}`** - Download Result Files

**Description:** Download video atau subtitle file hasil processing.

**Example URLs:**
```
http://localhost:8000/static/uploads/videos/abc123_video.mp4
http://localhost:8000/static/uploads/subtitles/def456_original.srt
http://localhost:8000/static/uploads/subtitles/ghi789_id.srt
```

---

## 💻 Frontend Implementation

### React Example (Complete Integration)

```jsx
import React, { useState, useEffect } from 'react';

const VideoTranslator = () => {
  const [file, setFile] = useState(null);
  const [language, setLanguage] = useState('id');
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Upload video
  const handleUpload = async () => {
    if (!file) {
      alert('Please select a video file');
      return;
    }

    const formData = new FormData();
    formData.append('video_file', file);
    formData.append('target_language', language);

    try {
      const response = await fetch('http://localhost:8000/translate-video/', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (response.ok) {
        setJobId(data.job_id);
        setStatus(data.status);
        setError(null);
      } else {
        setError(data.detail || 'Upload failed');
      }
    } catch (err) {
      setError('Network error: ' + err.message);
    }
  };

  // Poll status
  useEffect(() => {
    if (!jobId) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(
          `http://localhost:8000/translate-video/status/${jobId}`
        );
        const data = await response.json();

        setStatus(data.status);

        if (data.status === 'completed') {
          setResult(data.result);
          clearInterval(pollInterval);
        } else if (data.status === 'failed') {
          setError(data.error || 'Processing failed');
          clearInterval(pollInterval);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [jobId]);

  // Download SRT file
  const downloadSRT = (url, filename) => {
    const link = document.createElement('a');
    link.href = `http://localhost:8000${url}`;
    link.download = filename;
    link.click();
  };

  return (
    <div className="container">
      <h1>Video Translator</h1>

      {/* Upload Form */}
      {!jobId && (
        <div>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => setFile(e.target.files[0])}
          />
          <select value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option value="id">Indonesian</option>
            <option value="en">English</option>
            <option value="ja">Japanese</option>
            <option value="ko">Korean</option>
            <option value="zh-CN">Chinese</option>
          </select>
          <button onClick={handleUpload}>Upload & Translate</button>
        </div>
      )}

      {/* Processing Status */}
      {jobId && !result && !error && (
        <div>
          <h2>Processing...</h2>
          <p>Job ID: {jobId}</p>
          <p>Status: {status}</p>
          <div className="spinner">⏳</div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div>
          <h2>✅ Translation Completed!</h2>
          
          <h3>Original Transcript:</h3>
          <pre>{result.original_transcript}</pre>

          <h3>Original Subtitle (SRT):</h3>
          <button onClick={() => downloadSRT(result.srt_original_url, 'original.srt')}>
            Download Original SRT
          </button>

          <h3>Translated Subtitle ({language}):</h3>
          <button onClick={() => downloadSRT(result.srt_translated_url, `translated_${language}.srt`)}>
            Download Translated SRT
          </button>

          <h3>Video with Subtitles:</h3>
          <video controls width="600">
            <source src={`http://localhost:8000${result.video_url}`} type="video/mp4" />
            <track
              label="Original"
              kind="subtitles"
              srcLang="auto"
              src={`http://localhost:8000${result.srt_original_url}`}
            />
            <track
              label={language}
              kind="subtitles"
              srcLang={language}
              src={`http://localhost:8000${result.srt_translated_url}`}
              default
            />
          </video>

          <button onClick={() => { setJobId(null); setResult(null); }}>
            Translate Another Video
          </button>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="error">
          <h2>❌ Error</h2>
          <p>{error}</p>
          <button onClick={() => { setJobId(null); setError(null); }}>
            Try Again
          </button>
        </div>
      )}
    </div>
  );
};

export default VideoTranslator;
```

---

### Vue 3 Example

```vue
<template>
  <div class="video-translator">
    <h1>Video Translator</h1>

    <!-- Upload Form -->
    <div v-if="!jobId">
      <input type="file" @change="onFileChange" accept="video/*" />
      <select v-model="language">
        <option value="id">Indonesian</option>
        <option value="en">English</option>
        <option value="ja">Japanese</option>
      </select>
      <button @click="uploadVideo">Upload & Translate</button>
    </div>

    <!-- Processing -->
    <div v-if="jobId && !result && !error">
      <h2>Processing...</h2>
      <p>Status: {{ status }}</p>
      <p>Progress: {{ progress }}%</p>
    </div>

    <!-- Results -->
    <div v-if="result">
      <h2>✅ Completed!</h2>
      <button @click="downloadFile(result.srt_translated_url)">
        Download Translated SRT
      </button>
      <video controls :src="getFullUrl(result.video_url)"></video>
    </div>

    <!-- Error -->
    <div v-if="error" class="error">
      <p>{{ error }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';

const API_BASE = 'http://localhost:8000';
const file = ref(null);
const language = ref('id');
const jobId = ref(null);
const status = ref(null);
const progress = ref(0);
const result = ref(null);
const error = ref(null);

const onFileChange = (e) => {
  file.value = e.target.files[0];
};

const uploadVideo = async () => {
  const formData = new FormData();
  formData.append('video_file', file.value);
  formData.append('target_language', language.value);

  try {
    const response = await fetch(`${API_BASE}/translate-video/`, {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();
    jobId.value = data.job_id;
    status.value = data.status;
  } catch (err) {
    error.value = err.message;
  }
};

// Poll status
watch(jobId, (newJobId) => {
  if (!newJobId) return;

  const interval = setInterval(async () => {
    try {
      const response = await fetch(`${API_BASE}/translate-video/status/${newJobId}`);
      const data = await response.json();

      status.value = data.status;
      progress.value = data.progress;

      if (data.status === 'completed') {
        result.value = data.result;
        clearInterval(interval);
      } else if (data.status === 'failed') {
        error.value = data.error;
        clearInterval(interval);
      }
    } catch (err) {
      console.error(err);
    }
  }, 2000);
});

const getFullUrl = (path) => `${API_BASE}${path}`;

const downloadFile = (url) => {
  const link = document.createElement('a');
  link.href = getFullUrl(url);
  link.download = url.split('/').pop();
  link.click();
};
</script>
```

---

### Vanilla JavaScript Example

```html
<!DOCTYPE html>
<html>
<head>
  <title>Video Translator</title>
</head>
<body>
  <h1>Video Translator</h1>
  
  <input type="file" id="videoFile" accept="video/*">
  <select id="language">
    <option value="id">Indonesian</option>
    <option value="en">English</option>
  </select>
  <button onclick="uploadVideo()">Upload</button>

  <div id="status"></div>
  <div id="result"></div>

  <script>
    const API_BASE = 'http://localhost:8000';
    let pollInterval;

    async function uploadVideo() {
      const fileInput = document.getElementById('videoFile');
      const language = document.getElementById('language').value;
      const file = fileInput.files[0];

      if (!file) {
        alert('Please select a video');
        return;
      }

      const formData = new FormData();
      formData.append('video_file', file);
      formData.append('target_language', language);

      try {
        const response = await fetch(`${API_BASE}/translate-video/`, {
          method: 'POST',
          body: formData
        });

        const data = await response.json();
        
        if (response.ok) {
          startPolling(data.job_id);
        } else {
          document.getElementById('status').innerHTML = 
            `<p style="color:red">Error: ${data.detail}</p>`;
        }
      } catch (err) {
        document.getElementById('status').innerHTML = 
          `<p style="color:red">Error: ${err.message}</p>`;
      }
    }

    function startPolling(jobId) {
      document.getElementById('status').innerHTML = 
        `<p>Processing Job ID: ${jobId}...</p>`;

      pollInterval = setInterval(async () => {
        try {
          const response = await fetch(`${API_BASE}/translate-video/status/${jobId}`);
          const data = await response.json();

          document.getElementById('status').innerHTML = 
            `<p>Status: ${data.status} | Progress: ${data.progress}%</p>`;

          if (data.status === 'completed') {
            clearInterval(pollInterval);
            displayResult(data.result);
          } else if (data.status === 'failed') {
            clearInterval(pollInterval);
            document.getElementById('status').innerHTML = 
              `<p style="color:red">Failed: ${data.error}</p>`;
          }
        } catch (err) {
          console.error(err);
        }
      }, 2000);
    }

    function displayResult(result) {
      document.getElementById('result').innerHTML = `
        <h2>✅ Completed!</h2>
        <a href="${API_BASE}${result.srt_translated_url}" download>
          Download Translated SRT
        </a>
        <br><br>
        <video controls width="600">
          <source src="${API_BASE}${result.video_url}" type="video/mp4">
        </video>
      `;
    }
  </script>
</body>
</html>
```

---

## 🔄 Polling Best Practices

### Recommended Polling Strategy

```javascript
// Adaptive polling - slower for long jobs
let pollInterval = 2000; // Start with 2 seconds
const maxInterval = 10000; // Max 10 seconds

const poll = async (jobId) => {
  const response = await fetch(`/translate-video/status/${jobId}`);
  const data = await response.json();

  if (data.status === 'completed' || data.status === 'failed') {
    return data;
  }

  // Increase interval gradually
  pollInterval = Math.min(pollInterval + 1000, maxInterval);
  
  await new Promise(resolve => setTimeout(resolve, pollInterval));
  return poll(jobId); // Recursive
};
```

### Stop Polling When User Leaves

```javascript
useEffect(() => {
  let active = true;

  const pollStatus = async () => {
    while (active && status !== 'completed' && status !== 'failed') {
      // Poll...
      await new Promise(r => setTimeout(r, 2000));
    }
  };

  pollStatus();

  return () => {
    active = false; // Stop polling on unmount
  };
}, [jobId]);
```

---

## ⚠️ Error Handling

### Common Errors & Solutions

```javascript
const handleError = (error, response) => {
  if (!response) {
    return 'Network error. Check your connection.';
  }

  switch (response.status) {
    case 400:
      return 'Invalid request. Check file format and parameters.';
    case 404:
      return 'Job not found. It may have been deleted.';
    case 413:
      return 'File too large. Max size: 100MB';
    case 422:
      return 'Invalid file format. Use MP4, MKV, AVI, etc.';
    case 500:
      return 'Server error. Please try again later.';
    default:
      return error.message || 'Unknown error occurred.';
  }
};
```

---

## 🌐 CORS Configuration (if needed)

If frontend is on different domain, backend already has CORS enabled:

```python
# Already configured in app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For production, change to:
```python
allow_origins=["https://your-frontend-domain.com"]
```

---

## 📊 Progress Indicators

### Progress Bar Example

```jsx
const ProgressBar = ({ progress, status }) => (
  <div className="progress-container">
    <div 
      className="progress-bar" 
      style={{ width: `${progress}%` }}
    >
      {progress}%
    </div>
    <p>{status}</p>
  </div>
);

// CSS
.progress-container {
  width: 100%;
  background: #f0f0f0;
  border-radius: 10px;
  overflow: hidden;
}

.progress-bar {
  height: 30px;
  background: linear-gradient(90deg, #4CAF50, #8BC34A);
  text-align: center;
  line-height: 30px;
  color: white;
  transition: width 0.3s ease;
}
```

---

## 🔐 Authentication (Future)

For production with auth:

```javascript
const uploadWithAuth = async (file, language, token) => {
  const formData = new FormData();
  formData.append('video_file', file);
  formData.append('target_language', language);

  const response = await fetch('http://localhost:8000/translate-video/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}` // Add when auth is implemented
    },
    body: formData
  });

  return response.json();
};
```

---

## 📝 Language Codes

Supported languages:

| Code | Language |
|------|----------|
| `id` | Indonesian (Bahasa Indonesia) |
| `en` | English |
| `ja` | Japanese (日本語) |
| `ko` | Korean (한국어) |
| `zh-CN` | Chinese Simplified (简体中文) |
| `zh-TW` | Chinese Traditional (繁體中文) |
| `es` | Spanish (Español) |
| `fr` | French (Français) |
| `de` | German (Deutsch) |
| `ar` | Arabic (العربية) |

[See full list](https://py-googletrans.readthedocs.io/en/latest/#googletrans-languages)

---

## 🚀 Quick Start Checklist

- [ ] Backend server running (`uvicorn app.main:app --reload`)
- [ ] FFmpeg installed
- [ ] API base URL configured in frontend
- [ ] File upload form implemented
- [ ] Polling mechanism for status check
- [ ] Result display with download links
- [ ] Error handling for failed jobs
- [ ] Loading indicators during processing

---

## 📚 Additional Resources

- **API Documentation:** http://localhost:8000/docs (Swagger UI)
- **Alternative API Docs:** http://localhost:8000/redoc (ReDoc)
- **Performance Guide:** See `TRANSLATION_OPTIMIZATION.md`
- **FFmpeg Setup:** See `QUICK_FFMPEG_INSTALL.md`

---

## 💡 Tips

1. **Show estimated time:** Based on video duration (e.g., 1 min video ≈ 30-60s processing)
2. **Allow cancellation:** Keep track of job_id for future cancel feature
3. **Cache on frontend:** Store completed results in localStorage
4. **Retry failed jobs:** Implement retry button for failed uploads
5. **Multi-file upload:** Queue multiple videos and process sequentially

---

## 🎉 Example Projects

Check `test_api.py` and `benchmark_performance.py` for Python client examples.

---

**Happy coding! 🚀** For issues or questions, check the main documentation files.
