/* ═══════════════════════════════════════════════════════════
   YouTube Auto Dub — Frontend Application Logic
   ═══════════════════════════════════════════════════════════ */

(() => {
    'use strict';

    // ─── DOM Elements ──────────────────────────────────────────
    const $ = (sel) => document.querySelector(sel);
    const $$ = (sel) => document.querySelectorAll(sel);

    const urlInput = $('#urlInput');
    const urlHint = $('#urlHint');
    const langSearch = $('#langSearch');
    const langSelect = $('#langSelect');
    const genderBtns = $$('.toggle-btn[data-gender]');
    const gpuToggle = $('#gpuToggle');
    const subtitleToggle = $('#subtitleToggle');
    const dubForm = $('#dubForm');
    const submitBtn = $('#submitBtn');
    const progressSection = $('#progressSection');
    const progressFill = $('#progressFill');
    const progressText = $('#progressText');
    const stagesContainer = $('#stagesContainer');
    const statusMessage = $('#statusMessage');
    const jobIdLabel = $('#jobIdLabel');
    const resultSection = $('#resultSection');
    const resultSuccess = $('#resultSuccess');
    const resultError = $('#resultError');
    const resultMessage = $('#resultMessage');
    const errorMessage = $('#errorMessage');
    const downloadBtn = $('#downloadBtn');
    const retryBtn = $('#retryBtn');
    const systemStatus = $('#systemStatus');

    // ─── State ─────────────────────────────────────────────────
    let selectedGender = 'female';
    let allLanguages = [];
    let currentJobId = null;
    let eventSource = null;

    // ─── Stage Order Map ───────────────────────────────────────
    const STAGE_ORDER = ['download', 'transcribe', 'chunk', 'translate', 'tts', 'render', 'done'];

    // ═══════════════════════════════════════════════════════════
    // INITIALIZATION
    // ═══════════════════════════════════════════════════════════

    async function init() {
        checkSystemHealth();
        await loadLanguages();
        setupEventListeners();
        resumeActiveJob();
    }

    // ─── Resume Active Job After Refresh ────────────────────────
    async function resumeActiveJob() {
        const savedJobId = localStorage.getItem('yt_dub_job_id');
        if (!savedJobId) return;

        try {
            const res = await fetch(`/api/job/${savedJobId}`);
            if (!res.ok) {
                localStorage.removeItem('yt_dub_job_id');
                return;
            }
            const data = await res.json();

            // If job is still running, reconnect
            if (data.status === 'running' || data.status === 'queued') {
                currentJobId = savedJobId;
                showProgress(savedJobId);
                updateProgress(data);
                startSSE(savedJobId);
                submitBtn.disabled = true;
                submitBtn.querySelector('.btn-text').style.display = 'none';
                submitBtn.querySelector('.btn-loading').style.display = 'inline-flex';
            } else if (data.status === 'complete') {
                currentJobId = savedJobId;
                showProgress(savedJobId);
                updateProgress(data);
                finishSuccess(data);
            } else if (data.status === 'error') {
                currentJobId = savedJobId;
                showProgress(savedJobId);
                updateProgress(data);
                finishError(data);
            } else {
                localStorage.removeItem('yt_dub_job_id');
            }
        } catch {
            localStorage.removeItem('yt_dub_job_id');
        }
    }

    // ─── System Health Check ───────────────────────────────────
    async function checkSystemHealth() {
        try {
            const res = await fetch('/api/check');
            const data = await res.json();

            const dot = systemStatus.querySelector('.status-dot');
            const text = systemStatus.querySelector('.status-text');

            if (data.healthy) {
                dot.className = 'status-dot online';
                text.textContent = data.cuda_available
                    ? `GPU: ${data.gpu_name}`
                    : 'CPU Mode';
            } else {
                dot.className = 'status-dot offline';
                text.textContent = 'System Error';
            }
        } catch {
            const dot = systemStatus.querySelector('.status-dot');
            const text = systemStatus.querySelector('.status-text');
            dot.className = 'status-dot offline';
            text.textContent = 'Offline';
        }
    }

    // ─── Load Languages ────────────────────────────────────────
    async function loadLanguages() {
        try {
            const res = await fetch('/api/languages');
            const data = await res.json();
            allLanguages = data.languages;

            populateLanguageSelect(allLanguages);
        } catch (err) {
            console.error('Failed to load languages:', err);
            langSelect.innerHTML = '<option value="es">Spanish (Fallback)</option>';
        }
    }

    function populateLanguageSelect(langs) {
        langSelect.innerHTML = '';
        langs.forEach(lang => {
            const opt = document.createElement('option');
            opt.value = lang.code;
            opt.textContent = lang.native_name
                ? `${lang.name} — ${lang.native_name}`
                : lang.name;
            langSelect.appendChild(opt);
        });

        // Default to Spanish
        langSelect.value = 'es';

        // Update count in search placeholder
        langSearch.placeholder = `Search ${langs.length} languages...`;
    }

    // ═══════════════════════════════════════════════════════════
    // EVENT LISTENERS
    // ═══════════════════════════════════════════════════════════

    function setupEventListeners() {
        // Gender toggle
        genderBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                genderBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                selectedGender = btn.dataset.gender;
            });
        });

        // Language search filter
        langSearch.addEventListener('input', () => {
            const query = langSearch.value.toLowerCase().trim();
            if (!query) {
                populateLanguageSelect(allLanguages);
                return;
            }
            const filtered = allLanguages.filter(l =>
                l.name.toLowerCase().includes(query) ||
                l.native_name.toLowerCase().includes(query) ||
                l.code.toLowerCase().includes(query)
            );
            populateLanguageSelect(filtered);
        });

        // URL validation on blur
        urlInput.addEventListener('blur', validateUrl);
        urlInput.addEventListener('input', () => {
            urlHint.textContent = '';
        });

        // Form submit
        dubForm.addEventListener('submit', handleSubmit);

        // Retry button
        retryBtn.addEventListener('click', resetForm);
    }

    // ─── URL Validation ────────────────────────────────────────
    function validateUrl() {
        const url = urlInput.value.trim();
        if (!url) return true;

        const ytRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/(watch\?v=|shorts\/)|youtu\.be\/)/;
        if (!ytRegex.test(url)) {
            urlHint.textContent = '⚠️ Please enter a valid YouTube URL';
            return false;
        }
        urlHint.textContent = '';
        return true;
    }

    // ═══════════════════════════════════════════════════════════
    // FORM SUBMISSION
    // ═══════════════════════════════════════════════════════════

    async function handleSubmit(e) {
        e.preventDefault();

        if (!validateUrl()) return;

        const payload = {
            url: urlInput.value.trim(),
            lang: langSelect.value,
            gender: selectedGender,
            gpu: gpuToggle.checked,
            subtitle: subtitleToggle.checked,
        };

        // Update UI to loading state
        submitBtn.disabled = true;
        submitBtn.querySelector('.btn-text').style.display = 'none';
        submitBtn.querySelector('.btn-loading').style.display = 'inline-flex';

        try {
            const res = await fetch('/api/dub', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });

            const data = await res.json();

            if (!res.ok) {
                showError(data.error || 'Failed to start dubbing');
                resetSubmitBtn();
                return;
            }

            currentJobId = data.job_id;
            localStorage.setItem('yt_dub_job_id', currentJobId);
            showProgress(currentJobId);
            startSSE(currentJobId);

        } catch (err) {
            showError('Network error. Is the server running?');
            resetSubmitBtn();
        }
    }

    function resetSubmitBtn() {
        submitBtn.disabled = false;
        submitBtn.querySelector('.btn-text').style.display = 'inline';
        submitBtn.querySelector('.btn-loading').style.display = 'none';
    }

    // ═══════════════════════════════════════════════════════════
    // PROGRESS TRACKING (SSE)
    // ═══════════════════════════════════════════════════════════

    function showProgress(jobId) {
        progressSection.style.display = 'block';
        jobIdLabel.textContent = `Job: ${jobId}`;
        resultSection.style.display = 'none';

        // Reset all stages
        $$('.stage').forEach(s => {
            s.classList.remove('active', 'done');
            s.querySelector('.stage-status').textContent = 'Waiting';
        });

        progressFill.style.width = '0%';
        progressText.textContent = '0%';

        // Smooth scroll to progress
        progressSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function startSSE(jobId) {
        if (eventSource) {
            eventSource.close();
        }

        let retryCount = 0;
        const maxRetries = 5;

        function connect() {
            eventSource = new EventSource(`/api/status/${jobId}`);

            eventSource.onmessage = (event) => {
                try {
                    retryCount = 0; // Reset on success
                    const data = JSON.parse(event.data);
                    updateProgress(data);

                    // Stop SSE if job is done
                    if (data.status === 'complete' || data.status === 'error') {
                        eventSource.close();
                        eventSource = null;
                        stopPolling();
                    }
                } catch (err) {
                    console.error('SSE parse error:', err);
                }
            };

            eventSource.onerror = () => {
                eventSource.close();
                eventSource = null;
                retryCount++;
                if (retryCount <= maxRetries) {
                    console.log(`SSE reconnecting (${retryCount}/${maxRetries})...`);
                    setTimeout(connect, 2000);
                }
            };
        }

        connect();
        startPolling(jobId); // Always run polling as fallback
    }

    // ─── Polling Fallback ──────────────────────────────────────
    let pollTimer = null;

    function startPolling(jobId) {
        stopPolling();
        pollTimer = setInterval(async () => {
            try {
                const res = await fetch(`/api/job/${jobId}`);
                if (res.ok) {
                    const data = await res.json();
                    updateProgress(data);

                    if (data.status === 'complete' || data.status === 'error') {
                        stopPolling();
                        if (eventSource) { eventSource.close(); eventSource = null; }
                    }
                }
            } catch { /* ignore polling errors */ }
        }, 1500);
    }

    function stopPolling() {
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    function updateProgress(data) {
        // Update progress bar
        const pct = data.progress || 0;
        progressFill.style.width = `${pct}%`;
        progressText.textContent = `${pct}%`;

        // Update status message
        if (data.message) {
            statusMessage.textContent = data.message;
        }

        // Update pipeline stages
        const currentStage = data.stage;
        const currentIdx = STAGE_ORDER.indexOf(currentStage);

        $$('.stage').forEach(stageEl => {
            const stageId = stageEl.dataset.stage;
            const stageIdx = STAGE_ORDER.indexOf(stageId);
            const statusEl = stageEl.querySelector('.stage-status');

            stageEl.classList.remove('active', 'done');

            if (stageIdx < currentIdx) {
                stageEl.classList.add('done');
                statusEl.textContent = 'Complete ✓';
            } else if (stageIdx === currentIdx && data.status === 'running') {
                stageEl.classList.add('active');
                statusEl.textContent = 'Processing...';
            }
        });

        // Handle completion
        if (data.status === 'complete') {
            finishSuccess(data);
        } else if (data.status === 'error') {
            finishError(data);
        }
    }

    // ═══════════════════════════════════════════════════════════
    // RESULTS
    // ═══════════════════════════════════════════════════════════

    function finishSuccess(data) {
        if (eventSource) { eventSource.close(); eventSource = null; }
        stopPolling();
        localStorage.removeItem('yt_dub_job_id');

        // Mark all stages as done
        $$('.stage').forEach(s => {
            s.classList.remove('active');
            s.classList.add('done');
            s.querySelector('.stage-status').textContent = 'Complete ✓';
        });

        progressFill.style.width = '100%';
        progressText.textContent = '100%';

        // Show result
        resultSection.style.display = 'block';
        resultSuccess.style.display = 'block';
        resultError.style.display = 'none';
        resultMessage.textContent = data.message || 'Your video has been dubbed successfully!';
        downloadBtn.href = `/api/download/${currentJobId}`;

        resetSubmitBtn();
        resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    function finishError(data) {
        localStorage.removeItem('yt_dub_job_id');
        if (eventSource) { eventSource.close(); eventSource = null; }

        resultSection.style.display = 'block';
        resultSuccess.style.display = 'none';
        resultError.style.display = 'block';
        errorMessage.textContent = data.error || 'An unknown error occurred.';

        resetSubmitBtn();
    }

    function showError(msg) {
        resultSection.style.display = 'block';
        resultSuccess.style.display = 'none';
        resultError.style.display = 'block';
        errorMessage.textContent = msg;
    }

    function resetForm() {
        localStorage.removeItem('yt_dub_job_id');
        currentJobId = null;
        resultSection.style.display = 'none';
        resultSuccess.style.display = 'none';
        resultError.style.display = 'none';
        progressSection.style.display = 'none';
        resetSubmitBtn();
        urlInput.value = '';
        urlInput.focus();
    }

    // ═══════════════════════════════════════════════════════════
    // START
    // ═══════════════════════════════════════════════════════════
    document.addEventListener('DOMContentLoaded', init);

})();
