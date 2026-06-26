const baseUrl = "http://127.0.0.1:8000/api";
const tokenKey = "ai-lecture-access-token";

function getFileMeta(fileName) {
  const ext = (fileName || "").split('.').pop().toLowerCase();
  if (ext === 'pdf') {
    return {
      icon: 'fa-file-pdf',
      colorClass: 'file-pdf-color',
      isDoc: true
    };
  } else if (['png', 'jpg', 'jpeg'].includes(ext)) {
    return {
      icon: 'fa-file-image',
      colorClass: 'file-image-color',
      isDoc: true
    };
  } else {
    return {
      icon: 'fa-file-audio',
      colorClass: 'file-audio-color',
      isDoc: false
    };
  }
}

// State
let currentUser = null;
let activeLecture = null;
let activeTab = "dashboard-view";

// Quiz State
let quizQuestions = [];
let currentQuizIndex = 0;
let quizScore = 0;
let canSelectOption = true;

// Flashcard State
let flashcards = [];
let currentCardIndex = 0;

// DOM Elements
const authScreen = document.getElementById("auth-screen");
const viewsContainer = document.getElementById("views-container");
const toast = document.getElementById("toast-notification");
const sidebar = document.getElementById("sidebar");

// User displays
const profileName = document.getElementById("profile-name");
const profileEmail = document.getElementById("profile-email");
const authStatus = document.getElementById("auth-status");

// Navigation
const navDashboard = document.getElementById("nav-dashboard");
const navStudy = document.getElementById("nav-study");
const navChat = document.getElementById("nav-chat");

// Dashboard Elements
const dropzone = document.getElementById("dropzone");
const uploadFile = document.getElementById("upload-file");
const selectedFileArea = document.getElementById("selected-file-area");
const selectedFileName = document.getElementById("selected-file-name");
const selectedFileSize = document.getElementById("selected-file-size");
const btnClearFile = document.getElementById("btn-clear-file");
const uploadBtn = document.getElementById("upload-btn");
const historyRefreshBtn = document.getElementById("history-refresh-btn");
const lectureHistoryGrid = document.getElementById("lecture-history");

// Search
const searchInput = document.getElementById("search-query");
const searchBtn = document.getElementById("search-btn");
const semanticSearchBtn = document.getElementById("semantic-search-btn");

// Study View Elements
const studyLectureTitle = document.getElementById("study-lecture-title");
const studyLectureIdBadge = document.getElementById("study-lecture-id");
const studyLectureTopicBadge = document.getElementById("study-lecture-topic");

const transcribeBtn = document.getElementById("transcribe-btn");
const summaryBtn = document.getElementById("summary-btn");
const quizBtn = document.getElementById("quiz-btn");
const quizDifficulty = document.getElementById("quiz-difficulty");
const flashcardsBtn = document.getElementById("flashcards-btn");

const getTranscriptBtn = document.getElementById("get-transcript-btn");
const getNotesBtn = document.getElementById("get-notes-btn");
const getQuizBtn = document.getElementById("get-quiz-btn");
const getFlashcardsBtn = document.getElementById("get-flashcards-btn");

const studyTranscriptText = document.getElementById("study-transcript-text");
const studySummaryText = document.getElementById("study-summary-text");
const studyKeyPoints = document.getElementById("study-key-points");

// Flashcards Deck
const flashcardCard = document.getElementById("flashcard-card");
const cardQuestion = document.getElementById("card-question");
const cardAnswer = document.getElementById("card-answer");
const cardPrevBtn = document.getElementById("card-prev-btn");
const cardNextBtn = document.getElementById("card-next-btn");
const cardIndicator = document.getElementById("card-indicator");

// Quiz Player
const quizReadyScreen = document.getElementById("quiz-ready-screen");
const quizPlayScreen = document.getElementById("quiz-play-screen");
const quizResultsScreen = document.getElementById("quiz-results-screen");
const quizProgressFill = document.getElementById("quiz-progress-fill");
const quizQIndex = document.getElementById("quiz-q-index");
const quizQScore = document.getElementById("quiz-q-score");
const quizQuestionText = document.getElementById("quiz-question-text");
const quizOptionsList = document.getElementById("quiz-options-list");
const quizSubmitNextBtn = document.getElementById("quiz-submit-next-btn");
const startQuizBtn = document.getElementById("start-quiz-btn");
const quizRestartBtn = document.getElementById("quiz-restart-btn");

// Mindmap
const mindmapContainer = document.getElementById("mindmap-container");

// Chat
const chatLectureSelect = document.getElementById("chat-lecture-select");
const useRagCheckbox = document.getElementById("use-rag");
const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const chatQuestionInput = document.getElementById("chat-question");

// Token Utilities
function getToken() {
  return localStorage.getItem(tokenKey) || "";
}

function setToken(token) {
  localStorage.setItem(tokenKey, token);
}

function clearToken() {
  localStorage.removeItem(tokenKey);
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

// Toast System
function showToast(message, type = "info") {
  toast.textContent = message;
  toast.className = `toast-notification ${type}`;
  toast.style.display = "block";
  setTimeout(() => {
    toast.style.display = "none";
  }, 4000);
}

// HTTP Client
async function fetchJson(path, options = {}) {
  const headers = {
    ...(options.headers || {}),
    ...authHeaders(),
  };
  const response = await fetch(`${baseUrl}${path}`, { ...options, headers });
  const text = await response.text();
  let data;
  try {
    data = text ? JSON.parse(text) : null;
  } catch (err) {
    data = text;
  }
  if (!response.ok) {
    const msg = data?.detail || data?.message || data || response.statusText || "Request failed";
    throw new Error(msg);
  }
  return data;
}

// Views Navigation
function switchView(viewId) {
  if (!currentUser && viewId !== "auth-screen") {
    showToast("Please log in first", "error");
    return;
  }
  
  // Update view state
  activeTab = viewId;
  document.querySelectorAll(".view").forEach(v => v.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(item => item.classList.remove("active"));
  
  const targetView = document.getElementById(viewId);
  if (targetView) targetView.classList.add("active");
  
  // Highlight sidebar item
  if (viewId === "dashboard-view") navDashboard.classList.add("active");
  if (viewId === "study-view") navStudy.classList.add("active");
  if (viewId === "chat-view") navChat.classList.add("active");
  
  // Title adjustments
  const pageTitle = document.getElementById("page-title");
  const pageSubtitle = document.getElementById("page-subtitle");
  if (viewId === "dashboard-view") {
    pageTitle.textContent = "Dashboard";
    pageSubtitle.textContent = "Upload lectures, search transcripts, and generate study resources.";
  } else if (viewId === "study-view") {
    pageTitle.textContent = "Study Center";
    pageSubtitle.textContent = "Review transcripts, summaries, flashcards, and practice quizzes.";
  } else if (viewId === "chat-view") {
    pageTitle.textContent = "AI Study Assistant";
    pageSubtitle.textContent = "Ask anything about your lecture series. Powered by semantic search.";
  }
}

// Profile Loader
async function fetchCurrentUser() {
  const token = getToken();
  if (!token) {
    authScreen.classList.remove("hidden");
    viewsContainer.style.display = "none";
    sidebar.style.display = "none";
    return;
  }

  try {
    currentUser = await fetchJson("/auth/me", { method: "GET" });
    profileName.textContent = currentUser.name;
    profileEmail.textContent = currentUser.email;
    authScreen.classList.add("hidden");
    viewsContainer.style.display = "flex";
    sidebar.style.display = "flex";
    showToast(`Welcome back, ${currentUser.name}!`, "success");
    
    // Load initial data
    await loadHistory();
  } catch (err) {
    clearToken();
    currentUser = null;
    authScreen.classList.remove("hidden");
    viewsContainer.style.display = "none";
    sidebar.style.display = "none";
    showToast(`Session expired: ${err.message}`, "error");
  }
}

// Authentication Forms
async function handleLogin(event) {
  event.preventDefault();
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;
  
  authStatus.textContent = "Logging in...";
  const body = new URLSearchParams();
  body.append("username", email);
  body.append("password", password);
  
  try {
    const data = await fetchJson("/auth/token", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: body.toString(),
    });
    setToken(data.access_token);
    authStatus.textContent = "";
    await fetchCurrentUser();
  } catch (err) {
    authStatus.textContent = `Login failed: ${err.message}`;
    showToast(err.message, "error");
  }
}

async function handleRegister(event) {
  event.preventDefault();
  const name = document.getElementById("register-name").value.trim();
  const email = document.getElementById("register-email").value.trim();
  const password = document.getElementById("register-password").value;
  
  authStatus.textContent = "Creating account...";
  
  try {
    const data = await fetchJson("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
    });
    setToken(data.access_token);
    authStatus.textContent = "";
    await fetchCurrentUser();
  } catch (err) {
    authStatus.textContent = `Registration failed: ${err.message}`;
    showToast(err.message, "error");
  }
}

function handleLogout() {
  clearToken();
  currentUser = null;
  activeLecture = null;
  navStudy.setAttribute("disabled", "true");
  authScreen.classList.remove("hidden");
  viewsContainer.style.display = "none";
  sidebar.style.display = "none";
  showToast("Logged out successfully");
}

// Drag & Drop Upload
function setupDragAndDrop() {
  ["dragenter", "dragover"].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    }, false);
  });

  ["dragleave", "drop"].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    }, false);
  });

  dropzone.addEventListener("drop", (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length) {
      uploadFile.files = files;
      updateFileSelectionDisplay(files[0]);
    }
  });

  dropzone.addEventListener("click", () => {
    uploadFile.click();
  });

  uploadFile.addEventListener("change", (e) => {
    if (e.target.files.length) {
      updateFileSelectionDisplay(e.target.files[0]);
    }
  });

  btnClearFile.addEventListener("click", (e) => {
    e.stopPropagation();
    resetUploadState();
  });
}

function updateFileSelectionDisplay(file) {
  selectedFileName.textContent = file.name;
  const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
  selectedFileSize.textContent = `${sizeMB} MB`;
  
  const selectedFileIcon = selectedFileArea.querySelector(".file-icon-badge i");
  if (selectedFileIcon) {
    const meta = getFileMeta(file.name);
    selectedFileIcon.className = `fa-solid ${meta.icon}`;
    if (meta.icon === 'fa-file-pdf') {
      selectedFileIcon.style.color = '#e74c3c';
    } else if (meta.icon === 'fa-file-image') {
      selectedFileIcon.style.color = '#00bcd4';
    } else {
      selectedFileIcon.style.color = '#3f51b5';
    }
  }

  dropzone.style.display = "none";
  selectedFileArea.style.display = "flex";
  uploadBtn.removeAttribute("disabled");
}

function resetUploadState() {
  uploadFile.value = "";
  selectedFileArea.style.display = "none";
  dropzone.style.display = "block";
  uploadBtn.setAttribute("disabled", "true");
}

async function handleUpload(event) {
  event.preventDefault();
  const file = uploadFile.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  uploadBtn.setAttribute("disabled", "true");
  uploadBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Uploading...`;
  showToast("Uploading file...", "info");

  try {
    const response = await fetchJson("/upload", {
      method: "POST",
      body: formData,
    });
    showToast("Upload completed successfully!", "success");
    resetUploadState();
    await loadHistory();
    // Open the new lecture immediately
    await openLecture(response.lecture_id);
  } catch (err) {
    showToast(`Upload failed: ${err.message}`, "error");
    uploadBtn.removeAttribute("disabled");
    uploadBtn.innerHTML = `Upload Lecture <i class="fa-solid fa-arrow-up-from-bracket"></i>`;
  }
}

// History & Library
async function loadHistory() {
  lectureHistoryGrid.innerHTML = `
    <div class="loading-state">
      <i class="fa-solid fa-spinner fa-spin"></i> Loading library lectures...
    </div>
  `;
  
  try {
    const lectures = await fetchJson("/history", { method: "GET" });
    lectureHistoryGrid.innerHTML = "";
    chatLectureSelect.innerHTML = `<option value="">Latest uploaded lecture</option>`;

    // Dynamic stats computation
    const totalLecs = Array.isArray(lectures) ? lectures.length : 0;
    const totalNotes = Array.isArray(lectures) ? lectures.filter(l => l.status === 'summarized' || l.status === 'quiz_generated' || l.status === 'flashcards_generated').length : 0;
    const totalQuizzes = Array.isArray(lectures) ? lectures.filter(l => l.status === 'quiz_generated').length : 0;
    
    document.getElementById("stat-total-lectures").textContent = totalLecs;
    document.getElementById("stat-notes-generated").textContent = totalNotes;
    document.getElementById("stat-quizzes-taken").textContent = totalQuizzes;

    if (!Array.isArray(lectures) || lectures.length === 0) {
      lectureHistoryGrid.innerHTML = `
        <div class="empty-state">
          <i class="fa-solid fa-folder-open" style="font-size: 2rem; margin-bottom: 12px; display: block;"></i>
          No lectures uploaded yet. Drop an audio file to begin.
        </div>
      `;
      return;
    }

    // Sort by date desc
    lectures.sort((a, b) => new Date(b.upload_date) - new Date(a.upload_date));

    lectures.forEach(lec => {
      // Append to list
      const card = document.createElement("div");
      card.className = "lecture-card-item";
      
      const uploadDateFormatted = new Date(lec.upload_date).toLocaleString();
      const topicTag = lec.topic ? `<span class="badge topic-tag">${lec.topic}</span>` : "";
      
      const meta = getFileMeta(lec.file_name);
      let iconColor = '#3f51b5';
      if (meta.icon === 'fa-file-pdf') iconColor = '#e74c3c';
      else if (meta.icon === 'fa-file-image') iconColor = '#00bcd4';
      
      card.innerHTML = `
        <div class="lec-left">
          <div class="lec-icon" style="color: ${iconColor};">
            <i class="fa-solid ${meta.icon}"></i>
          </div>
          <div class="lec-info">
            <div class="lec-title" title="${lec.file_name}">${lec.file_name}</div>
            <div class="lec-meta">
              <span class="lec-date">${uploadDateFormatted}</span>
              <span class="badge status-${lec.status}">${lec.status}</span>
              ${topicTag}
            </div>
          </div>
        </div>
        <div class="lec-actions">
          <button class="btn-icon open-lec-btn" data-id="${lec.id}" title="Open in Study Center">
            <i class="fa-solid fa-graduation-cap"></i>
          </button>
          <button class="btn-icon chat-lec-btn" data-id="${lec.id}" title="Chat about this">
            <i class="fa-solid fa-comments"></i>
          </button>
        </div>
      `;
      lectureHistoryGrid.appendChild(card);

      // Append to chat selection dropdown
      const opt = document.createElement("option");
      opt.value = lec.id;
      opt.textContent = `ID: ${lec.id} - ${lec.file_name}`;
      chatLectureSelect.appendChild(opt);
    });

    // Wire up events
    document.querySelectorAll(".open-lec-btn").forEach(btn => {
      btn.addEventListener("click", () => openLecture(btn.getAttribute("data-id")));
    });
    document.querySelectorAll(".chat-lec-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-id");
        chatLectureSelect.value = id;
        switchView("chat-view");
      });
    });

  } catch (err) {
    showToast(`Failed to load history: ${err.message}`, "error");
  }
}

// Search
async function handleSearch(semantic = false) {
  const query = searchInput.value.trim();
  if (!query) {
    showToast("Please enter a query to search", "error");
    return;
  }
  
  lectureHistoryGrid.innerHTML = `
    <div class="loading-state">
      <i class="fa-solid fa-spinner fa-spin"></i> Performing search query...
    </div>
  `;

  try {
    let results = [];
    if (semantic) {
      const resp = await fetchJson(`/search/semantic?q=${encodeURIComponent(query)}`, { method: "GET" });
      results = resp.results;
    } else {
      results = await fetchJson(`/search?q=${encodeURIComponent(query)}`, { method: "GET" });
    }

    lectureHistoryGrid.innerHTML = "";
    const titleText = semantic ? "Semantic Search Results" : "Text Search Results";
    
    const header = document.createElement("div");
    header.style.cssText = "display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 10px; margin-bottom: 10px;";
    header.innerHTML = `
      <span style="font-weight: 600; color: var(--color-accent); font-size: 0.9rem;">${titleText} for: "${query}"</span>
      <button id="search-clear-btn" class="btn btn-small btn-secondary" style="padding: 4px 8px; font-size: 0.75rem;">Clear Search</button>
    `;
    lectureHistoryGrid.appendChild(header);

    document.getElementById("search-clear-btn").addEventListener("click", () => {
      searchInput.value = "";
      loadHistory();
    });

    if (results.length === 0) {
      lectureHistoryGrid.innerHTML += `
        <div class="empty-state">
          No matching lectures found. Try different keywords.
        </div>
      `;
      return;
    }

    results.forEach(lec => {
      const card = document.createElement("div");
      card.className = "lecture-card-item";
      const uploadDateFormatted = new Date(lec.upload_date).toLocaleString();
      const topicTag = lec.topic ? `<span class="badge topic-tag">${lec.topic}</span>` : "";
      
      const meta = getFileMeta(lec.file_name);
      let iconColor = '#3f51b5';
      if (meta.icon === 'fa-file-pdf') iconColor = '#e74c3c';
      else if (meta.icon === 'fa-file-image') iconColor = '#00bcd4';

      card.innerHTML = `
        <div class="lec-left">
          <div class="lec-icon" style="color: ${iconColor};">
            <i class="fa-solid ${meta.icon}"></i>
          </div>
          <div class="lec-info">
            <div class="lec-title" title="${lec.file_name}">${lec.file_name}</div>
            <div class="lec-meta">
              <span class="lec-date">${uploadDateFormatted}</span>
              <span class="badge status-${lec.status}">${lec.status}</span>
              ${topicTag}
            </div>
          </div>
        </div>
        <div class="lec-actions">
          <button class="btn-icon open-lec-btn" data-id="${lec.id}" title="Open in Study Center">
            <i class="fa-solid fa-graduation-cap"></i>
          </button>
          <button class="btn-icon chat-lec-btn" data-id="${lec.id}" title="Chat about this">
            <i class="fa-solid fa-comments"></i>
          </button>
        </div>
      `;
      lectureHistoryGrid.appendChild(card);
    });

    document.querySelectorAll(".open-lec-btn").forEach(btn => {
      btn.addEventListener("click", () => openLecture(btn.getAttribute("data-id")));
    });
    document.querySelectorAll(".chat-lec-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-id");
        chatLectureSelect.value = id;
        switchView("chat-view");
      });
    });

  } catch (err) {
    showToast(`Search failed: ${err.message}`, "error");
    loadHistory();
  }
}

// Open Lecture in Study Center
async function openLecture(lectureId) {
  showToast("Opening lecture...", "info");
  try {
    activeLecture = await fetchJson(`/lecture/${lectureId}`, { method: "GET" });
    
    // Unlock sidebar tab
    navStudy.removeAttribute("disabled");
    
    // Set UI details
    studyLectureTitle.textContent = activeLecture.file_name;
    studyLectureIdBadge.textContent = `ID: ${activeLecture.id}`;
    studyLectureTopicBadge.textContent = `Topic: ${activeLecture.topic || "Undetected"}`;
    
    // Clean tab displays
    const meta = getFileMeta(activeLecture.file_name);
    if (meta.isDoc) {
      transcribeBtn.innerHTML = `<i class="fa-solid fa-file-contract"></i> Extract Text (OCR)`;
      studyTranscriptText.textContent = activeLecture.transcript?.transcript || "Document text not extracted yet. Click 'Extract Text (OCR)' in the sidebar.";
    } else {
      transcribeBtn.innerHTML = `<i class="fa-solid fa-audio-description"></i> Transcribe Audio`;
      studyTranscriptText.textContent = activeLecture.transcript?.transcript || "Transcript not generated yet. Click 'Transcribe Audio' in the sidebar.";
    }
    studySummaryText.textContent = activeLecture.notes?.summary || "Notes not generated yet. Click 'Generate Notes' in the sidebar.";
    studyKeyPoints.textContent = activeLecture.notes?.key_points || "Notes not generated yet.";
    
    // Load flashcards and quiz if available
    flashcards = activeLecture.flashcards || [];
    currentCardIndex = 0;
    updateFlashcardUI();

    quizQuestions = activeLecture.quizzes || [];
    initQuizUI();

    // Render mind map if available
    renderMindmap(activeLecture.notes?.mind_map);

    // Switch view to Study Center
    switchView("study-view");
    
  } catch (err) {
    showToast(`Failed to open lecture: ${err.message}`, "error");
  }
}

// Study Center Operations
async function runLectureAction(path, successMsg, button) {
  if (!activeLecture) return;
  
  const originalHtml = button.innerHTML;
  button.setAttribute("disabled", "true");
  button.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i> Processing...`;
  showToast("Invoking AI Model...", "info");
  
  try {
    const data = await fetchJson(path, { method: "POST" });
    showToast(successMsg, "success");
    await openLecture(activeLecture.id);
    await loadHistory();
  } catch (err) {
    showToast(err.message, "error");
  } finally {
    button.removeAttribute("disabled");
    button.innerHTML = originalHtml;
  }
}

// Flashcards Controller
function updateFlashcardUI() {
  flashcardCard.classList.remove("flipped");
  if (flashcards.length === 0) {
    cardQuestion.textContent = "No flashcards generated. Click 'Generate Flashcards' in the sidebar.";
    cardAnswer.textContent = "Flashcards are empty.";
    cardIndicator.textContent = "0 / 0";
    cardPrevBtn.setAttribute("disabled", "true");
    cardNextBtn.setAttribute("disabled", "true");
    return;
  }

  const current = flashcards[currentCardIndex];
  cardQuestion.textContent = current.question;
  cardAnswer.textContent = current.answer;
  cardIndicator.textContent = `${currentCardIndex + 1} / ${flashcards.length}`;
  
  cardPrevBtn.toggleAttribute("disabled", currentCardIndex === 0);
  cardNextBtn.toggleAttribute("disabled", currentCardIndex === flashcards.length - 1);
}

// Quiz gameplay engine
function initQuizUI() {
  quizReadyScreen.style.display = "block";
  quizPlayScreen.style.display = "none";
  quizResultsScreen.style.display = "none";
}

function startQuiz() {
  if (quizQuestions.length === 0) {
    showToast("Please generate a quiz first", "error");
    return;
  }
  
  currentQuizIndex = 0;
  quizScore = 0;
  quizReadyScreen.style.display = "none";
  quizPlayScreen.style.display = "block";
  quizResultsScreen.style.display = "none";
  
  showQuizQuestion();
}

function showQuizQuestion() {
  canSelectOption = true;
  quizSubmitNextBtn.style.display = "none";
  
  const q = quizQuestions[currentQuizIndex];
  quizQIndex.textContent = `Question ${currentQuizIndex + 1} of ${quizQuestions.length}`;
  quizQScore.textContent = `Score: ${quizScore}`;
  quizQuestionText.textContent = q.question;
  
  // Progress Bar
  const progressPercent = ((currentQuizIndex + 1) / quizQuestions.length) * 100;
  quizProgressFill.style.width = `${progressPercent}%`;

  // Options
  quizOptionsList.innerHTML = "";
  
  const isShortAnswer = !q.option_a && !q.option_b && !q.option_c && !q.option_d;
  const isTrueFalse = q.option_a && q.option_b && !q.option_c && !q.option_d;

  if (isShortAnswer) {
    const wrapper = document.createElement("div");
    wrapper.className = "short-answer-wrapper";
    wrapper.innerHTML = `
      <input type="text" id="quiz-short-answer-input" placeholder="Type your answer here..." autocomplete="off" />
      <button type="button" id="quiz-short-answer-submit-btn" class="btn btn-primary">Submit Answer</button>
    `;
    quizOptionsList.appendChild(wrapper);

    const inputField = document.getElementById("quiz-short-answer-input");
    const submitBtn = document.getElementById("quiz-short-answer-submit-btn");

    submitBtn.addEventListener("click", () => {
      if (!canSelectOption) return;
      canSelectOption = false;
      submitBtn.setAttribute("disabled", "true");
      submitShortAnswer(inputField.value.trim(), q.answer, inputField);
    });

    inputField.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        submitBtn.click();
      }
    });

    // Auto-focus input
    setTimeout(() => inputField.focus(), 100);
  } else {
    const options = [
      { key: "a", text: q.option_a },
      { key: "b", text: q.option_b },
    ];
    if (!isTrueFalse) {
      options.push({ key: "c", text: q.option_c });
      options.push({ key: "d", text: q.option_d });
    }
    
    options.forEach(opt => {
      const btn = document.createElement("button");
      btn.className = "option-btn";
      btn.textContent = opt.text;
      btn.addEventListener("click", () => selectQuizOption(btn, opt.text, q.answer));
      quizOptionsList.appendChild(btn);
    });
  }
}

function submitShortAnswer(userAnswer, correctAnswer, inputField) {
  inputField.setAttribute("readonly", "true");
  
  const cleanStr = str => (str || "").toLowerCase().replace(/[^a-z0-9]/g, '').trim();
  const isCorrect = cleanStr(userAnswer) === cleanStr(correctAnswer);
  
  const feedbackEl = document.createElement("div");
  feedbackEl.className = "quiz-feedback-msg";
  
  if (isCorrect) {
    inputField.classList.add("correct-input");
    quizScore++;
    quizQScore.textContent = `Score: ${quizScore}`;
    feedbackEl.textContent = `Correct! The answer is "${correctAnswer}".`;
    feedbackEl.classList.add("success");
    showToast("Correct Answer!", "success");
  } else {
    inputField.classList.add("incorrect-input");
    feedbackEl.textContent = `Incorrect. The correct answer is "${correctAnswer}".`;
    feedbackEl.classList.add("error");
    showToast("Incorrect Answer.", "error");
  }
  
  quizOptionsList.appendChild(feedbackEl);
  quizSubmitNextBtn.style.display = "inline-flex";
}

function selectQuizOption(selectedBtn, selectedText, correctText) {
  if (!canSelectOption) return;
  canSelectOption = false;
  
  const isCorrect = selectedText.trim().toLowerCase() === correctText.trim().toLowerCase();
  
  // Highlight
  document.querySelectorAll(".option-btn").forEach(btn => {
    btn.setAttribute("disabled", "true");
    if (btn.textContent.trim().toLowerCase() === correctText.trim().toLowerCase()) {
      btn.classList.add("correct");
    }
  });

  if (isCorrect) {
    selectedBtn.classList.add("correct");
    quizScore++;
    quizQScore.textContent = `Score: ${quizScore}`;
    showToast("Correct Answer!", "success");
  } else {
    selectedBtn.classList.add("incorrect");
    showToast("Incorrect Answer.", "error");
  }
  
  quizSubmitNextBtn.style.display = "inline-flex";
}

function nextQuizQuestion() {
  currentQuizIndex++;
  if (currentQuizIndex < quizQuestions.length) {
    showQuizQuestion();
  } else {
    // End of quiz
    quizPlayScreen.style.display = "none";
    quizResultsScreen.style.display = "block";
    
    const percent = Math.round((quizScore / quizQuestions.length) * 100);
    document.getElementById("quiz-final-percent").textContent = `${percent}%`;
    document.getElementById("quiz-final-score").textContent = `${quizScore} out of ${quizQuestions.length} Correct`;
  }
}

// Mind Map Tree Renderer
function renderMindmap(mindMapJsonStr) {
  mindmapContainer.innerHTML = "";
  if (!mindMapJsonStr) {
    mindmapContainer.innerHTML = `
      <div class="mindmap-empty">
        <i class="fa-solid fa-diagram-project"></i>
        <p>Mind map is generated as part of study notes. Click "Generate Notes" to create one.</p>
      </div>
    `;
    return;
  }
  
  try {
    const rootNode = JSON.parse(mindMapJsonStr);
    const rootEl = createMindmapNodeElement(rootNode);
    mindmapContainer.appendChild(rootEl);
  } catch (err) {
    mindmapContainer.innerHTML = `<div class="mindmap-empty">Error loading mind map: ${err.message}</div>`;
  }
}

function createMindmapNodeElement(node) {
  const nodeEl = document.createElement("div");
  nodeEl.className = "mm-node";
  
  const hasChildren = Array.isArray(node.children) && node.children.length > 0;
  if (!hasChildren) {
    nodeEl.classList.add("mm-node-leaf");
  }

  const header = document.createElement("div");
  header.className = "mm-header";
  
  if (hasChildren) {
    header.innerHTML = `
      <span class="mm-toggle"><i class="fa-solid fa-chevron-down"></i></span>
      <span class="mm-text">${node.topic}</span>
    `;
  } else {
    header.innerHTML = `
      <span class="mm-bullet"><i class="fa-solid fa-circle-nodes"></i></span>
      <span class="mm-text">${node.topic}</span>
    `;
  }
  
  nodeEl.appendChild(header);

  if (hasChildren) {
    const childrenContainer = document.createElement("div");
    childrenContainer.className = "mm-children";
    
    node.children.forEach(child => {
      const childEl = createMindmapNodeElement(child);
      childrenContainer.appendChild(childEl);
    });
    
    nodeEl.appendChild(childrenContainer);
    
    // Toggle Collapse
    header.addEventListener("click", () => {
      const isCollapsed = childrenContainer.style.display === "none";
      childrenContainer.style.display = isCollapsed ? "flex" : "none";
      header.classList.toggle("collapsed", !isCollapsed);
    });
  }

  return nodeEl;
}

// Chat Assistant
async function handleChat(event) {
  event.preventDefault();
  const question = chatQuestionInput.value.trim();
  if (!question) return;

  const selectVal = chatLectureSelect.value;
  const useRag = useRagCheckbox.checked;

  // Render user bubble
  appendChatMessage(question, "user-message");
  chatQuestionInput.value = "";
  
  // Render typing bubble
  const loaderId = appendChatMessage(`<i class="fa-solid fa-ellipsis fa-pulse"></i> Thinking...`, "ai-message");
  
  try {
    const payload = {
      question,
      use_rag: useRag,
    };
    if (selectVal) {
      payload.lecture_id = parseInt(selectVal);
    }

    const response = await fetchJson("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    // Remove typing bubble and append actual answer
    document.getElementById(loaderId).remove();
    appendChatMessage(response.answer, "ai-message", response.sources);
    
  } catch (err) {
    document.getElementById(loaderId).remove();
    appendChatMessage(`Sorry, I encountered an error: ${err.message}`, "ai-message");
  }
}

function formatMarkdown(text) {
  if (!text) return "";
  let html = text;
  
  // Safe escape of html tags to prevent XSS but allow markdown structure
  html = html
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
    
  // Code blocks: ```code```
  html = html.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
  
  // Inline code: `code`
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  
  // Bold: **text**
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
  
  // Italic: *text*
  html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
  
  // Bullet points
  html = html.split('\n').map(line => {
    const trimmed = line.trim();
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      return `<li>${trimmed.substring(2)}</li>`;
    }
    return line;
  }).join('\n');
  
  // Wrap bullet groups in ul
  html = html.replace(/(<li>.*<\/li>)/gs, '<ul>$1</ul>');
  
  // Line breaks
  html = html.replace(/\n/g, '<br>');
  
  return html;
}

function appendChatMessage(text, senderClass, sources = null) {
  const bubbleId = `msg-${Date.now()}`;
  const msg = document.createElement("div");
  msg.className = `message ${senderClass}`;
  msg.id = bubbleId;
  
  const timeStr = senderClass === "user-message" ? "You" : "Study Assistant";
  
  let sourcesHtml = "";
  if (Array.isArray(sources) && sources.length > 0) {
    const badges = sources.map(src => `<span class="source-badge"><i class="fa-solid fa-link"></i> ${src}</span>`).join("");
    sourcesHtml = `<div class="message-sources">${badges}</div>`;
  }

  // Format AI answers with markdown
  const formattedText = (senderClass === "ai-message" && !text.includes("fa-ellipsis")) ? formatMarkdown(text) : text;

  msg.innerHTML = `
    <div class="message-bubble">${formattedText}</div>
    ${sourcesHtml}
    <span class="message-time">${timeStr}</span>
  `;
  chatMessages.appendChild(msg);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return bubbleId;
}

// Setup Event Listeners
function attachEvents() {
  // Navigation
  document.querySelectorAll(".nav-item").forEach(item => {
    item.addEventListener("click", () => {
      const tabId = item.getAttribute("data-tab");
      switchView(tabId);
    });
  });

  // Auth Tabs
  const tabLoginBtn = document.getElementById("tab-login-btn");
  const tabRegisterBtn = document.getElementById("tab-register-btn");
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");

  tabLoginBtn.addEventListener("click", () => {
    tabLoginBtn.classList.add("active");
    tabRegisterBtn.classList.remove("active");
    loginForm.classList.add("active");
    registerForm.classList.remove("active");
  });

  tabRegisterBtn.addEventListener("click", () => {
    tabRegisterBtn.classList.add("active");
    tabLoginBtn.classList.remove("active");
    registerForm.classList.add("active");
    loginForm.classList.remove("active");
  });

  // Auth Forms Submission
  loginForm.addEventListener("submit", handleLogin);
  registerForm.addEventListener("submit", handleRegister);
  document.getElementById("logout-btn").addEventListener("click", handleLogout);

  // Upload Form
  document.getElementById("upload-form").addEventListener("submit", handleUpload);

  // Search Library
  searchBtn.addEventListener("click", () => handleSearch(false));
  semanticSearchBtn.addEventListener("click", () => handleSearch(true));
  historyRefreshBtn.addEventListener("click", loadHistory);

  // Generation Buttons
  transcribeBtn.addEventListener("click", () => {
    if (activeLecture) {
      const meta = getFileMeta(activeLecture.file_name);
      const successMsg = meta.isDoc ? "Document text extraction succeeded!" : "Audio transcription succeeded!";
      runLectureAction(`/transcribe/${activeLecture.id}`, successMsg, transcribeBtn);
    }
  });
  summaryBtn.addEventListener("click", () => {
    if (activeLecture) runLectureAction(`/summary/${activeLecture.id}`, "Structured study notes generated!", summaryBtn);
  });
  quizBtn.addEventListener("click", () => {
    if (activeLecture) {
      const diff = quizDifficulty.value;
      runLectureAction(`/quiz/${activeLecture.id}?difficulty=${diff}`, "Practice quiz generated!", quizBtn);
    }
  });
  flashcardsBtn.addEventListener("click", () => {
    if (activeLecture) runLectureAction(`/flashcards/${activeLecture.id}`, "Study flashcards generated!", flashcardsBtn);
  });

  // Load Content Buttons
  getTranscriptBtn.addEventListener("click", async () => {
    if (!activeLecture) return;
    try {
      const data = await fetchJson(`/lecture/${activeLecture.id}/transcript`, { method: "GET" });
      studyTranscriptText.textContent = data.transcript;
      showToast("Transcript updated!");
    } catch (err) {
      showToast(err.message, "error");
    }
  });
  getNotesBtn.addEventListener("click", async () => {
    if (!activeLecture) return;
    try {
      const data = await fetchJson(`/lecture/${activeLecture.id}/notes`, { method: "GET" });
      studySummaryText.textContent = data.summary;
      studyKeyPoints.textContent = data.key_points;
      renderMindmap(data.mind_map);
      showToast("Study notes updated!");
    } catch (err) {
      showToast(err.message, "error");
    }
  });
  getQuizBtn.addEventListener("click", async () => {
    if (!activeLecture) return;
    try {
      quizQuestions = await fetchJson(`/lecture/${activeLecture.id}/quiz`, { method: "GET" });
      initQuizUI();
      showToast("Quiz deck loaded!");
    } catch (err) {
      showToast(err.message, "error");
    }
  });
  getFlashcardsBtn.addEventListener("click", async () => {
    if (!activeLecture) return;
    try {
      flashcards = await fetchJson(`/lecture/${activeLecture.id}/flashcards`, { method: "GET" });
      currentCardIndex = 0;
      updateFlashcardUI();
      showToast("Flashcards loaded!");
    } catch (err) {
      showToast(err.message, "error");
    }
  });

  // Study View sub-tabs
  document.querySelectorAll(".study-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".study-tab").forEach(t => t.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(tc => tc.classList.remove("active"));
      
      tab.classList.add("active");
      const targetId = tab.getAttribute("data-content");
      document.getElementById(targetId).classList.add("active");
    });
  });

  // Flashcards flipper
  flashcardCard.addEventListener("click", () => {
    flashcardCard.classList.toggle("flipped");
  });
  cardPrevBtn.addEventListener("click", () => {
    if (currentCardIndex > 0) {
      currentCardIndex--;
      updateFlashcardUI();
    }
  });
  cardNextBtn.addEventListener("click", () => {
    if (currentCardIndex < flashcards.length - 1) {
      currentCardIndex++;
      updateFlashcardUI();
    }
  });

  // Quiz Player Gameplay
  startQuizBtn.addEventListener("click", startQuiz);
  quizRestartBtn.addEventListener("click", startQuiz);
  quizSubmitNextBtn.addEventListener("click", () => {
    nextQuizQuestion();
  });

  // Chat Submission
  chatForm.addEventListener("submit", handleChat);
}

// Bootstrap
setupDragAndDrop();
attachEvents();
fetchCurrentUser();
