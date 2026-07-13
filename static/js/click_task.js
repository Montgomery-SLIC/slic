/**
 * SLIC Click Task - ported from Rails inline HAML JavaScript.
 *
 * Key fix vs Rails version: navigation happens in req.onload (not setTimeout)
 * to prevent data loss under load.
 *
 * Expects the following data attributes on #click-task-data:
 *   data-participant-id
 *   data-click-task-id
 *   data-calibration ("true"/"false")
 *   data-transcript (full EAF XML string, empty string if calibration)
 *   data-next-url
 *   data-audio-url
 *   data-prompt
 *   data-explanation-prompt
 */

'use strict';

// ── CSRF helper ──────────────────────────────────────────────────────────────

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
}

// ── State ────────────────────────────────────────────────────────────────────

let clickTimes = [];
let annotations = [];
let audioEl = null;
let isCalibration = false;
let participantId = null;
let clickTaskId = null;
let nextUrl = null;
let explanationPrompt = '';
let listenCount = 0;

// ── EAF parsing (matches JS behaviour in Rails exactly) ──────────────────────

function loadTranscript(xmlString) {
    if (!xmlString) return;
    try {
        const parser = new DOMParser();
        const doc = parser.parseFromString(xmlString, 'application/xml');

        // Build TIME_SLOT_ID → TIME_VALUE (ms) map
        const slots = {};
        doc.querySelectorAll('TIME_ORDER TIME_SLOT').forEach(slot => {
            slots[slot.getAttribute('TIME_SLOT_ID')] = parseInt(slot.getAttribute('TIME_VALUE'), 10);
        });

        // Prefer TIER[1] over TIER[0] (matches Rails)
        const tiers = doc.querySelectorAll('TIER');
        const tier = tiers.length > 1 ? tiers[1] : tiers[0];
        if (!tier) return;

        tier.querySelectorAll('ANNOTATION ALIGNABLE_ANNOTATION').forEach(ann => {
            const start = slots[ann.getAttribute('TIME_SLOT_REF1')];
            const end = slots[ann.getAttribute('TIME_SLOT_REF2')];
            const valueEl = ann.querySelector('ANNOTATION_VALUE');
            if (start == null || end == null || !valueEl) return;
            annotations.push({
                start_ms: start,
                end_ms: end,
                text: (valueEl.textContent || '').trim(),
            });
        });

        annotations.sort((a, b) => a.start_ms - b.start_ms);
    } catch (e) {
        console.warn('EAF parse error:', e);
    }
}

// ── SingleClickAudioManager ───────────────────────────────────────────────────

class SingleClickAudioManager {
    /**
     * @param {number} clickTime - audio position in seconds when participant clicked
     * @param {number} duration  - total audio duration in seconds
     * @param {number} index     - loop index (used for input IDs)
     */
    constructor(clickTime, duration, index) {
        this.clickTime = clickTime;
        this.duration = duration;
        this.index = index;
        this.start = Math.max(0, clickTime - 4);
        this.end = Math.min(duration, clickTime + 1);
        this.playing = false;
        this._buildAnnotationWindow();
    }

    _buildAnnotationWindow() {
        const startMs = this.start * 1000;
        const endMs = this.end * 1000;
        const clickMs = this.clickTime * 1000;

        this.windowAnnotations = annotations.filter(
            a => a.end_ms > startMs && a.start_ms < endMs
        );

        // Find the annotation covering the click moment
        this.clickedWord = null;
        for (const ann of this.windowAnnotations) {
            if (ann.start_ms <= clickMs && ann.end_ms >= clickMs) {
                this.clickedWord = ann;
                break;
            }
        }
        if (!this.clickedWord && this.windowAnnotations.length) {
            // Nearest annotation if no exact match
            let nearest = this.windowAnnotations[0];
            let minDist = Math.abs(nearest.start_ms - clickMs);
            for (const ann of this.windowAnnotations) {
                const d = Math.abs(ann.start_ms - clickMs);
                if (d < minDist) { minDist = d; nearest = ann; }
            }
            this.clickedWord = nearest;
        }
    }

    render(container) {
        const i = this.index;
        const div = document.createElement('div');
        div.className = 'click-review-item border rounded p-3 mb-3';
        div.innerHTML = `
            <div class="d-flex align-items-center mb-2">
                <button type="button" class="btn btn-sm btn-outline-secondary mr-2 replay-btn" data-index="${i}">
                    &#9654; Replay
                </button>
                <small class="text-muted">Click at ${this.clickTime.toFixed(2)}s</small>
            </div>
            <div class="transcript-window mb-2 font-monospace small bg-light p-2 rounded">${this._buildTranscriptHtml()}</div>
            <div class="mb-2">
                <label class="form-label small">${explanationPrompt || 'Why did you click?'}</label>
                <textarea class="form-control form-control-sm click-explanation" id="text_field_${i}" rows="2" placeholder="Describe what you noticed..."></textarea>
            </div>
            <div class="form-check form-check-inline">
                <input type="checkbox" class="form-check-input accident-cb" id="accident_checkbox_${i}">
                <label class="form-check-label small" for="accident_checkbox_${i}">I clicked by accident</label>
            </div>
            <div class="form-check form-check-inline">
                <input type="checkbox" class="form-check-input dontknow-cb" id="dontknow_checkbox_${i}">
                <label class="form-check-label small" for="dontknow_checkbox_${i}">I don't know why I clicked</label>
            </div>
            <div class="validation-msg text-danger small mt-1" id="validation_${i}" style="display:none;">Please explain your click or tick a checkbox.</div>
        `;
        container.appendChild(div);

        // Replay button
        div.querySelector('.replay-btn').addEventListener('click', () => this._replay());

        // Mutual exclusion for checkboxes
        const accidentCb = div.querySelector(`#accident_checkbox_${i}`);
        const dontknowCb = div.querySelector(`#dontknow_checkbox_${i}`);
        const textField = div.querySelector(`#text_field_${i}`);

        accidentCb.addEventListener('change', () => {
            if (accidentCb.checked) { dontknowCb.checked = false; textField.disabled = true; }
            else { textField.disabled = false; }
        });
        dontknowCb.addEventListener('change', () => {
            if (dontknowCb.checked) { accidentCb.checked = false; textField.disabled = true; }
            else { textField.disabled = false; }
        });
    }

    _buildTranscriptHtml() {
        if (!this.windowAnnotations.length) return '<em class="text-muted">[no transcript]</em>';
        return this.windowAnnotations.map(ann => {
            const isClicked = ann === this.clickedWord;
            const word = escapeHtml(ann.text);
            if (isClicked) {
                return `<span class="clicked-word fw-bold text-primary" title="You clicked here">${word}<br><span style="color:var(--bs-primary)">^</span></span>`;
            }
            return `<span>${word}</span>`;
        }).join(' ');
    }

    _replay() {
        if (this.playing) return;
        this.playing = true;
        audioEl.currentTime = this.start;
        audioEl.play();
        const stop = () => {
            if (audioEl.currentTime >= this.end) {
                audioEl.pause();
                this.playing = false;
                audioEl.removeEventListener('timeupdate', stop);
            }
        };
        audioEl.addEventListener('timeupdate', stop);
    }

    collect() {
        const i = this.index;
        const accidentCb = document.getElementById(`accident_checkbox_${i}`);
        const dontknowCb = document.getElementById(`dontknow_checkbox_${i}`);
        const textField = document.getElementById(`text_field_${i}`);
        const validMsg = document.getElementById(`validation_${i}`);

        let answer = '';
        let fromCheckbox = false;

        if (accidentCb && accidentCb.checked) {
            answer = 'accident';
            fromCheckbox = true;
        } else if (dontknowCb && dontknowCb.checked) {
            answer = 'dontknow';
            fromCheckbox = true;
        } else {
            answer = (textField ? textField.value : '').trim();
            if (!answer) {
                if (validMsg) validMsg.style.display = '';
                return null; // validation failure
            }
        }
        if (validMsg) validMsg.style.display = 'none';

        return {
            time: this.clickTime,
            answer,
            from_checkbox: fromCheckbox,
            no_clicks_explanation: false,
            participant_id: participantId,
            click_task_id: clickTaskId,
        };
    }
}

// ── Canvas progress bar ───────────────────────────────────────────────────────

function updateBar() {
    const canvas = document.getElementById('progress');
    if (!canvas || !audioEl) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    const pct = audioEl.duration ? audioEl.currentTime / audioEl.duration : 0;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#dee2e6';
    ctx.fillRect(0, h / 2 - 4, w, 8);
    ctx.fillStyle = '#0d6efd';
    ctx.fillRect(0, h / 2 - 4, w * pct, 8);
    // Click markers
    clickTimes.forEach(t => {
        const x = (t / audioEl.duration) * w;
        ctx.fillStyle = '#dc3545';
        ctx.fillRect(x - 2, h / 2 - 10, 4, 20);
    });

    if (audioEl.ended || (audioEl.duration && audioEl.currentTime >= audioEl.duration - 0.05)) {
        onAudioEnd();
    }
}

// ── Audio end handler ─────────────────────────────────────────────────────────

let audioEndHandled = false;

function onAudioEnd() {
    if (audioEndHandled) return;
    audioEndHandled = true;

    document.getElementById('click-btn-container').style.display = 'none';

    if (isCalibration) {
        sendAllResponses(clickTimes.map(t => ({
            time: t, answer: '', from_checkbox: false,
            no_clicks_explanation: false,
            participant_id: participantId, click_task_id: clickTaskId,
        })));
        return;
    }

    if (clickTimes.length === 0) {
        displayNoClicksUI();
        return;
    }

    displayClickReview();
}

// ── No-clicks UI ─────────────────────────────────────────────────────────────

function displayNoClicksUI() {
    const container = document.getElementById('review-container');
    container.innerHTML = `
        <p class="mb-3">You didn't click during this audio clip. Please explain why:</p>
        <textarea id="no-click-explanation" class="form-control mb-3" rows="3"
                  placeholder="I didn't notice any accent features..."></textarea>
        <button type="button" class="btn btn-primary" id="no-click-submit">Continue</button>
    `;
    container.style.display = '';

    document.getElementById('no-click-submit').addEventListener('click', () => {
        const answer = document.getElementById('no-click-explanation').value.trim();
        sendAllResponses([{
            time: null, answer, from_checkbox: false,
            no_clicks_explanation: true,
            participant_id: participantId, click_task_id: clickTaskId,
        }]);
    });
}

// ── Click review UI ───────────────────────────────────────────────────────────

let managers = [];

function displayClickReview() {
    const container = document.getElementById('review-container');
    container.innerHTML = `<p class="mb-3">You clicked ${clickTimes.length} time${clickTimes.length !== 1 ? 's' : ''}. For each click, tell us what you noticed:</p>`;
    container.style.display = '';

    managers = clickTimes.map((t, i) => {
        const m = new SingleClickAudioManager(t, audioEl.duration, i);
        m.render(container);
        return m;
    });

    const submitBtn = document.createElement('button');
    submitBtn.type = 'button';
    submitBtn.className = 'btn btn-primary mt-3';
    submitBtn.textContent = 'Submit and continue';
    submitBtn.addEventListener('click', collectAndSend);
    container.appendChild(submitBtn);
}

function collectAndSend() {
    const responses = [];
    for (const m of managers) {
        const r = m.collect();
        if (r === null) return; // validation failed
        responses.push(r);
    }
    sendAllResponses(responses);
}

// ── XHR submission (fix: navigate in onload, not setTimeout) ─────────────────

function sendAllResponses(responses) {
    const submitBtn = document.querySelector('#review-container .btn-primary');
    if (submitBtn) { submitBtn.disabled = true; submitBtn.textContent = 'Saving...'; }

    const req = new XMLHttpRequest();
    req.open('POST', '/click-responses/');
    req.setRequestHeader('X-CSRFToken', getCookie('csrftoken'));
    req.setRequestHeader('Content-Type', 'application/json');

    // Fallback: navigate anyway after 5s if onload doesn't fire
    const fallback = setTimeout(() => { window.location.href = nextUrl; }, 5000);
    req.onload = function () {
        clearTimeout(fallback);
        window.location.href = nextUrl;
    };
    req.onerror = function () {
        clearTimeout(fallback);
        window.location.href = nextUrl;
    };

    req.send(JSON.stringify(responses));
}

// ── Utility ───────────────────────────────────────────────────────────────────

function escapeHtml(text) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}

// ── Init ──────────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    const dataEl = document.getElementById('click-task-data');
    if (!dataEl) return;

    participantId = parseInt(dataEl.dataset.participantId, 10);
    clickTaskId = parseInt(dataEl.dataset.clickTaskId, 10);
    isCalibration = dataEl.dataset.calibration === 'true';
    nextUrl = dataEl.dataset.nextUrl;
    explanationPrompt = dataEl.dataset.explanationPrompt || '';

    // Load EAF transcript (only if not calibration)
    if (!isCalibration) {
        loadTranscript(dataEl.dataset.transcript || '');
    }

    // Set up audio element
    audioEl = document.getElementById('click-audio');
    if (!audioEl) return;

    audioEl.addEventListener('timeupdate', updateBar);

    // Click button
    const clickBtn = document.getElementById('click-btn');
    if (clickBtn) {
        clickBtn.addEventListener('click', () => {
            if (audioEl.paused || audioEl.ended) return;
            clickTimes.push(audioEl.currentTime);
            updateBar();
        });
    }

    // Audio control button
    const audioControl = document.getElementById('audio-control');
    if (audioControl) {
        audioControl.addEventListener('click', () => {
            if (audioEl.paused) {
                audioEl.play();
                audioControl.textContent = 'Pause';
            } else {
                audioEl.pause();
                audioControl.textContent = 'Play';
            }
        });
        audioEl.addEventListener('ended', () => { audioControl.textContent = 'Play'; });
    }
});
