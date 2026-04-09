/**
 * Çağrı Merkezi Asistanı — Modern Frontend Application
 * =====================================================
 * Web Speech API (STT & TTS), Backend iletişimi,
 * Panel navigasyonu (Sohbet ↔ Takvim),
 * Particle canvas, sidebar, quick actions.
 */

// ============================================================
// YAPILANDIRMA
// ============================================================
const API_URL = window.location.origin + "/api/chat";
const APPOINTMENTS_URL = window.location.origin + "/api/appointments";
const GOOGLE_TTS_API_KEY = "AIzaSyBCyMH48uLM8QN_C9F9xNofsWOE1cuNqbg";

// ============================================================
// DOM ELEMANLARI
// ============================================================
const micButton = document.getElementById("mic-button");
const micIcon = document.getElementById("mic-icon");
const stopIcon = document.getElementById("stop-icon");
const pulseRing1 = document.getElementById("pulse-ring-1");
const pulseRing2 = document.getElementById("pulse-ring-2");
const chatContainer = document.getElementById("chat-container");
const statusBar = document.getElementById("status-bar");
const statusText = document.getElementById("status-text");
const textForm = document.getElementById("text-form");
const textInput = document.getElementById("text-input");
const liveWaveform = document.getElementById("live-waveform");
const sidebar = document.getElementById("sidebar");
const hamburgerBtn = document.getElementById("hamburger-btn");
const sidebarOverlay = document.getElementById("sidebar-overlay");

// Panels
const panelChat = document.getElementById("panel-chat");
const panelCalendar = document.getElementById("panel-calendar");
const navChat = document.getElementById("nav-chat");
const navCalendar = document.getElementById("nav-calendar");
const refreshCalendarBtn = document.getElementById("refresh-calendar");
const goToChatBtn = document.getElementById("go-to-chat-btn");

// ============================================================
// DURUM DEĞİŞKENLERİ
// ============================================================
let isRecording = false;
let recognition = null;
let welcomeShown = true;
let currentPanel = "chat";

// ============================================================
// PARTICLE CANVAS ANIMATION
// ============================================================
(function initParticles() {
    const canvas = document.getElementById("particle-canvas");
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    let particles = [];
    let w, h;

    function resize() {
        w = canvas.width = window.innerWidth;
        h = canvas.height = window.innerHeight;
    }

    function createParticles() {
        particles = [];
        const count = Math.floor((w * h) / 18000);
        for (let i = 0; i < count; i++) {
            particles.push({
                x: Math.random() * w,
                y: Math.random() * h,
                vx: (Math.random() - 0.5) * 0.3,
                vy: (Math.random() - 0.5) * 0.3,
                r: Math.random() * 1.5 + 0.3,
                alpha: Math.random() * 0.4 + 0.1,
            });
        }
    }

    function draw() {
        ctx.clearRect(0, 0, w, h);

        for (let i = 0; i < particles.length; i++) {
            const p = particles[i];
            p.x += p.vx;
            p.y += p.vy;

            if (p.x < 0) p.x = w;
            if (p.x > w) p.x = 0;
            if (p.y < 0) p.y = h;
            if (p.y > h) p.y = 0;

            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(129, 140, 248, ${p.alpha})`;
            ctx.fill();

            for (let j = i + 1; j < particles.length; j++) {
                const p2 = particles[j];
                const dx = p.x - p2.x;
                const dy = p.y - p2.y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(p.x, p.y);
                    ctx.lineTo(p2.x, p2.y);
                    ctx.strokeStyle = `rgba(99, 102, 241, ${0.06 * (1 - dist / 120)})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }

        requestAnimationFrame(draw);
    }

    resize();
    createParticles();
    draw();

    window.addEventListener("resize", () => {
        resize();
        createParticles();
    });
})();

// ============================================================
// PANEL NAVIGATION
// ============================================================
function switchPanel(panelName) {
    currentPanel = panelName;

    // Panels
    panelChat.classList.toggle("hidden", panelName !== "chat");
    panelCalendar.classList.toggle("hidden", panelName !== "calendar");

    // Sidebar active state
    document.querySelectorAll(".sidebar-item").forEach(item => {
        item.classList.toggle("active", item.dataset.panel === panelName);
    });

    // Close mobile sidebar
    sidebar.classList.remove("open");
    hamburgerBtn?.classList.remove("active");
    sidebarOverlay?.classList.remove("active");

    // Load calendar data when switching to calendar
    if (panelName === "calendar") {
        loadAppointments();
    }
}

navChat?.addEventListener("click", () => switchPanel("chat"));
navCalendar?.addEventListener("click", () => switchPanel("calendar"));
goToChatBtn?.addEventListener("click", () => switchPanel("chat"));

// ============================================================
// MOBILE SIDEBAR
// ============================================================
hamburgerBtn?.addEventListener("click", () => {
    sidebar.classList.toggle("open");
    hamburgerBtn.classList.toggle("active");
    sidebarOverlay.classList.toggle("active");
});

sidebarOverlay?.addEventListener("click", () => {
    sidebar.classList.remove("open");
    hamburgerBtn.classList.remove("active");
    sidebarOverlay.classList.remove("active");
});

// ============================================================
// CALENDAR — LOAD APPOINTMENTS
// ============================================================
const MONTHS_TR = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"];

async function loadAppointments() {
    const loadingEl = document.getElementById("calendar-loading");
    const listEl = document.getElementById("calendar-list");
    const emptyEl = document.getElementById("calendar-empty");

    // Show loading, hide others
    loadingEl?.classList.remove("hidden");
    listEl.innerHTML = "";
    emptyEl?.classList.add("hidden");

    try {
        const response = await fetch(APPOINTMENTS_URL);
        const data = await response.json();
        const appointments = data.appointments || [];

        loadingEl?.classList.add("hidden");

        // Backend returned an error message
        if (data.error) {
            console.warn("Calendar API hatası:", data.error);
            listEl.innerHTML = `
                <div class="calendar-empty">
                    <div class="empty-icon">📅</div>
                    <h3>Takvim Bağlantısı Kurulamadı</h3>
                    <p>Google Calendar'a bağlanırken bir sorun oluştu. Sunucuyu yeniden başlatıp Google hesabınızla giriş yapmanız gerekebilir.</p>
                    <p style="font-size:11px; color:var(--text-dim); margin-top:8px; font-family:'JetBrains Mono',monospace;">${escapeHtml(data.error)}</p>
                </div>
            `;
            return;
        }

        if (appointments.length === 0) {
            emptyEl?.classList.remove("hidden");
            return;
        }

        appointments.forEach((appt, index) => {
            const card = createAppointmentCard(appt, index);
            listEl.appendChild(card);
        });

    } catch (err) {
        console.error("Randevu yükleme hatası:", err);
        loadingEl?.classList.add("hidden");
        listEl.innerHTML = `
            <div class="calendar-empty">
                <div class="empty-icon">⚠️</div>
                <h3>Bağlantı Hatası</h3>
                <p>Sunucuya ulaşılamadı. Uygulamanın çalıştığından emin olun.</p>
            </div>
        `;
    }
}

function createAppointmentCard(appt, index) {
    const card = document.createElement("div");
    card.className = "appointment-card";
    card.style.animationDelay = `${index * 0.08}s`;

    // Parse date
    let dayStr = "--";
    let monthStr = "";
    let timeStr = "";

    if (appt.start) {
        const dt = new Date(appt.start);
        dayStr = dt.getDate();
        monthStr = MONTHS_TR[dt.getMonth()];
        const endDt = appt.end ? new Date(appt.end) : null;
        const startTime = dt.toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" });
        const endTime = endDt ? endDt.toLocaleTimeString("tr-TR", { hour: "2-digit", minute: "2-digit" }) : "";
        timeStr = endTime ? `${startTime} — ${endTime}` : startTime;
    }

    const statusClass = appt.status === "cancelled" ? "cancelled" : "confirmed";
    const statusLabel = appt.status === "cancelled" ? "İptal" : "Aktif";

    card.innerHTML = `
        <div class="appt-date-badge">
            <span class="appt-day">${dayStr}</span>
            <span class="appt-month">${monthStr}</span>
        </div>
        <div class="appt-info">
            <div class="appt-title">${escapeHtml(appt.title)}</div>
            <div class="appt-time">
                <svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                ${timeStr}
            </div>
            ${appt.description ? `<div class="appt-desc">${escapeHtml(appt.description)}</div>` : ""}
            ${appt.link ? `<a class="appt-link" href="${appt.link}" target="_blank">Google Calendar'da Aç →</a>` : ""}
        </div>
        <span class="appt-status ${statusClass}">${statusLabel}</span>
    `;

    return card;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

refreshCalendarBtn?.addEventListener("click", () => loadAppointments());

// ============================================================
// WEB SPEECH API — STT (Ses -> Metin)
// ============================================================
function initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
        setStatus("Tarayıcınız ses tanımayı desteklemiyor. Chrome kullanmayı deneyin.", "error");
        micButton.disabled = true;
        micButton.style.opacity = "0.5";
        return null;
    }

    const rec = new SpeechRecognition();
    rec.lang = "tr-TR";
    rec.continuous = false;
    rec.interimResults = false;
    rec.maxAlternatives = 1;

    rec.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        console.log("🎤 Tanınan:", transcript);
        stopRecording();
        addMessage(transcript, "user");
        sendToBackend(transcript);
    };

    rec.onerror = (event) => {
        console.error("STT Hatası:", event.error);
        stopRecording();

        if (event.error === "no-speech") {
            setStatus("Ses algılanamadı, tekrar deneyin.", "error");
        } else if (event.error === "not-allowed") {
            setStatus("Mikrofon izni verilmedi.", "error");
        } else {
            setStatus(`Ses tanıma hatası: ${event.error}`, "error");
        }
    };

    rec.onend = () => {
        if (isRecording) stopRecording();
    };

    return rec;
}

// ============================================================
// KAYIT KONTROL
// ============================================================
function startRecording() {
    if (!recognition) {
        recognition = initSpeechRecognition();
        if (!recognition) return;
    }

    isRecording = true;
    recognition.start();

    micButton.classList.add("recording");
    micIcon.classList.add("hidden");
    stopIcon.classList.remove("hidden");
    pulseRing1.classList.remove("hidden");
    pulseRing2.classList.remove("hidden");
    liveWaveform?.classList.add("active");
    setStatus("🎙️ Dinliyorum... Buyurun, sizi dinliyorum.", "listening");
}

function stopRecording() {
    isRecording = false;

    try { recognition?.stop(); } catch (e) {}

    micButton.classList.remove("recording");
    micIcon.classList.remove("hidden");
    stopIcon.classList.add("hidden");
    pulseRing1.classList.add("hidden");
    pulseRing2.classList.add("hidden");
    liveWaveform?.classList.remove("active");
}

// ============================================================
// BACKEND İLETİŞİMİ
// ============================================================
async function sendToBackend(message) {
    // If on calendar panel, switch to chat first
    if (currentPanel !== "chat") switchPanel("chat");

    removeWelcome();
    setStatus("⏳ Düşünüyorum...", "processing");

    const thinkingId = addThinkingBubble();

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message }),
        });

        if (!response.ok) throw new Error(`Sunucu hatası: ${response.status}`);

        const data = await response.json();
        let aiResponse = data.response;

        // Google Calendar link extraction
        let extractedUrl = null;
        const urlRegex = /(https:\/\/www\.google\.com\/calendar\/event\?eid=[^\s]+)/g;
        const urls = aiResponse.match(urlRegex);

        if (urls && urls.length > 0) {
            extractedUrl = urls[0];
            aiResponse = aiResponse.replace(urlRegex, "").trim();
        }

        removeThinkingBubble(thinkingId);
        addMessage(aiResponse, "ai", extractedUrl);
        speakText(aiResponse);

    } catch (error) {
        console.error("Backend hatası:", error);
        removeThinkingBubble(thinkingId);
        addMessage("Bağlantı hatası oluştu. Sunucunun çalıştığından emin olun!", "ai");
        setStatus("Bağlantı hatası!", "error");
    }
}

// ============================================================
// TTS — GOOGLE CLOUD WAVENET
// ============================================================
let currentAudio = null;

async function speakText(text) {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
    }

    setStatus("🔊 Konuşuyorum...", "speaking");
    liveWaveform?.classList.add("active");

    try {
        const response = await fetch(`https://texttospeech.googleapis.com/v1/text:synthesize?key=${GOOGLE_TTS_API_KEY}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                input: { text: text },
                voice: { languageCode: 'tr-TR', name: 'tr-TR-Wavenet-C' },
                audioConfig: { audioEncoding: 'MP3', pitch: 0.0, speakingRate: 1.05 }
            })
        });

        if (!response.ok) {
            console.error("Google TTS Hatasi:", await response.text());
            setStatus("Ses sentezlenemedi.", "error");
            liveWaveform?.classList.remove("active");
            return;
        }

        const data = await response.json();
        const audioSrc = 'data:audio/mp3;base64,' + data.audioContent;

        currentAudio = new Audio(audioSrc);

        currentAudio.onended = () => {
            setStatus("Mikrofona basarak veya yazarak konuşmaya başlayın", "");
            liveWaveform?.classList.remove("active");
        };

        currentAudio.play();

    } catch (e) {
        console.error("TTS Bağlantı Hatası:", e);
        setStatus("Ses bağlantı hatası", "error");
        liveWaveform?.classList.remove("active");
    }
}

// ============================================================
// SOHBET MESAJLARI
// ============================================================
function removeWelcome() {
    if (welcomeShown) {
        const welcome = chatContainer.querySelector(".chat-welcome");
        if (welcome) {
            welcome.style.transition = "opacity 0.3s, transform 0.3s";
            welcome.style.opacity = "0";
            welcome.style.transform = "translateY(-10px)";
            setTimeout(() => welcome.remove(), 300);
        }
        welcomeShown = false;
    }
}

function addMessage(text, sender, link = null) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${sender === "user" ? "user-bubble" : "ai-bubble"}`;

    const avatar = document.createElement("div");
    avatar.className = "bubble-avatar";
    avatar.textContent = sender === "user" ? "👤" : "📞";

    const content = document.createElement("div");
    content.className = "bubble-content";

    const p = document.createElement("p");
    p.textContent = text;
    content.appendChild(p);

    if (link) {
        const linkBtn = document.createElement("a");
        linkBtn.href = link;
        linkBtn.target = "_blank";
        linkBtn.className = "bubble-link-btn";
        linkBtn.innerHTML = `📅 Takvime Git <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>`;
        content.appendChild(linkBtn);
    }

    bubble.appendChild(avatar);
    bubble.appendChild(content);

    chatContainer.appendChild(bubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addThinkingBubble() {
    const id = "thinking-" + Date.now();
    const bubble = document.createElement("div");
    bubble.className = "chat-bubble ai-bubble";
    bubble.id = id;

    const avatar = document.createElement("div");
    avatar.className = "bubble-avatar";
    avatar.textContent = "📞";

    const content = document.createElement("div");
    content.className = "bubble-content";
    content.innerHTML = `
        <div class="thinking-dots">
            <span></span><span></span><span></span>
        </div>
    `;

    bubble.appendChild(avatar);
    bubble.appendChild(content);
    chatContainer.appendChild(bubble);
    chatContainer.scrollTop = chatContainer.scrollHeight;

    return id;
}

function removeThinkingBubble(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// ============================================================
// DURUM ÇUBUĞU
// ============================================================
function setStatus(text, state) {
    statusText.textContent = text;
    statusBar.className = "status-bar";
    if (state) statusBar.classList.add(state);
}

// ============================================================
// QUICK ACTIONS
// ============================================================
document.querySelectorAll(".quick-btn[data-msg]").forEach(btn => {
    btn.addEventListener("click", () => {
        const msg = btn.getAttribute("data-msg");
        if (msg) {
            addMessage(msg, "user");
            sendToBackend(msg);
        }
    });
});

// ============================================================
// OLAY DİNLEYİCİLER
// ============================================================

// Mikrofon
micButton.addEventListener("click", () => {
    if (isRecording) {
        stopRecording();
        setStatus("Mikrofona basarak veya yazarak konuşmaya başlayın", "");
    } else {
        startRecording();
    }
});

// Metin Formu
textForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const message = textInput.value.trim();
    if (!message) return;

    addMessage(message, "user");
    textInput.value = "";
    sendToBackend(message);
});

// Enter tuşu
textInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        textForm.dispatchEvent(new Event("submit"));
    }
});

// Sayfa yüklendiğinde
window.addEventListener("load", () => {
    console.log("📞 Çağrı Merkezi Asistanı — Modern UI hazır!");
});
