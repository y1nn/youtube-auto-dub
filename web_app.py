#!/usr/bin/env python3
"""
YouTube Auto Dub - Web Interface Backend.

Flask-based web server providing a modern UI for the dubbing pipeline.
Uses Server-Sent Events (SSE) for real-time progress updates.

Author: Auto-generated web interface
"""

import json
import uuid
import time
import random
import shutil
import subprocess
import threading
from pathlib import Path
from flask import Flask, render_template, request, jsonify, Response, send_file

# Local imports
import src.engines
import src.youtube
import src.media

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # No caching for static files


@app.after_request
def add_no_cache_headers(response):
    """Disable caching for static files during development."""
    if 'static' in request.path:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
    return response

# ─── Job Storage ────────────────────────────────────────────────────────────
jobs = {}  # {job_id: {status, progress, stage, message, output_file, error}}
jobs_lock = threading.Lock()

PIPELINE_STAGES = [
    {"id": "download",    "label": "📥 Downloading",      "label_ar": "📥 تحميل الفيديو"},
    {"id": "transcribe",  "label": "🎤 Transcribing",     "label_ar": "🎤 تحويل الكلام لنص"},
    {"id": "chunk",       "label": "✂️ Chunking",          "label_ar": "✂️ تقسيم المقاطع"},
    {"id": "translate",   "label": "🌍 Translating",      "label_ar": "🌍 الترجمة"},
    {"id": "tts",         "label": "🔊 Voice Synthesis",   "label_ar": "🔊 توليد الصوت"},
    {"id": "render",      "label": "🎬 Rendering Video",   "label_ar": "🎬 تصيير الفيديو"},
]


def update_job(job_id, **kwargs):
    """Thread-safe job status update."""
    with jobs_lock:
        if job_id in jobs:
            jobs[job_id].update(kwargs)


def check_dependencies():
    """Verify critical dependencies."""
    from shutil import which
    missing = []
    if not which("ffmpeg"):
        missing.append("ffmpeg")
    if not which("ffprobe"):
        missing.append("ffprobe")
    if missing:
        return False, f"Missing: {', '.join(missing)}"
    try:
        import torch
        return True, f"PyTorch {torch.__version__} | CUDA: {torch.cuda.is_available()}"
    except ImportError:
        return False, "PyTorch not installed"


def cleanup_temp():
    """Clean up temp directory with retry for Windows file locks."""
    max_retries = 5
    for attempt in range(max_retries):
        try:
            if src.engines.TEMP_DIR.exists():
                shutil.rmtree(src.engines.TEMP_DIR)
            src.engines.TEMP_DIR.mkdir(parents=True, exist_ok=True)
            return
        except PermissionError:
            wait_time = 0.5 * (2 ** attempt)
            time.sleep(wait_time)


def create_base_silence():
    """Generate a base silence audio file for gap filling."""
    path = src.engines.TEMP_DIR / "silence_base.wav"
    if path.exists():
        return path
    cmd = [
        'ffmpeg', '-y', '-v', 'error',
        '-f', 'lavfi', '-i', 'anullsrc=r=24000:cl=mono',
        '-t', '300',
        '-c:a', 'pcm_s16le',
        str(path)
    ]
    subprocess.run(cmd, check=True)
    return path


def run_pipeline(job_id, url, lang, gender, gpu, subtitle):
    """Run the full dubbing pipeline in a background thread."""
    try:
        # ── Stage 0: Init ──────────────────────────────────────────────
        update_job(job_id, status="running", stage="init", progress=0,
                   message="Initializing pipeline...")
        
        ok, dep_msg = check_dependencies()
        if not ok:
            update_job(job_id, status="error", error=f"Dependency check failed: {dep_msg}")
            return
        
        cleanup_temp()
        device = "cpu"
        if gpu:
            try:
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
                else:
                    update_job(job_id, message="CUDA not available, using CPU instead...")
            except ImportError:
                update_job(job_id, message="PyTorch CUDA not found, using CPU...")
        engine = src.engines.Engine(device)

        # Report the actual device being used
        device_label = device.upper()
        if device == "cuda":
            import torch
            device_label = f"CUDA ({torch.cuda.get_device_name(0)})"
        update_job(job_id, device=device_label)

        # ── Stage 1: Download ──────────────────────────────────────────
        update_job(job_id, stage="download", progress=5,
                   message=f"Downloading video and audio from YouTube... [{device_label}]")
        
        try:
            video_path = src.youtube.download_video(url)
            audio_path = src.youtube.download_audio(url)
        except Exception as e:
            update_job(job_id, status="error", 
                       error=f"Download failed: {str(e)}. Check if URL is valid.")
            return
        
        update_job(job_id, progress=15, message="Download complete!")

        # ── Stage 2: Transcribe ────────────────────────────────────────
        update_job(job_id, stage="transcribe", progress=20,
                   message="Transcribing speech with Whisper AI...")
        
        raw_segments = engine.transcribe_safe(audio_path)
        update_job(job_id, progress=35,
                   message=f"Transcription complete: {len(raw_segments)} segments")

        # ── Stage 3: Chunk ─────────────────────────────────────────────
        update_job(job_id, stage="chunk", progress=40,
                   message="Optimizing audio chunks...")
        
        chunks = src.engines.smart_chunk(raw_segments)
        update_job(job_id, progress=45,
                   message=f"Optimized into {len(chunks)} chunks")

        # ── Stage 4: Translate ─────────────────────────────────────────
        update_job(job_id, stage="translate", progress=50,
                   message=f"Translating to {lang.upper()}...")
        
        texts = [c['text'] for c in chunks]
        translated_texts = engine.translate_safe(texts, lang)
        
        for i, chunk in enumerate(chunks):
            chunk['trans_text'] = translated_texts[i]
        
        update_job(job_id, progress=60,
                   message="Translation complete!")

        # ── Stage 5: TTS ───────────────────────────────────────────────
        update_job(job_id, stage="tts", progress=65,
                   message=f"Generating {gender} voice...")
        
        failed_tts = 0
        for i, chunk in enumerate(chunks):
            filename = f"chunk_{i:04d}.mp3"
            tts_path = src.engines.TEMP_DIR / filename
            
            try:
                engine.synthesize(
                    text=chunk['trans_text'],
                    target_lang=lang,
                    gender=gender,
                    out_path=tts_path
                )
                time.sleep(random.uniform(0.5, 1.5))
                
                slot_duration = chunk['end'] - chunk['start']
                final_audio = src.media.fit_audio(tts_path, slot_duration)
                chunk['processed_audio'] = final_audio
            except Exception as e:
                failed_tts += 1
                continue
            
            # Update progress within TTS stage (65-85%)
            tts_progress = 65 + int((i + 1) / len(chunks) * 20)
            update_job(job_id, progress=tts_progress,
                       message=f"Voice synthesis: {i+1}/{len(chunks)} chunks")
        
        update_job(job_id, progress=85,
                   message=f"TTS complete ({len(chunks) - failed_tts}/{len(chunks)} successful)")

        # ── Stage 6: Render ────────────────────────────────────────────
        update_job(job_id, stage="render", progress=88,
                   message="Rendering final video...")
        
        try:
            silence_path = create_base_silence()
            concat_list_path = src.engines.TEMP_DIR / "concat_list.txt"
            src.media.create_concat_file(chunks, silence_path, concat_list_path)
            
            subtitle_path = None
            if subtitle:
                subtitle_path = src.engines.TEMP_DIR / "subtitles.srt"
                src.media.generate_srt(chunks, subtitle_path)
            
            video_name = video_path.stem
            sub_suffix = "_sub" if subtitle else ""
            out_name = f"dubbed_{lang}_{gender}{sub_suffix}_{video_name}.mp4"
            final_output = src.engines.OUTPUT_DIR / out_name
            
            src.media.render_video(video_path, concat_list_path, final_output,
                                   subtitle_path=subtitle_path)
            
            if final_output.exists():
                file_size = final_output.stat().st_size / (1024 * 1024)
                update_job(job_id, status="complete", progress=100,
                           stage="done",
                           message=f"Done! File size: {file_size:.1f} MB",
                           output_file=str(final_output))
            else:
                update_job(job_id, status="error",
                           error="Output file was not created")
        except Exception as e:
            update_job(job_id, status="error",
                       error=f"Rendering failed: {str(e)}")
            
    except Exception as e:
        update_job(job_id, status="error", error=f"Pipeline error: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Serve the main page."""
    return render_template("index.html")


@app.route("/api/languages")
def get_languages():
    """Return available languages from language_map.json."""
    langs = []
    for code, data in src.engines.LANG_DATA.items():
        entry = {
            "code": code,
            "name": data.get("name", code),
            "native_name": data.get("native_name", ""),
        }
        langs.append(entry)
    
    # Sort by name
    langs.sort(key=lambda x: x["name"])
    return jsonify({"languages": langs, "count": len(langs)})


@app.route("/api/dub", methods=["POST"])
def start_dub():
    """Start a dubbing job."""
    data = request.get_json()
    
    if not data or "url" not in data:
        return jsonify({"error": "Missing YouTube URL"}), 400
    
    url = data["url"].strip()
    lang = data.get("lang", "es")
    gender = data.get("gender", "female")
    gpu = data.get("gpu", False)
    subtitle = data.get("subtitle", False)
    
    # Basic URL validation
    if "youtube.com" not in url and "youtu.be" not in url:
        return jsonify({"error": "Invalid YouTube URL"}), 400
    
    # Create job
    job_id = str(uuid.uuid4())[:8]
    with jobs_lock:
        jobs[job_id] = {
            "status": "queued",
            "progress": 0,
            "stage": "queued",
            "message": "Job queued...",
            "output_file": None,
            "error": None,
            "url": url,
            "lang": lang,
            "gender": gender,
        }
    
    # Start pipeline in background thread
    thread = threading.Thread(
        target=run_pipeline,
        args=(job_id, url, lang, gender, gpu, subtitle),
        daemon=True
    )
    thread.start()
    
    return jsonify({"job_id": job_id, "message": "Dubbing job started!"})


@app.route("/api/status/<job_id>")
def job_status_sse(job_id):
    """Stream real-time job progress via Server-Sent Events."""
    def generate():
        last_sent = None
        while True:
            with jobs_lock:
                job = jobs.get(job_id)
            
            if not job:
                yield f"data: {json.dumps({'error': 'Job not found'})}\n\n"
                break
            
            # Only send if data changed
            current = json.dumps(job, default=str)
            if current != last_sent:
                yield f"data: {current}\n\n"
                last_sent = current
            
            # Stop streaming if job is done or errored
            if job["status"] in ("complete", "error"):
                break
            
            time.sleep(0.5)
    
    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


@app.route("/api/job/<job_id>")
def job_status_poll(job_id):
    """Return current job status as JSON (polling fallback)."""
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/api/download/<job_id>")
def download_file(job_id):
    """Download the final dubbed video."""
    with jobs_lock:
        job = jobs.get(job_id)
    
    if not job:
        return jsonify({"error": "Job not found"}), 404
    
    if job["status"] != "complete" or not job.get("output_file"):
        return jsonify({"error": "File not ready"}), 400
    
    output_path = Path(job["output_file"])
    if not output_path.exists():
        return jsonify({"error": "Output file missing"}), 404
    
    return send_file(
        output_path,
        as_attachment=True,
        download_name=output_path.name,
        mimetype="video/mp4"
    )


@app.route("/api/check")
def health_check():
    """Check system health and dependencies."""
    ok, msg = check_dependencies()
    cuda_available = False
    gpu_name = None
    try:
        import torch
        cuda_available = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if cuda_available else None
    except ImportError:
        pass
    return jsonify({
        "healthy": ok,
        "details": msg,
        "cuda_available": cuda_available,
        "gpu_name": gpu_name,
    })


# ═══════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  YOUTUBE AUTO DUB — WEB INTERFACE")
    print("  Open: http://localhost:5000")
    print("=" * 60 + "\n")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
