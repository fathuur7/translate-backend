# 🎬 Video Translation Backend API

<div align="center">

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)
![Whisper](https://img.shields.io/badge/OpenAI-Whisper-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**High-performance video transcription and translation API powered by OpenAI Whisper**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [API Documentation](#-api-documentation) • [Performance](#-performance)

</div>

---

## 📖 Overview

Video Translation Backend adalah REST API berbasis FastAPI yang memungkinkan Anda untuk:
- 🎙️ **Transcribe** video ke teks menggunakan OpenAI Whisper
- 🌍 **Translate** subtitle ke berbagai bahasa (100+ bahasa)
- ⚡ **Process** video secara asynchronous dengan background tasks
- 💾 **Cache** hasil untuk performa optimal
- 📊 **Track** progress processing secara real-time

Sistem ini dioptimasi untuk **kecepatan tinggi** dengan fitur caching, batch translation, dan background processing.

---

## ✨ Features

### Core Features
- 🎥 **Video Transcription** - Extract audio dan transcribe menggunakan Whisper AI
- 🔤 **Multi-language Translation** - Support 100+ bahasa via Google Translate
- 📝 **SRT Generation** - Generate subtitle file (SRT format) otomatis
- ⚡ **Background Processing** - Non-blocking API dengan job tracking
- 🚀 **Smart Caching** - File-level dan segment-level caching untuk speed

### Performance Optimizations
- 📦 **Batch Translation** - Process multiple segments sekaligus (5-10x faster)
- 🎯 **Whisper Model Selection** - Pilih model (tiny/base/small/medium/large) sesuai kebutuhan
- 💨 **Local Storage** - Zero network overhead (no cloud upload)
- 🔄 **LRU Cache** - Intelligent cache eviction untuk memory efficiency
- 📊 **Progress Tracking** - Real-time status updates

### Technical Features
- 🔐 **Google OAuth2** - Ready (optional authentication)
- 🗄️ **SQLAlchemy** - Database ORM ready
- 📚 **Auto Documentation** - Swagger UI & ReDoc included
- 🐛 **Error Handling** - Comprehensive error messages
- 🔧 **Configurable** - Environment variables untuk customization

---

---

## 🔌 Frontend Integration

This backend is designed to work seamlessly with the **TransVidio Frontend**.

- **Repository**: [TransVidio Frontend](../transvidio-frontend)
- **Integration**:
    - **API URL**: The frontend connects to `http://localhost:8000` (configurable via `.env`).
    - **CORS**: Configured to allow requests from the frontend (default `*`).
    - **Static Files**: Serves processed videos and subtitles via `/static` endpoint.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.13** atau lebih tinggi
- **FFmpeg** (required untuk audio processing)

### 1. Install FFmpeg

**Windows (PowerShell as Administrator):**
```powershell
# Via Chocolatey
choco install ffmpeg

# Or download manually from https://ffmpeg.org/download.html
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

Verify installation:
```bash
ffmpeg -version
```

### 2. Clone Repository

```bash
git clone https://github.com/fathuur7/translate-backend.git
cd translate-backend
```

### 3. Create Virtual Environment

**Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file (optional)
# Set WHISPER_MODEL, CACHE_MAX_SIZE, etc.
```

### 6. Run Server

```bash
uvicorn app.main:app --reload
```

Server akan berjalan di: **http://localhost:8000**

🎉 **Done!** API siap digunakan.

---

## 📚 API Documentation

### Interactive Documentation

Setelah server running, buka:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

#### 1. Upload & Process Video

```http
POST /translate-video/
Content-Type: multipart/form-data

Parameters:
- video_file: File (MP4, AVI, MKV, etc.)
- target_language: string (e.g., "id", "en", "ja")

Response:
{
  "job_id": "uuid",
  "status": "pending",
  "message": "Video sedang diproses di background"
}
```

#### 2. Check Status

```http
GET /translate-video/status/{job_id}

Response (completed):
{
  "job_id": "uuid",
  "status": "completed",
  "progress": 100,
  "result": {
    "original_transcript": "...",
    "original_srt": "...",
    "translated_srt": "...",
    "video_url": "/static/uploads/videos/...",
    "srt_original_url": "/static/uploads/subtitles/...",
    "srt_translated_url": "/static/uploads/subtitles/..."
  }
}
```

#### 3. List Jobs

```http
GET /translate-video/jobs

Response:
{
  "total": 10,
  "jobs": [...]
}
```

#### 4. Cache Management

```http
GET /translate-video/cache/stats
POST /translate-video/cache/clear
```

### Language Codes

| Code | Language | Code | Language |
|------|----------|------|----------|
| `id` | Indonesian | `en` | English |
| `ja` | Japanese | `ko` | Korean |
| `zh-CN` | Chinese (Simplified) | `zh-TW` | Chinese (Traditional) |
| `es` | Spanish | `fr` | French |
| `de` | German | `ar` | Arabic |

[See full list (100+ languages)](https://py-googletrans.readthedocs.io/en/latest/#googletrans-languages)

---

## 💻 Usage Examples

### Python Client

```python
import requests

# Upload video
with open('video.mp4', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/translate-video/',
        files={'video_file': f},
        data={'target_language': 'id'}
    )

job_id = response.json()['job_id']
print(f"Job ID: {job_id}")

# Check status
import time
while True:
    status = requests.get(f'http://localhost:8000/translate-video/status/{job_id}')
    data = status.json()
    
    if data['status'] == 'completed':
        print("Selesai!")
        print(f"Translated SRT: {data['result']['srt_translated_url']}")
        break
    elif data['status'] == 'failed':
        print(f"Gagal: {data['error']}")
        break
    
    print(f"Progress: {data['progress']}%")
    time.sleep(2)
```

### JavaScript (Fetch API)

```javascript
// Upload
const formData = new FormData();
formData.append('video_file', videoFile);
formData.append('target_language', 'id');

const uploadResponse = await fetch('http://localhost:8000/translate-video/', {
  method: 'POST',
  body: formData
});

const { job_id } = await uploadResponse.json();

// Poll status
const checkStatus = async () => {
  const response = await fetch(`http://localhost:8000/translate-video/status/${job_id}`);
  const data = await response.json();
  
  if (data.status === 'completed') {
    console.log('Done!', data.result);
    return;
  }
  
  setTimeout(checkStatus, 2000);
};

checkStatus();
```

### cURL

```bash
# Upload
curl -X POST "http://localhost:8000/translate-video/" \
  -F "video_file=@video.mp4" \
  -F "target_language=id"

# Check status
curl "http://localhost:8000/translate-video/status/{job_id}"
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# Whisper Model Selection
WHISPER_MODEL=base  # Options: tiny, base, small, medium, large

# Cache Configuration
CACHE_MAX_SIZE=100  # Maximum cached transcriptions

# Translation Batch Size
TRANSLATION_BATCH_SIZE=50  # Segments per batch
```

### Whisper Model Comparison

| Model | Speed | Accuracy | Memory | Recommended For |
|-------|-------|----------|--------|-----------------|
| `tiny` | ⚡⚡⚡⚡⚡ | ⭐⭐ | 1 GB | Testing, quick previews |
| `base` | ⚡⚡⚡⚡ | ⭐⭐⭐ | 1 GB | **Default, balanced** |
| `small` | ⚡⚡⚡ | ⭐⭐⭐⭐ | 2 GB | Production, good quality |
| `medium` | ⚡⚡ | ⭐⭐⭐⭐⭐ | 5 GB | High accuracy needed |
| `large` | ⚡ | ⭐⭐⭐⭐⭐ | 10 GB | Maximum accuracy |

**Recommendation:** Start with `base`, upgrade to `small` for production.

---

## 📊 Performance

### Benchmarks

**Test Environment:**
- Video: 2 minutes, Korean audio
- Model: Whisper `base`
- Language: Korean → Indonesian

**Results:**

| Metric | First Run | Cached Run |
|--------|-----------|------------|
| Total Time | ~45 seconds | ~2 seconds |
| Transcription | ~30s | ~0s (cached) |
| Translation | ~10s | ~0s (cached) |
| File Operations | ~5s | ~2s |

**Speedup:** ~22x faster with cache! 🚀

### Optimization Features

1. ✅ **File-level Cache** - Same video = instant result
2. ✅ **Segment-level Cache** - Same audio segments reused
3. ✅ **Batch Translation** - 5-10x faster than sequential
4. ✅ **Background Processing** - API responds immediately
5. ✅ **Local Storage** - No network upload delays

See `TRANSLATION_OPTIMIZATION.md` for detailed analysis.

---

## 🏗️ Project Structure

```
translate-backend/
├── app/
│   ├── main.py                    # FastAPI application
│   ├── config/
│   │   └── db.py                  # Database configuration
│   ├── controllers/
│   │   └── auth_controller.py     # Authentication logic
│   ├── middleware/
│   │   └── auth_middleware.py     # Auth middleware
│   ├── models/
│   │   ├── User.py                # User model
│   │   └── Translation.py         # Translation model
│   ├── routers/
│   │   ├── auth_routes.py         # Auth endpoints
│   │   └── translate_router.py    # Translation endpoints
│   ├── services/
│   │   └── TranslationService.py  # Core translation service
│   ├── utils/
│   │   ├── functions.py           # Utility functions
│   │   ├── cache_manager.py       # Transcription cache
│   │   └── job_manager.py         # Background job tracking
│   ├── static/
│   │   └── uploads/               # Local file storage
│   │       ├── videos/
│   │       └── subtitles/
│   └── migration/
│       └── create_tables.py       # Database migrations
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
├── README.md                      # This file
├── FRONTEND_INTEGRATION.md        # Frontend guide
└── docs/                          # Additional documentation
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. FFmpeg Not Found

**Error:** `[WinError 2] The system cannot find the file specified`

**Solution:**
```powershell
# Install FFmpeg
choco install ffmpeg

# Restart terminal
# Verify
ffmpeg -version
```

See `QUICK_FFMPEG_INSTALL.md` for detailed guide.

#### 2. Python 3.13 Module Errors

**Error:** `ModuleNotFoundError: No module named 'cgi'`

**Solution:** Already fixed! We use `deep-translator` instead of `googletrans`.

#### 3. Out of Memory

**Error:** CUDA/Memory error during Whisper transcription

**Solution:**
```bash
# Use smaller model
WHISPER_MODEL=tiny  # or base
```

#### 4. Translation Not Working

**Check:**
- Server logs showing "🌐 Menerjemahkan ke bahasa 'XX'..."
- `translate_to` parameter is set
- Output SRT contains translated text

See `PYTHON_313_FIX.md` for migration details.

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/fathuur7/translate-backend/issues)
- **Documentation:** See `/docs` folder for detailed guides
- **API Docs:** http://localhost:8000/docs (when server running)

---

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) - Audio transcription
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [deep-translator](https://github.com/nidhaloff/deep-translator) - Translation library
- [MoviePy](https://zulko.github.io/moviepy/) - Video processing

---

## 📈 Roadmap

- [ ] WebSocket support untuk real-time progress
- [ ] Batch video processing
- [ ] Custom dictionary untuk translation
- [ ] Video preview dengan embedded subtitles
- [ ] Export ke berbagai format (VTT, ASS, etc.)
- [ ] Docker container untuk easy deployment
- [ ] Cloud storage integration (S3, GCS)
- [ ] User authentication & quota system

---

## 📝 Changelog

### v2.0.0 (November 2024)
- ✨ Added background task processing
- ✨ Implemented smart caching system
- ✨ Batch translation optimization
- ✨ Whisper model selection
- 🐛 Fixed Python 3.13 compatibility
- 🐛 Fixed translation logic bugs
- 📚 Comprehensive documentation

### v1.0.0 (Initial Release)
- ✨ Basic transcription & translation
- ✨ SRT generation
- ✨ Cloudinary integration

---

<div align="center">

**Made with ❤️ by [fathuur7](https://github.com/fathuur7)**

⭐ Star this repo if you find it helpful!

</div>
