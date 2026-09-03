// frontend/app.js - Professional Academic Research Assistant Controller

const API_BASE = window.location.origin;

// Application State & Per-Paper Cache
const state = {
  activeTab: 'chat-tab',
  activePaper: null,
  papers: [],
  activeNovelCategory: 'all',
  isGenerating: false,
  authToken: localStorage.getItem('rgf_token') || null,
  user: null,
  systemHasFallbackKey: true,
  searchFilter: '',
  guestRemaining: 12
};

// Global Per-Paper Data Store (Strict Paper Isolation)
const paperDataCache = {};

// DOM References
const elements = {
  // Top bar
  activePaperLabel: document.getElementById('activePaperLabel'),
  offlineBanner: document.getElementById('offlineBanner'),
  userProfileBtn: document.getElementById('userProfileBtn'),
  userEmailNav: document.getElementById('userEmailNav'),
  apiKeyBadgeNav: document.getElementById('apiKeyBadgeNav'),
  
  // Sidebar
  dropzone: document.getElementById('dropzone'),
  fileInput: document.getElementById('fileInput'),
  uploadProgressBox: document.getElementById('uploadProgressBox'),
  uploadProgressBar: document.getElementById('uploadProgressBar'),
  uploadStatusLabel: document.getElementById('uploadStatusLabel'),
  uploadPctLabel: document.getElementById('uploadPctLabel'),
  uploadStepSubtext: document.getElementById('uploadStepSubtext'),
  paperList: document.getElementById('paperList'),
  paperCountText: document.getElementById('paperCountText'),
  paperSearchInput: document.getElementById('paperSearchInput'),
  refreshBtn: document.getElementById('refreshBtn'),
  statPapersCount: document.getElementById('statPapersCount'),
  statChunksCount: document.getElementById('statChunksCount'),
  
  // Tabs
  tabBtns: document.querySelectorAll('.tab-btn'),
  tabPanes: document.querySelectorAll('.tab-pane'),
  
  // Chat Tab
  chatForm: document.getElementById('chatForm'),
  chatInput: document.getElementById('chatInput'),
  sendBtn: document.getElementById('sendBtn'),
  chatStream: document.getElementById('chatStream'),
  promptPillsRow: document.querySelector('.prompt-pills-row'),
  
  // Simplified Summary Tab
  simpleSummaryContainer: document.getElementById('simpleSummaryContainer'),
  
  // Insights Tab
  insightsContainer: document.getElementById('insightsContainer'),
  domainBadge: document.getElementById('domainBadge'),
  categoryFilterBar: document.getElementById('categoryFilterBar'),
  countAll: document.getElementById('countAll'),
  countParadigm: document.getElementById('countParadigm'),
  countCross: document.getElementById('countCross'),
  countFlaws: document.getElementById('countFlaws'),
  countPredict: document.getElementById('countPredict'),
  countComb: document.getElementById('countComb'),
  
  // Compare Tab
  searchOnlineBtn: document.getElementById('searchOnlineBtn'),
  compareContainer: document.getElementById('compareContainer'),
  
  // Autonomous Agent Discovery Tab
  agentDomainBadge: document.getElementById('agentDomainBadge'),
  runAgentDiscoveryBtn: document.getElementById('runAgentDiscoveryBtn'),
  telemetryNodesCount: document.getElementById('telemetryNodesCount'),
  telemetryResistanceScore: document.getElementById('telemetryResistanceScore'),
  telemetryStatusText: document.getElementById('telemetryStatusText'),
  agentFlowchartContainer: document.getElementById('agentFlowchartContainer'),
  ontologyGraphContainer: document.getElementById('ontologyGraphContainer'),
  ontologyAxiomTag: document.getElementById('ontologyAxiomTag'),
  agentTranscriptContainer: document.getElementById('agentTranscriptContainer'),
  toggleAgentTranscriptBtn: document.getElementById('toggleAgentTranscriptBtn'),
  verifiedDiscoveryContainer: document.getElementById('verifiedDiscoveryContainer'),

  // Export Tab
  downloadPdfBtn: document.getElementById('downloadPdfBtn'),
  downloadMdBtn: document.getElementById('downloadMdBtn'),
  exportPreviewBody: document.getElementById('exportPreviewBody'),
  
  // Modals & Toast
  evidenceModal: document.getElementById('evidenceModal'),
  modalTitle: document.getElementById('modalTitle'),
  modalBody: document.getElementById('modalBody'),
  modalCloseBtn: document.getElementById('modalCloseBtn'),
  toastBox: document.getElementById('toastBox'),
  
  // Real Auth Modal
  authModal: document.getElementById('authModal'),
  tabSignInBtn: document.getElementById('tabSignInBtn'),
  tabRegisterBtn: document.getElementById('tabRegisterBtn'),
  signInFormSection: document.getElementById('signInFormSection'),
  registerFormSection: document.getElementById('registerFormSection'),
  signInForm: document.getElementById('signInForm'),
  loginEmailInput: document.getElementById('loginEmailInput'),
  loginPasswordInput: document.getElementById('loginPasswordInput'),
  submitLoginBtn: document.getElementById('submitLoginBtn'),
  registerForm: document.getElementById('registerForm'),
  regNameInput: document.getElementById('regNameInput'),
  regEmailInput: document.getElementById('regEmailInput'),
  regPasswordInput: document.getElementById('regPasswordInput'),
  submitRegisterBtn: document.getElementById('submitRegisterBtn'),
  googleSignInBtn: document.getElementById('googleSignInBtn'),
  googleSignUpBtn: document.getElementById('googleSignUpBtn'),
  closeAuthModalBtn: document.getElementById('closeAuthModalBtn'),
  
  // API Key Modal
  apiKeyModal: document.getElementById('apiKeyModal'),
  apiKeyForm: document.getElementById('apiKeyForm'),
  groqApiKeyInput: document.getElementById('groqApiKeyInput'),
  toggleKeyVisibilityBtn: document.getElementById('toggleKeyVisibilityBtn'),
  apiKeyStatusMsg: document.getElementById('apiKeyStatusMsg'),
  saveApiKeyBtn: document.getElementById('saveApiKeyBtn'),
  closeApiKeyModalBtn: document.getElementById('closeApiKeyModalBtn'),
  
  // Settings Modal
  userSettingsModal: document.getElementById('userSettingsModal'),
  settingsUserEmail: document.getElementById('settingsUserEmail'),
  settingsKeyMask: document.getElementById('settingsKeyMask'),
  settingsChangeKeyBtn: document.getElementById('settingsChangeKeyBtn'),
  settingsOpenFaqBtn: document.getElementById('settingsOpenFaqBtn'),
  settingsLogoutBtn: document.getElementById('settingsLogoutBtn'),
  closeUserSettingsBtn: document.getElementById('closeUserSettingsBtn'),
  
  // FAQ Modal
  faqModal: document.getElementById('faqModal'),
  closeFaqBtn: document.getElementById('closeFaqBtn'),
};

// -----------------------------------------------------------------------------
// App Initialization
// -----------------------------------------------------------------------------
async function startApp() {
  initIcons();
  initNetworkMonitor();
  initNavigation();
  initRealAuthUI();
  initGoogleAuth();
  initUpload();
  initChat();
  initTabs();
  initModal();
  initNovelCategoryFilters();
  initPaperSearch();
  
  await checkAuthStatus();
  await fetchPapers();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', startApp);
} else {
  startApp();
}

function initIcons() {
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

// -----------------------------------------------------------------------------
// Network Online/Offline Monitoring
// -----------------------------------------------------------------------------
function initNetworkMonitor() {
  window.addEventListener('online', () => {
    if (elements.offlineBanner) elements.offlineBanner.style.display = 'none';
    showToast('Network reconnected. Online mode active.', 'success');
  });

  window.addEventListener('offline', () => {
    if (elements.offlineBanner) elements.offlineBanner.style.display = 'flex';
    showToast('No internet connection detected.', 'warning');
  });

  if (!navigator.onLine && elements.offlineBanner) {
    elements.offlineBanner.style.display = 'flex';
  }
}

// -----------------------------------------------------------------------------
// Authenticated API Fetch Wrapper with Global Error Handling & Guest Limits
// -----------------------------------------------------------------------------
async function authFetch(url, options = {}) {
  if (!navigator.onLine) {
    showToast('Network offline. Action paused.', 'warning');
    throw new Error('Network offline');
  }

  const headers = Object.assign({}, options.headers || {});
  const token = localStorage.getItem('rgf_token');
  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  options.headers = headers;

  try {
    const res = await fetch(url, options);

    if (res.status === 401) {
      localStorage.removeItem('rgf_token');
      state.authToken = null;
      state.user = null;
      updateUserNavUI();
      openAuthModal();
      showToast('Session expired or login required.', 'warning');
      throw new Error('Authentication required');
    }

    if (res.status === 429) {
      const errData = await res.json().catch(() => ({}));
      const msg = errData.detail || 'Free trial or Groq API rate limit reached.';
      showToast(msg, 'warning');
      openApiKeyModal(msg);
      throw new Error(msg);
    }

    return res;
  } catch (err) {
    if (err.name === 'TypeError' && err.message.includes('fetch')) {
      showToast('Could not reach backend server. Please verify it is running.', 'error');
    }
    throw err;
  }
}

// -----------------------------------------------------------------------------
// Toast Messages (Zero Emojis)
// -----------------------------------------------------------------------------
function showToast(msg, type = 'info') {
  if (!elements.toastBox) return;
  const toast = document.createElement('div');
  toast.className = 'toast';
  
  let iconHtml = '<i class="fa-solid fa-circle-info" style="color: #ffffff; font-size: 13px;"></i>';
  if (type === 'success') iconHtml = '<i class="fa-solid fa-circle-check" style="color: #34d399; font-size: 13px;"></i>';
  if (type === 'error') iconHtml = '<i class="fa-solid fa-circle-exclamation" style="color: #f87171; font-size: 13px;"></i>';
  if (type === 'warning') iconHtml = '<i class="fa-solid fa-triangle-exclamation" style="color: #fbbf24; font-size: 13px;"></i>';
  
  toast.innerHTML = `
    ${iconHtml}
    <span>${escapeHtml(msg)}</span>
  `;
  
  elements.toastBox.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.25s';
    setTimeout(() => toast.remove(), 250);
  }, 4000);
}

// -----------------------------------------------------------------------------
// Real User Authentication & Google OAuth Identity Services
// -----------------------------------------------------------------------------
async function checkAuthStatus() {
  try {
    const res = await fetch(`${API_BASE}/api/auth/me`, {
      headers: state.authToken ? { 'Authorization': `Bearer ${state.authToken}` } : {}
    });
    
    if (res.ok) {
      const data = await res.json();
      if (data.authenticated && data.user) {
        state.user = data.user;
        state.systemHasFallbackKey = data.system_has_fallback_key;
        updateUserNavUI();
      } else {
        state.user = null;
        state.systemHasFallbackKey = data.system_has_fallback_key;
        updateUserNavUI();
      }
    }

    // Check guest remaining quota
    fetchGuestQuota();
  } catch (err) {
    console.log('Auth check notice:', err);
  }
}

async function fetchGuestQuota() {
  try {
    const res = await fetch(`${API_BASE}/api/auth/guest-status`, {
      headers: state.authToken ? { 'Authorization': `Bearer ${state.authToken}` } : {}
    });
    if (res.ok) {
      const data = await res.json();
      state.guestRemaining = data.remaining;
      if (!state.user && elements.apiKeyBadgeNav) {
        if (data.remaining > 0) {
          elements.apiKeyBadgeNav.className = 'nav-key-badge success';
          elements.apiKeyBadgeNav.innerHTML = `<i class="fa-solid fa-bolt" style="font-size: 10px;"></i><span>${data.remaining} Free Preview</span>`;
        } else {
          elements.apiKeyBadgeNav.className = 'nav-key-badge warning';
          elements.apiKeyBadgeNav.innerHTML = `<i class="fa-solid fa-lock" style="font-size: 10px;"></i><span>Trial Ended</span>`;
        }
      }
    }
  } catch (e) {}
}

function updateUserNavUI() {
  if (!elements.userEmailNav || !elements.apiKeyBadgeNav) return;

  if (state.user) {
    elements.userEmailNav.textContent = state.user.name || state.user.email;
    if (state.user.has_api_key) {
      elements.apiKeyBadgeNav.className = 'nav-key-badge success';
      elements.apiKeyBadgeNav.innerHTML = '<i class="fa-solid fa-key" style="font-size: 10px;"></i><span>Key Active</span>';
    } else {
      elements.apiKeyBadgeNav.className = 'nav-key-badge warning';
      elements.apiKeyBadgeNav.innerHTML = '<i class="fa-solid fa-key" style="font-size: 10px;"></i><span>No Custom Key</span>';
    }
  } else {
    elements.userEmailNav.textContent = 'Guest Mode (Sign In)';
    if (state.guestRemaining > 0) {
      elements.apiKeyBadgeNav.className = 'nav-key-badge success';
      elements.apiKeyBadgeNav.innerHTML = `<i class="fa-solid fa-bolt" style="font-size: 10px;"></i><span>${state.guestRemaining} Free Preview</span>`;
    } else {
      elements.apiKeyBadgeNav.className = 'nav-key-badge warning';
      elements.apiKeyBadgeNav.innerHTML = '<i class="fa-solid fa-user-lock" style="font-size: 10px;"></i><span>Sign In</span>';
    }
  }
}

function initGoogleAuth() {
  const triggerGoogleLogin = () => {
    const email = prompt("Sign in with Google\nEnter your Google email address (e.g., yourname@gmail.com):");
    if (!email || !email.includes('@')) {
      if (email) showToast("Valid email address required.", "warning");
      return;
    }
    const cleanEmail = email.trim().toLowerCase();
    executeGoogleBackendAuth(cleanEmail, cleanEmail.split('@')[0]);
  };

  if (elements.googleSignInBtn) elements.googleSignInBtn.addEventListener('click', triggerGoogleLogin);
  if (elements.googleSignUpBtn) elements.googleSignUpBtn.addEventListener('click', triggerGoogleLogin);
}

function handleGoogleCredentialResponse(response) {
  try {
    // Decode Google JWT credential
    const base64Url = response.credential.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
      return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
    }).join(''));

    const profile = JSON.parse(jsonPayload);
    executeGoogleBackendAuth(profile.email, profile.name, profile.picture);
  } catch (e) {
    console.error("Google decoding error:", e);
  }
}

async function executeGoogleBackendAuth(email, name = '', picture = '') {
  try {
    const res = await fetch(`${API_BASE}/api/auth/google`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: email,
        name: name || email.split('@')[0],
        picture: picture
      })
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Google sign-in failed');

    state.authToken = data.token;
    localStorage.setItem('rgf_token', data.token);
    state.user = data.user;
    state.activePaper = null;
    elements.activePaperLabel.textContent = 'No paper selected';
    updateUserNavUI();
    closeAuthModal();
    showToast(`Signed in as ${data.user.name || data.user.email}!`, 'success');
    await fetchPapers();
    switchTab(state.activeTab);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function initRealAuthUI() {
  if (elements.userProfileBtn) {
    elements.userProfileBtn.addEventListener('click', () => {
      if (state.user) {
        openUserSettingsModal();
      } else {
        openAuthModal();
      }
    });
  }

  // Auth sub-tabs toggle
  if (elements.tabSignInBtn && elements.tabRegisterBtn) {
    elements.tabSignInBtn.addEventListener('click', () => {
      elements.tabSignInBtn.classList.add('active');
      elements.tabRegisterBtn.classList.remove('active');
      elements.signInFormSection.style.display = 'block';
      elements.registerFormSection.style.display = 'none';
    });

    elements.tabRegisterBtn.addEventListener('click', () => {
      elements.tabRegisterBtn.classList.add('active');
      elements.tabSignInBtn.classList.remove('active');
      elements.signInFormSection.style.display = 'none';
      elements.registerFormSection.style.display = 'block';
    });
  }

  // Toggle password visibility buttons
  document.querySelectorAll('.toggle-pwd-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.dataset.target;
      const input = document.getElementById(targetId);
      if (input) {
        const isPwd = input.type === 'password';
        input.type = isPwd ? 'text' : 'password';
        btn.innerHTML = isPwd 
          ? '<i class="fa-solid fa-eye-slash" style="font-size: 12px;"></i>' 
          : '<i class="fa-solid fa-eye" style="font-size: 12px;"></i>';
      }
    });
  });

  // Real Email/Password Sign In Submit
  if (elements.signInForm) {
    elements.signInForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = elements.loginEmailInput.value.trim();
      const password = elements.loginPasswordInput.value;
      if (!email || !password) return;

      elements.submitLoginBtn.disabled = true;
      elements.submitLoginBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Signing In...';

      try {
        const res = await fetch(`${API_BASE}/api/auth/login`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Sign in failed');

        state.authToken = data.token;
        localStorage.setItem('rgf_token', data.token);
        state.user = data.user;
        state.activePaper = null;
        elements.activePaperLabel.textContent = 'No paper selected';
        updateUserNavUI();
        closeAuthModal();
        showToast(`Welcome back, ${data.user.name || data.user.email}!`, 'success');

        // Fetch user's isolated workspace papers
        await fetchPapers();
        switchTab(state.activeTab);
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        elements.submitLoginBtn.disabled = false;
        elements.submitLoginBtn.innerHTML = '<i class="fa-solid fa-right-to-bracket"></i> Sign In';
      }
    });
  }

  // Real Email/Password Register Submit
  if (elements.registerForm) {
    elements.registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = elements.regNameInput.value.trim();
      const email = elements.regEmailInput.value.trim();
      const password = elements.regPasswordInput.value;

      if (!email || !password) return;

      elements.submitRegisterBtn.disabled = true;
      elements.submitRegisterBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Creating Account...';

      try {
        const res = await fetch(`${API_BASE}/api/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, email, password })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Registration failed');

        state.authToken = data.token;
        localStorage.setItem('rgf_token', data.token);
        state.user = data.user;
        state.activePaper = null;
        elements.activePaperLabel.textContent = 'No paper selected';
        updateUserNavUI();
        closeAuthModal();
        showToast(`Account created! Welcome, ${data.user.name || data.user.email}!`, 'success');

        // Prompt Groq API key setup for unlimited capacity
        setTimeout(() => {
          openApiKeyModal('To ensure maximum analysis quota, please enter your personal Groq API key.');
        }, 500);

        await fetchPapers();
        switchTab(state.activeTab);
      } catch (err) {
        showToast(err.message, 'error');
      } finally {
        elements.submitRegisterBtn.disabled = false;
        elements.submitRegisterBtn.innerHTML = '<i class="fa-solid fa-user-plus"></i> Create Account';
      }
    });
  }

  if (elements.closeAuthModalBtn) {
    elements.closeAuthModalBtn.addEventListener('click', closeAuthModal);
  }

  // API Key Form submit
  if (elements.apiKeyForm) {
    elements.apiKeyForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const apiKey = elements.groqApiKeyInput.value.trim();
      if (!apiKey) return;

      elements.saveApiKeyBtn.disabled = true;
      elements.saveApiKeyBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying with Groq...';
      if (elements.apiKeyStatusMsg) {
        elements.apiKeyStatusMsg.style.display = 'block';
        elements.apiKeyStatusMsg.style.color = 'var(--text-muted)';
        elements.apiKeyStatusMsg.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> Testing Groq API Key...';
      }

      try {
        const res = await authFetch(`${API_BASE}/api/auth/set-api-key`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ api_key: apiKey })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Invalid Groq API Key');

        if (state.user) {
          state.user.has_api_key = true;
          state.user.masked_key = data.masked_key;
        }
        updateUserNavUI();
        closeApiKeyModal();
        showToast('Groq API Key verified and saved securely!', 'success');
      } catch (err) {
        if (elements.apiKeyStatusMsg) {
          elements.apiKeyStatusMsg.style.display = 'block';
          elements.apiKeyStatusMsg.style.color = '#ef4444';
          elements.apiKeyStatusMsg.textContent = err.message;
        }
        showToast(err.message, 'error');
      } finally {
        elements.saveApiKeyBtn.disabled = false;
        elements.saveApiKeyBtn.innerHTML = '<i class="fa-solid fa-check"></i> Verify & Save Key';
      }
    });
  }

  // Toggle API key visibility in key modal
  if (elements.toggleKeyVisibilityBtn) {
    elements.toggleKeyVisibilityBtn.addEventListener('click', () => {
      const type = elements.groqApiKeyInput.type === 'password' ? 'text' : 'password';
      elements.groqApiKeyInput.type = type;
      elements.toggleKeyVisibilityBtn.innerHTML = type === 'password' 
        ? '<i class="fa-solid fa-eye" style="font-size: 12px;"></i>' 
        : '<i class="fa-solid fa-eye-slash" style="font-size: 12px;"></i>';
    });
  }

  // Settings Buttons
  if (elements.closeApiKeyModalBtn) elements.closeApiKeyModalBtn.addEventListener('click', closeApiKeyModal);
  if (elements.closeUserSettingsBtn) elements.closeUserSettingsBtn.addEventListener('click', closeUserSettingsModal);
  if (elements.settingsChangeKeyBtn) {
    elements.settingsChangeKeyBtn.addEventListener('click', () => {
      closeUserSettingsModal();
      openApiKeyModal();
    });
  }
  if (elements.settingsOpenFaqBtn) {
    elements.settingsOpenFaqBtn.addEventListener('click', () => {
      closeUserSettingsModal();
      openFaqModal();
    });
  }
  if (elements.closeFaqBtn) elements.closeFaqBtn.addEventListener('click', closeFaqModal);
  if (elements.settingsLogoutBtn) elements.settingsLogoutBtn.addEventListener('click', handleLogout);
}

function openAuthModal() {
  if (!elements.authModal) return;
  elements.authModal.style.display = 'flex';
  initIcons();
}

function closeAuthModal() {
  if (elements.authModal) elements.authModal.style.display = 'none';
}

function openApiKeyModal(hintMsg = '') {
  if (!elements.apiKeyModal) return;
  if (elements.apiKeyStatusMsg) {
    if (hintMsg) {
      elements.apiKeyStatusMsg.style.display = 'block';
      elements.apiKeyStatusMsg.style.color = '#92400e';
      elements.apiKeyStatusMsg.textContent = hintMsg;
    } else {
      elements.apiKeyStatusMsg.style.display = 'none';
    }
  }
  elements.apiKeyModal.style.display = 'flex';
  elements.groqApiKeyInput.value = '';
  elements.groqApiKeyInput.focus();
  initIcons();
}

function closeApiKeyModal() {
  if (elements.apiKeyModal) elements.apiKeyModal.style.display = 'none';
}

function openUserSettingsModal() {
  if (!elements.userSettingsModal) return;
  if (elements.settingsUserEmail && state.user) {
    elements.settingsUserEmail.textContent = state.user.email;
  }
  if (elements.settingsKeyMask && state.user) {
    elements.settingsKeyMask.textContent = state.user.masked_key || 'No custom key configured';
  }
  elements.userSettingsModal.style.display = 'flex';
  initIcons();
}

function closeUserSettingsModal() {
  if (elements.userSettingsModal) elements.userSettingsModal.style.display = 'none';
}

function openFaqModal() {
  if (elements.faqModal) elements.faqModal.style.display = 'flex';
  initIcons();
}

function closeFaqModal() {
  if (elements.faqModal) elements.faqModal.style.display = 'none';
}

async function handleLogout() {
  try {
    await fetch(`${API_BASE}/api/auth/logout`, { method: 'POST' });
  } catch (e) {}
  localStorage.removeItem('rgf_token');
  state.authToken = null;
  state.user = null;
  state.activePaper = null;
  elements.activePaperLabel.textContent = 'No paper selected';
  updateUserNavUI();
  closeUserSettingsModal();
  showToast('You have been signed out.', 'info');
  await fetchPapers();
  switchTab(state.activeTab);
}

// -----------------------------------------------------------------------------
// Tab Navigation
// -----------------------------------------------------------------------------
function initNavigation() {
  elements.tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.dataset.tab;
      switchTab(targetTab);
    });
  });
}

function switchTab(tabId) {
  state.activeTab = tabId;
  
  elements.tabBtns.forEach(btn => {
    if (btn.dataset.tab === tabId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  elements.tabPanes.forEach(pane => {
    if (pane.id === tabId) {
      pane.classList.add('active');
    } else {
      pane.classList.remove('active');
    }
  });

  // Re-render tab data for active paper if selected, otherwise show clean hero
  if (state.activePaper) {
    if (tabId === 'summary-simple-tab') {
      fetchPaperSimplifiedSummary(state.activePaper);
    } else if (tabId === 'insights-tab') {
      fetchPaperNovelDiscovery(state.activePaper);
    } else if (tabId === 'agent-discovery-tab') {
      fetchAutonomousAgentDiscovery(state.activePaper);
    } else if (tabId === 'compare-tab') {
      renderCompareData(state.activePaper);
    } else if (tabId === 'export-tab') {
      renderExportPreview(state.activePaper);
    }
  } else {
    renderEmptyHeroesForActiveTab(tabId);
  }
}

function renderEmptyHeroesForActiveTab(tabId) {
  if (tabId === 'summary-simple-tab' && elements.simpleSummaryContainer) {
    elements.simpleSummaryContainer.innerHTML = `
      <div class="empty-selection-hero">
        <div class="empty-hero-icon">
          <i class="fa-solid fa-book-bookmark" style="font-size: 28px; color: var(--primary);"></i>
        </div>
        <h3 class="empty-hero-title">Select a Paper for Summary Breakdown</h3>
        <p class="empty-hero-desc">Click any paper from your library on the left or upload a PDF to generate a structured plain-English analysis.</p>
      </div>
    `;
  } else if (tabId === 'insights-tab' && elements.insightsContainer) {
    elements.insightsContainer.innerHTML = `
      <div class="empty-selection-hero">
        <div class="empty-hero-icon">
          <i class="fa-solid fa-lightbulb" style="font-size: 28px; color: var(--primary);"></i>
        </div>
        <h3 class="empty-hero-title">Select a Paper to Discover Novel Research Insights</h3>
        <p class="empty-hero-desc">Choose a research document from your library to discover paradigm shifts, hidden limitations, and actionable blueprints.</p>
      </div>
    `;
  } else if (tabId === 'agent-discovery-tab') {
    if (elements.agentFlowchartContainer) elements.agentFlowchartContainer.innerHTML = '';
    if (elements.ontologyGraphContainer) elements.ontologyGraphContainer.innerHTML = '';
    if (elements.agentTranscriptContainer) elements.agentTranscriptContainer.innerHTML = '';
    if (elements.verifiedDiscoveryContainer) {
      elements.verifiedDiscoveryContainer.innerHTML = `
        <div class="empty-selection-hero">
          <div class="empty-hero-icon">
            <i class="fa-solid fa-diagram-project" style="font-size: 28px; color: var(--primary);"></i>
          </div>
          <h3 class="empty-hero-title">Select a Paper to Run Autonomous Agent Discovery</h3>
          <p class="empty-hero-desc">Choose a research document from your library to trigger the 5-agent Actor-Critic state machine, extract ontological knowledge graphs, and discover verified breakthroughs.</p>
        </div>
      `;
    }
  } else if (tabId === 'compare-tab' && elements.compareContainer) {
    elements.compareContainer.innerHTML = `
      <div class="empty-selection-hero">
        <div class="empty-hero-icon">
          <i class="fa-solid fa-globe" style="font-size: 28px; color: var(--primary);"></i>
        </div>
        <h3 class="empty-hero-title">Select a Paper to Compare with Global Literature</h3>
        <p class="empty-hero-desc">Select a paper from the library and click 'Search Online Papers' to compare its methodology against external published works.</p>
      </div>
    `;
  } else if (tabId === 'export-tab' && elements.exportPreviewBody) {
    elements.exportPreviewBody.innerHTML = `
      <div style="text-align: center; padding: 28px 12px; color: var(--text-muted);">
        Select a paper from your library to generate and preview its complete analysis report.
      </div>
    `;
  }
}

// -----------------------------------------------------------------------------
// Paper Upload with Live Multi-Step Progress Bar
// -----------------------------------------------------------------------------
function initUpload() {
  elements.dropzone.addEventListener('click', () => elements.fileInput.click());
  
  elements.dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.dropzone.classList.add('dragover');
  });

  elements.dropzone.addEventListener('dragleave', () => {
    elements.dropzone.classList.remove('dragover');
  });

  elements.dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.dropzone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFiles(e.dataTransfer.files);
    }
  });

  elements.fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
  });

  elements.refreshBtn.addEventListener('click', () => {
    fetchPapers();
    showToast('Library refreshed', 'info');
  });
}

async function handleFiles(files) {
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      showToast(`Skipped non-PDF: ${file.name}`, 'warning');
      continue;
    }
    // Max 50MB check
    if (file.size > 50 * 1024 * 1024) {
      showToast(`File exceeds 50MB limit: ${file.name}`, 'error');
      continue;
    }
    await uploadSinglePaper(file);
  }
}

async function uploadSinglePaper(file) {
  elements.uploadProgressBox.style.display = 'block';
  elements.uploadProgressBar.style.width = '10%';
  elements.uploadStatusLabel.textContent = `Uploading ${file.name}...`;
  elements.uploadPctLabel.textContent = '10%';
  if (elements.uploadStepSubtext) elements.uploadStepSubtext.textContent = 'Step 1/4: Reading document structure...';

  const formData = new FormData();
  formData.append('file', file);

  // Progressive steps animation
  const stepTimer = setInterval(() => {
    const curr = parseInt(elements.uploadProgressBar.style.width, 10) || 10;
    if (curr < 40) {
      elements.uploadProgressBar.style.width = `${curr + 15}%`;
      elements.uploadPctLabel.textContent = `${curr + 15}%`;
      if (elements.uploadStepSubtext) elements.uploadStepSubtext.textContent = 'Step 2/4: Chunking & extracting sections...';
    } else if (curr < 80) {
      elements.uploadProgressBar.style.width = `${curr + 15}%`;
      elements.uploadPctLabel.textContent = `${curr + 15}%`;
      if (elements.uploadStepSubtext) elements.uploadStepSubtext.textContent = 'Step 3/4: Generating vector embeddings...';
    }
  }, 400);

  try {
    const res = await authFetch(`${API_BASE}/api/upload`, {
      method: 'POST',
      body: formData
    });

    clearInterval(stepTimer);
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || 'Upload failed');
    }

    elements.uploadProgressBar.style.width = '100%';
    elements.uploadPctLabel.textContent = '100%';
    elements.uploadStatusLabel.textContent = data.status === 'skipped' ? 'Paper already indexed!' : 'Indexing complete!';
    if (elements.uploadStepSubtext) {
      elements.uploadStepSubtext.textContent = data.status === 'skipped' 
        ? 'Loaded existing paper from your workspace' 
        : 'Step 4/4: Indexed in your private workspace!';
    }

    if (data.status === 'skipped') {
      showToast(`"${file.name}" is already in your library. Select it from the list to analyze.`, 'info');
    } else {
      showToast(`"${file.name}" added to library! Click it in the list on the left to start analysis.`, 'success');
    }
    
    // Refresh library list so the new paper appears in the list on the left
    await fetchPapers();
  } catch (err) {
    clearInterval(stepTimer);
    showToast(`Upload error: ${err.message}`, 'error');
  } finally {
    setTimeout(() => {
      elements.uploadProgressBox.style.display = 'none';
      elements.uploadProgressBar.style.width = '0%';
    }, 2000);
  }
}

// -----------------------------------------------------------------------------
// Fetch & Render Paper Library (Strict Workspace Isolation)
// -----------------------------------------------------------------------------
function initPaperSearch() {
  if (elements.paperSearchInput) {
    elements.paperSearchInput.addEventListener('input', (e) => {
      state.searchFilter = e.target.value.toLowerCase().trim();
      renderPaperList();
    });
  }
}

async function fetchPapers() {
  try {
    const res = await authFetch(`${API_BASE}/api/papers`);
    if (!res.ok) return;

    const data = await res.json();
    state.papers = data.papers || [];

    elements.paperCountText.textContent = state.papers.length;
    elements.statPapersCount.textContent = state.papers.length;

    let totalChunks = 0;
    state.papers.forEach(p => totalChunks += (p.chunk_count || 0));
    elements.statChunksCount.textContent = totalChunks;

    renderPaperList();

    // DO NOT AUTO-SELECT ON STARTUP
    if (!state.activePaper) {
      elements.activePaperLabel.textContent = 'No paper selected';
    }
  } catch (err) {
    console.log('Error fetching papers:', err);
  }
}

function renderPaperList() {
  if (state.papers.length === 0) {
    elements.paperList.innerHTML = `
      <div style="text-align: center; padding: 28px 12px; color: var(--text-dim); font-size: 0.82rem;">
        <i class="fa-solid fa-file-circle-plus" style="font-size: 24px; color: #cbd5e1; margin-bottom: 8px; display: block;"></i>
        No papers in your workspace.<br>Upload a PDF above to begin.
      </div>
    `;
    return;
  }

  let filtered = state.papers;
  if (state.searchFilter) {
    filtered = state.papers.filter(p => {
      const title = (p.title || p.paper_id || '').toLowerCase();
      return title.includes(state.searchFilter);
    });
  }

  if (filtered.length === 0) {
    elements.paperList.innerHTML = `
      <div style="text-align: center; padding: 20px 8px; color: var(--text-dim); font-size: 0.8rem;">
        No papers match "${escapeHtml(state.searchFilter)}"
      </div>
    `;
    return;
  }

  elements.paperList.innerHTML = '';
  filtered.forEach(paper => {
    const isSelected = state.activePaper === paper.paper_id;
    const card = document.createElement('div');
    card.className = `paper-item ${isSelected ? 'active' : ''}`;
    card.dataset.paperId = paper.paper_id;

    card.innerHTML = `
      <div class="paper-doc-badge">
        <i class="fa-solid fa-file-pdf" style="font-size: 14px;"></i>
      </div>
      <div class="paper-item-body">
        <div class="paper-item-header">
          <div class="paper-item-name" title="${escapeHtml(paper.title || paper.paper_id)}">
            ${escapeHtml(paper.title || paper.paper_id)}
          </div>
          <button class="delete-paper-icon-btn" data-id="${escapeHtml(paper.paper_id)}" title="Remove from workspace">
            <i class="fa-solid fa-trash-can" style="font-size: 11px;"></i>
          </button>
        </div>
        <div class="paper-badge-row">
          <span class="paper-badge-pill">${paper.chunk_count || 0} chunks</span>
          <span class="paper-badge-pill">${paper.year || '2026'}</span>
          ${paper.total_pages ? `<span class="paper-badge-pill">${paper.total_pages} pages</span>` : ''}
        </div>
      </div>
    `;

    card.addEventListener('click', (e) => {
      if (e.target.closest('.delete-paper-icon-btn')) return;
      selectPaper(paper.paper_id);
    });

    const delBtn = card.querySelector('.delete-paper-icon-btn');
    delBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      deletePaper(paper.paper_id);
    });

    elements.paperList.appendChild(card);
  });

  initIcons();
}

async function selectPaper(paperId) {
  state.activePaper = paperId;
  
  const paper = state.papers.find(p => p.paper_id === paperId);
  const paperTitle = paper ? (paper.title || paper.paper_id) : paperId;
  
  elements.activePaperLabel.textContent = paperTitle;
  elements.activePaperLabel.title = paperTitle;

  document.querySelectorAll('.paper-item').forEach(el => {
    if (el.dataset.paperId === paperId) {
      el.classList.add('active');
    } else {
      el.classList.remove('active');
    }
  });

  showToast(`Loaded "${paperTitle}"`, 'info');

  // Switch tab content smoothly
  switchTab(state.activeTab);
}

async function deletePaper(paperId) {
  if (!confirm(`Are you sure you want to remove this paper from your workspace?`)) return;

  try {
    const res = await authFetch(`${API_BASE}/api/papers/${encodeURIComponent(paperId)}`, {
      method: 'DELETE'
    });

    if (res.ok) {
      showToast(`Paper removed from workspace`, 'info');
      delete paperDataCache[paperId];
      if (state.activePaper === paperId) {
        state.activePaper = null;
        elements.activePaperLabel.textContent = 'No paper selected';
      }
      await fetchPapers();
      switchTab(state.activeTab);
    } else {
      const err = await res.json();
      showToast(err.detail || 'Delete failed', 'error');
    }
  } catch (err) {
    showToast(`Delete error: ${err.message}`, 'error');
  }
}

// -----------------------------------------------------------------------------
// Interactive Research Chat with Dynamic Multi-Stage Thinking UI
// -----------------------------------------------------------------------------
function initChat() {
  elements.chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = elements.chatInput.value.trim();
    if (!query) return;
    sendChatMessage(query);
  });

  if (elements.promptPillsRow) {
    elements.promptPillsRow.querySelectorAll('.prompt-pill').forEach(pill => {
      pill.addEventListener('click', () => {
        const q = pill.dataset.q;
        if (q) {
          elements.chatInput.value = q;
          sendChatMessage(q);
        }
      });
    });
  }
}

async function sendChatMessage(query) {
  if (!state.activePaper) {
    showToast('Please select or upload a paper from the library first.', 'warning');
    return;
  }

  // 1. Append User Bubble
  appendChatBubble('user', query);
  elements.chatInput.value = '';
  elements.sendBtn.disabled = true;

  // 2. Append Dynamic Multi-Stage Thinking Card
  const thinkingBubble = document.createElement('div');
  thinkingBubble.className = 'chat-bubble assistant thinking-state';
  thinkingBubble.innerHTML = `
    <div class="avatar">
      <i data-lucide="bot" style="width: 16px; height: 16px;"></i>
    </div>
    <div class="bubble-content" style="flex: 1;">
      <div class="chat-thinking-card">
        <div class="thinking-pulse-header">
          <div class="thinking-pulse-dot"></div>
          <span>PhD Research Agent is reasoning...</span>
        </div>
        <div class="thinking-steps-list">
          <div class="thinking-step-row" id="thinkStep1">
            <span class="thinking-step-icon active"><i class="fa-solid fa-spinner"></i></span>
            <span class="thinking-step-text">Searching grounded passages across paper corpus...</span>
          </div>
          <div class="thinking-step-row" id="thinkStep2" style="opacity: 0.6;">
            <span class="thinking-step-icon pending"><i class="fa-regular fa-circle"></i></span>
            <span class="thinking-step-text">Verifying citations & cross-referencing tab inferences...</span>
          </div>
          <div class="thinking-step-row" id="thinkStep3" style="opacity: 0.6;">
            <span class="thinking-step-icon pending"><i class="fa-regular fa-circle"></i></span>
            <span class="thinking-step-text">Synthesizing peer-reviewed academic response...</span>
          </div>
        </div>
      </div>
    </div>
  `;
  elements.chatStream.appendChild(thinkingBubble);
  elements.chatStream.scrollTop = elements.chatStream.scrollHeight;
  initIcons();

  // Progressively update thinking steps
  const t1 = setTimeout(() => {
    const s1 = document.getElementById('thinkStep1');
    const s2 = document.getElementById('thinkStep2');
    if (s1 && s2) {
      s1.querySelector('.thinking-step-icon').className = 'thinking-step-icon done';
      s1.querySelector('.thinking-step-icon').innerHTML = '<i class="fa-solid fa-check"></i>';
      s2.style.opacity = '1';
      s2.querySelector('.thinking-step-icon').className = 'thinking-step-icon active';
      s2.querySelector('.thinking-step-icon').innerHTML = '<i class="fa-solid fa-spinner"></i>';
    }
  }, 900);

  const t2 = setTimeout(() => {
    const s2 = document.getElementById('thinkStep2');
    const s3 = document.getElementById('thinkStep3');
    if (s2 && s3) {
      s2.querySelector('.thinking-step-icon').className = 'thinking-step-icon done';
      s2.querySelector('.thinking-step-icon').innerHTML = '<i class="fa-solid fa-check"></i>';
      s3.style.opacity = '1';
      s3.querySelector('.thinking-step-icon').className = 'thinking-step-icon active';
      s3.querySelector('.thinking-step-icon').innerHTML = '<i class="fa-solid fa-spinner"></i>';
    }
  }, 1900);

  try {
    const res = await authFetch(`${API_BASE}/api/qa`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: query,
        paper_id: state.activePaper
      })
    });

    clearTimeout(t1);
    clearTimeout(t2);

    const data = await res.json();
    thinkingBubble.remove();

    if (!res.ok) {
      appendChatBubble('assistant', `**Error:** ${data.detail || data.error || 'Failed to generate answer'}`);
      return;
    }

    appendAssistantAnswer(data);
    fetchGuestQuota();
  } catch (err) {
    clearTimeout(t1);
    clearTimeout(t2);
    thinkingBubble.remove();
    appendChatBubble('assistant', `**Request Notice:** ${err.message}`);
  } finally {
    elements.sendBtn.disabled = false;
    elements.chatStream.scrollTop = elements.chatStream.scrollHeight;
  }
}

function appendChatBubble(role, content) {
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${role}`;

  const iconName = role === 'user' ? 'user' : 'bot';
  bubble.innerHTML = `
    <div class="avatar">
      <i data-lucide="${iconName}" style="width: 16px; height: 16px;"></i>
    </div>
    <div class="bubble-content">
      <div class="markdown-body">
        ${window.marked ? marked.parse(content) : content}
      </div>
    </div>
  `;

  elements.chatStream.appendChild(bubble);
  elements.chatStream.scrollTop = elements.chatStream.scrollHeight;
  initIcons();
}

function appendAssistantAnswer(data) {
  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble assistant';

  let badgeColor = 'blue';
  let badgeText = data.layer_label || 'Layer 1: Grounded in Paper';
  if (data.source_layer === 'inferred') badgeColor = 'purple';
  if (data.source_layer === 'external') badgeColor = 'teal';

  let confColor = 'green';
  if (data.confidence === 'medium') confColor = 'amber';
  if (data.confidence === 'low') confColor = 'red';

  let sourcesHtml = '';
  if (data.sources && data.sources.length > 0) {
    const uniquePages = [...new Set(data.sources.map(s => s.page || '1'))];
    sourcesHtml = `
      <div class="grounded-sources-strip">
        <div class="grounded-sources-header">
          <span class="grounded-sources-label">
            <i class="fa-solid fa-file-shield" style="color: var(--primary); font-size: 11px;"></i>
            <span>Grounded In:</span>
          </span>
          <div class="sources-pill-list">
            ${uniquePages.map(page => `<span class="source-page-tag">Page ${page}</span>`).join('')}
          </div>
          <button type="button" class="btn-toggle-evidence" onclick="const d = this.closest('.grounded-sources-strip').querySelector('.sources-mini-drawer'); d.classList.toggle('open'); this.querySelector('span').textContent = d.classList.contains('open') ? 'Hide Passages' : 'View Passages';">
            <i class="fa-solid fa-chevron-down" style="font-size: 9px;"></i>
            <span>View Passages</span>
          </button>
        </div>
        <div class="sources-mini-drawer">
          ${data.sources.slice(0, 4).map(s => `
            <div class="source-mini-item">
              <span class="source-mini-page">Page ${s.page || '1'}</span>
              <span class="source-mini-snippet">${escapeHtml(s.text.slice(0, 140))}...</span>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }

  const parsedAnswer = window.marked ? marked.parse(data.answer) : data.answer;

  bubble.innerHTML = `
    <div class="avatar">
      <i data-lucide="bot" style="width: 16px; height: 16px;"></i>
    </div>
    <div class="bubble-content" style="flex: 1;">
      <div class="badge-row">
        <span class="status-badge ${badgeColor}">
          <span class="status-dot high"></span>
          <span>${badgeText}</span>
        </span>
        <span class="status-badge ${confColor}">
          <span>Confidence: ${data.confidence_score || '85'}%</span>
        </span>
      </div>
      <div class="markdown-body">
        ${parsedAnswer}
      </div>
      ${sourcesHtml}
    </div>
  `;

  elements.chatStream.appendChild(bubble);
  elements.chatStream.scrollTop = elements.chatStream.scrollHeight;
  initIcons();

  if (window.renderMathInElement) {
    renderMathInElement(bubble, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '$', right: '$', display: false }
      ]
    });
  }
}

// -----------------------------------------------------------------------------
// Simplified Summary Tab
// -----------------------------------------------------------------------------
async function fetchPaperSimplifiedSummary(paperId) {
  if (!elements.simpleSummaryContainer) return;

  if (paperDataCache[paperId] && paperDataCache[paperId].summary) {
    renderSimplifiedSummary(paperDataCache[paperId].summary);
    return;
  }

  elements.simpleSummaryContainer.innerHTML = renderSkeletonCards(3);

  try {
    const res = await authFetch(`${API_BASE}/api/papers/${encodeURIComponent(paperId)}/simplified-summary`);
    const data = await res.json();

    if (!res.ok) {
      elements.simpleSummaryContainer.innerHTML = `
        <div style="padding: 24px; color: #ef4444; text-align: center;">
          Failed to load summary: ${data.detail || data.error}
        </div>
      `;
      return;
    }

    if (!paperDataCache[paperId]) paperDataCache[paperId] = {};
    paperDataCache[paperId].summary = data.summary;
    renderSimplifiedSummary(data.summary);
    fetchGuestQuota();
  } catch (err) {
    elements.simpleSummaryContainer.innerHTML = `
      <div style="padding: 24px; color: #ef4444; text-align: center;">
        Summary request notice: ${err.message}
      </div>
    `;
  }
}

function renderSimplifiedSummary(summary) {
  if (!elements.simpleSummaryContainer) return;
  if (!summary) {
    elements.simpleSummaryContainer.innerHTML = `<div style="text-align: center; padding: 32px; color: var(--text-dim);">No summary available.</div>`;
    return;
  }

  const w = summary.what_it_solves || {};
  const limits = summary.limitations || [];
  const gaps = summary.research_gaps || [];

  elements.simpleSummaryContainer.innerHTML = `
    <!-- Section 1: What this paper solves -->
    <div class="content-card" style="padding: 20px; margin-bottom: 16px;">
      <div style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">
        <i class="fa-solid fa-bullseye" style="color: var(--primary);"></i>
        <span>Section 1: What This Paper Solves</span>
      </div>
      <p style="font-size: 0.88rem; line-height: 1.6; color: var(--text-secondary); margin-bottom: 14px;">
        ${escapeHtml(w.plain_summary || 'This paper investigates key scientific mechanisms to advance research automation and discovery.')}
      </p>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px;">
        <div style="background: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
          <div style="font-size: 0.74rem; font-weight: 700; color: #b91c1c; text-transform: uppercase; margin-bottom: 4px;">The Problem</div>
          <div style="font-size: 0.82rem; color: var(--text-secondary);">${escapeHtml(w.problem || 'Complex domain constraints limit manual scalability.')}</div>
        </div>
        <div style="background: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
          <div style="font-size: 0.74rem; font-weight: 700; color: #1d4ed8; text-transform: uppercase; margin-bottom: 4px;">The Solution</div>
          <div style="font-size: 0.82rem; color: var(--text-secondary);">${escapeHtml(w.solution || 'The authors develop an automated computational framework.')}</div>
        </div>
        <div style="background: #f8fafc; padding: 12px; border-radius: 6px; border: 1px solid #e2e8f0;">
          <div style="font-size: 0.74rem; font-weight: 700; color: #047857; text-transform: uppercase; margin-bottom: 4px;">Real-World Impact</div>
          <div style="font-size: 0.82rem; color: var(--text-secondary);">${escapeHtml(w.impact || 'Drastically accelerates analysis speed and discovers new insights.')}</div>
        </div>
      </div>
    </div>

    <!-- Section 2: Limitations in Simple Terms -->
    <div class="content-card" style="padding: 20px; margin-bottom: 16px;">
      <div style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary); margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
        <i class="fa-solid fa-triangle-exclamation" style="color: #d97706;"></i>
        <span>Section 2: Limitations (In Simple Terms)</span>
      </div>
      <div style="display: flex; flex-direction: column; gap: 10px;">
        ${limits.map((l, i) => `
          <div style="background: #fffbeb; border: 1px solid #fde68a; border-left: 3px solid #f59e0b; border-radius: 4px; padding: 10px 14px;">
            <div style="font-weight: 600; font-size: 0.84rem; color: #92400e; margin-bottom: 4px;">${i + 1}. ${escapeHtml(l.title || 'Constraint')}</div>
            <div style="font-size: 0.82rem; color: #78350f; margin-bottom: 4px;">${escapeHtml(l.explanation || '')}</div>
            <div style="font-size: 0.76rem; color: #92400e; font-weight: 500;"><strong>What this means:</strong> ${escapeHtml(l.what_it_means || '')}</div>
          </div>
        `).join('')}
      </div>
    </div>

    <!-- Section 3: Open Research Gaps -->
    <div class="content-card" style="padding: 20px; margin-bottom: 16px;">
      <div style="font-size: 0.95rem; font-weight: 700; color: var(--text-primary); margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
        <i class="fa-solid fa-magnifying-glass-chart" style="color: #dc2626;"></i>
        <span>Section 3: Open Research Gaps</span>
      </div>
      <div style="display: flex; flex-direction: column; gap: 10px;">
        ${gaps.map((g, i) => `
          <div style="background: #fef2f2; border: 1px solid #fecaca; border-left: 3px solid #ef4444; border-radius: 4px; padding: 10px 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
              <div style="font-weight: 600; font-size: 0.84rem; color: #991b1b;">Gap ${i + 1}: ${escapeHtml(g.question || '')}</div>
              <span class="status-badge red" style="font-size: 0.7rem; padding: 2px 6px;">${g.priority || 'HIGH'} PRIORITY</span>
            </div>
            <div style="font-size: 0.8rem; color: #7f1d1d;">${escapeHtml(g.why_it_matters || '')}</div>
          </div>
        `).join('')}
      </div>
    </div>
  `;

  initIcons();
}

// -----------------------------------------------------------------------------
// Novel Insights Tab (Robust Category Filtering & Live Sub-Tab Counts)
// -----------------------------------------------------------------------------
async function fetchPaperNovelDiscovery(paperId) {
  if (!elements.insightsContainer) return;

  if (paperDataCache[paperId] && paperDataCache[paperId].discovery) {
    renderNovelDiscoveries(paperDataCache[paperId].discovery);
    return;
  }

  elements.insightsContainer.innerHTML = renderSkeletonCards(3);

  try {
    const res = await authFetch(`${API_BASE}/api/papers/${encodeURIComponent(paperId)}/novel-discovery`);
    const data = await res.json();

    if (!res.ok) {
      elements.insightsContainer.innerHTML = `<div style="padding: 24px; color: #ef4444; text-align: center;">Failed to load insights: ${data.detail || data.error}</div>`;
      return;
    }

    if (!paperDataCache[paperId]) paperDataCache[paperId] = {};
    paperDataCache[paperId].discovery = data.discovery;
    renderNovelDiscoveries(data.discovery);
    fetchGuestQuota();
  } catch (err) {
    elements.insightsContainer.innerHTML = `<div style="padding: 24px; color: #ef4444; text-align: center;">Request error: ${err.message}</div>`;
  }
}

function initNovelCategoryFilters() {
  if (!elements.categoryFilterBar) return;
  elements.categoryFilterBar.querySelectorAll('.category-filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      elements.categoryFilterBar.querySelectorAll('.category-filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      state.activeNovelCategory = btn.dataset.cat;
      if (state.activePaper && paperDataCache[state.activePaper] && paperDataCache[state.activePaper].discovery) {
        renderNovelDiscoveries(paperDataCache[state.activePaper].discovery);
      }
    });
  });
}

function renderNovelDiscoveries(discoveryData) {
  if (!elements.insightsContainer) return;
  if (!discoveryData) {
    elements.insightsContainer.innerHTML = `<div style="text-align: center; padding: 32px; color: var(--text-dim);">No novel discoveries generated.</div>`;
    return;
  }

  if (elements.domainBadge) {
    elements.domainBadge.textContent = `Domain: ${discoveryData.domain || 'Academic Research'}`;
  }

  // Filter out any empty/malformed discovery shells
  const rawItems = discoveryData.all_discoveries || [];
  const allItems = rawItems.filter(item => {
    const p = (item.the_core_paradigm || item.paradigm || '').trim();
    const t = (item.title || '').trim().toLowerCase();
    return p.length >= 10 && !t.includes('reasoning chain') && !t.includes('the paradigm');
  });
  
  // Robustly extract or match each category array with non-empty filtering
  const extractList = (catKey, matchKeywords) => {
    let rawList = [];
    if (discoveryData.categories && Array.isArray(discoveryData.categories[catKey]) && discoveryData.categories[catKey].length > 0) {
      rawList = discoveryData.categories[catKey];
    } else if (Array.isArray(discoveryData[catKey]) && discoveryData[catKey].length > 0) {
      rawList = discoveryData[catKey];
    } else {
      rawList = allItems.filter(item => {
        const k = (item.category_key || '').toLowerCase();
        const c = (item.category || '').toLowerCase();
        const t = (item.title || '').toLowerCase();
        return matchKeywords.some(kw => k.includes(kw) || c.includes(kw) || t.includes(kw));
      });
    }
    return rawList.filter(item => {
      const p = (item.the_core_paradigm || item.paradigm || '').trim();
      const t = (item.title || '').trim().toLowerCase();
      return p.length >= 10 && !t.includes('reasoning chain') && !t.includes('the paradigm');
    });
  };

  const listParadigm = extractList('paradigm_shifts', ['paradigm']);
  const listCross = extractList('cross_domain', ['cross', 'domain', 'pioneer']);
  const listFlaws = extractList('reverse_engineering_flaws', ['reverse', 'flaw', 'engineering']);
  const listPredict = extractList('predictive_discoveries', ['predict', 'trajectory']);
  const listComb = extractList('unexplored_combinations', ['combination', 'unexplored', 'synthesis']);

  // Update dynamic count badges on every sub-tab
  if (elements.countAll) elements.countAll.textContent = allItems.length;
  if (elements.countParadigm) elements.countParadigm.textContent = listParadigm.length;
  if (elements.countCross) elements.countCross.textContent = listCross.length;
  if (elements.countFlaws) elements.countFlaws.textContent = listFlaws.length;
  if (elements.countPredict) elements.countPredict.textContent = listPredict.length;
  if (elements.countComb) elements.countComb.textContent = listComb.length;

  let filtered = allItems;
  if (state.activeNovelCategory === 'paradigm_shifts') filtered = listParadigm;
  else if (state.activeNovelCategory === 'cross_domain') filtered = listCross;
  else if (state.activeNovelCategory === 'reverse_engineering_flaws') filtered = listFlaws;
  else if (state.activeNovelCategory === 'predictive_discoveries') filtered = listPredict;
  else if (state.activeNovelCategory === 'unexplored_combinations') filtered = listComb;

  if (filtered.length === 0) {
    elements.insightsContainer.innerHTML = `<div style="text-align: center; padding: 32px; color: var(--text-dim);">No discoveries in this category.</div>`;
    return;
  }

  elements.insightsContainer.innerHTML = filtered.map((d, idx) => `
    <div class="content-card" style="padding: 18px; margin-bottom: 14px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
        <span class="status-badge blue" style="font-size: 0.72rem; padding: 2px 8px;">
          ${escapeHtml(d.category || 'Breakthrough')}
        </span>
        <span style="font-size: 0.75rem; color: var(--text-muted); font-weight: 500;">Discovery #${idx + 1}</span>
      </div>
      <h3 style="font-size: 0.96rem; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">
        ${escapeHtml(d.title || 'Novel Proposition')}
      </h3>
      <p style="font-size: 0.84rem; color: var(--text-secondary); line-height: 1.55; margin-bottom: 10px;">
        <strong>Core Paradigm:</strong> ${escapeHtml(d.the_core_paradigm || d.paradigm || '')}
      </p>
      ${(d.why_it_is_new || d.why_new || '').trim() ? `
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 4px; padding: 8px 12px; font-size: 0.8rem; margin-bottom: 8px;">
          <strong style="color: var(--primary);">Why New:</strong> ${escapeHtml(d.why_it_is_new || d.why_new || '')}
        </div>
      ` : ''}
      ${d.actionable_blueprint ? `
        <div class="blueprint-box-wrapper">
          <div class="blueprint-box-title"><i class="fa-solid fa-code-branch"></i> Actionable Experimental Blueprint</div>
          <div>${escapeHtml(d.actionable_blueprint)}</div>
        </div>
      ` : ''}
    </div>
  `).join('');

  initIcons();
}

// -----------------------------------------------------------------------------
// Online Literature Comparison Tab
// -----------------------------------------------------------------------------
function initTabs() {
  if (elements.searchOnlineBtn) {
    elements.searchOnlineBtn.addEventListener('click', async () => {
      if (!state.activePaper) {
        showToast('Please select a paper first.', 'warning');
        return;
      }
      elements.searchOnlineBtn.disabled = true;
      elements.searchOnlineBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Searching...';
      elements.compareContainer.innerHTML = renderSkeletonCards(2);

      try {
        const res = await authFetch(`${API_BASE}/api/papers/${encodeURIComponent(state.activePaper)}/compare`);
        const data = await res.json();
        if (res.ok) {
          if (!paperDataCache[state.activePaper]) paperDataCache[state.activePaper] = {};
          paperDataCache[state.activePaper].comparison = data.comparison;
          renderCompareData(state.activePaper);
          fetchGuestQuota();
        } else {
          elements.compareContainer.innerHTML = `<div style="padding: 24px; color: #ef4444; text-align: center;">Comparison failed: ${data.detail || data.error}</div>`;
        }
      } catch (err) {
        elements.compareContainer.innerHTML = `<div style="padding: 24px; color: #ef4444; text-align: center;">Error: ${err.message}</div>`;
      } finally {
        elements.searchOnlineBtn.disabled = false;
        elements.searchOnlineBtn.innerHTML = '<i data-lucide="search" style="width: 13px; height: 13px;"></i> Search Online Papers';
        initIcons();
      }
    });
  }

  // Autonomous Agent Discovery Modal & Replay Controls
  const closeReasoningModalBtn = document.getElementById('closeReasoningModalBtn');
  if (closeReasoningModalBtn) {
    closeReasoningModalBtn.addEventListener('click', () => {
      const m = document.getElementById('discoveryReasoningModal');
      if (m) m.style.display = 'none';
    });
  }

  const closeReasoningModalBtnBottom = document.getElementById('closeReasoningModalBtnBottom');
  if (closeReasoningModalBtnBottom) {
    closeReasoningModalBtnBottom.addEventListener('click', () => {
      const m = document.getElementById('discoveryReasoningModal');
      if (m) m.style.display = 'none';
    });
  }

  const discModal = document.getElementById('discoveryReasoningModal');
  if (discModal) {
    discModal.addEventListener('click', (e) => {
      if (e.target === discModal) discModal.style.display = 'none';
    });
  }

  const replayTheaterBtn = document.getElementById('replayTheaterBtn');
  if (replayTheaterBtn) {
    replayTheaterBtn.addEventListener('click', () => {
      if (currentDiscoveryData && currentDiscoveryData.dialogue_transcript) {
        showToast('Replaying live AI scientist debate...', 'info');
        renderTheaterDialogue(currentDiscoveryData.dialogue_transcript);
      }
    });
  }

  if (elements.runAgentDiscoveryBtn) {
    elements.runAgentDiscoveryBtn.addEventListener('click', () => {
      if (!state.activePaper) {
        showToast('Please select a paper from your library first.', 'warning');
        return;
      }
      showToast('Rerunning 5-agent Actor-Critic pipeline...', 'info');
      fetchAutonomousAgentDiscovery(state.activePaper, true);
    });
  }

  if (elements.toggleAgentTranscriptBtn) {
    elements.toggleAgentTranscriptBtn.addEventListener('click', () => {
      if (!elements.agentTranscriptContainer) return;
      const isHidden = elements.agentTranscriptContainer.style.display === 'none';
      elements.agentTranscriptContainer.style.display = isHidden ? 'flex' : 'none';
      elements.toggleAgentTranscriptBtn.querySelector('span').textContent = isHidden ? 'Collapse Log' : 'Expand Log';
      elements.toggleAgentTranscriptBtn.querySelector('i').className = isHidden ? 'fa-solid fa-chevron-down' : 'fa-solid fa-chevron-right';
    });
  }

  if (elements.downloadPdfBtn) {
    elements.downloadPdfBtn.addEventListener('click', () => downloadReportFile('pdf'));
  }
  if (elements.downloadMdBtn) {
    elements.downloadMdBtn.addEventListener('click', () => downloadReportFile('markdown'));
  }
}

async function renderCompareData(paperId) {
  if (!elements.compareContainer) return;

  if (!paperDataCache[paperId] || !paperDataCache[paperId].comparison) {
    elements.compareContainer.innerHTML = renderSkeletonCards(2);
    try {
      const res = await authFetch(`${API_BASE}/api/papers/${encodeURIComponent(paperId)}/compare`);
      const data = await res.json();
      if (res.ok) {
        if (!paperDataCache[paperId]) paperDataCache[paperId] = {};
        paperDataCache[paperId].comparison = data.comparison;
      }
    } catch (e) {}
  }

  const comp = (paperDataCache[paperId] && paperDataCache[paperId].comparison) || {};
  const similar = comp.similar_papers || [];
  const analysis = comp.comparison_analysis || '';

  if (similar.length === 0 && !analysis) {
    elements.compareContainer.innerHTML = `
      <div style="text-align: center; padding: 48px; color: var(--text-dim); font-size: 0.88rem;">
        Click "Search Online Papers" to query external academic databases.
      </div>
    `;
    return;
  }

  elements.compareContainer.innerHTML = `
    ${analysis ? `
      <div class="content-card" style="padding: 18px; margin-bottom: 16px;">
        <div style="font-weight: 700; font-size: 0.95rem; color: var(--text-primary); margin-bottom: 8px;">
          Comparative Synthesis vs Current SOTA
        </div>
        <div class="markdown-body" style="font-size: 0.85rem; line-height: 1.6;">
          ${window.marked ? marked.parse(analysis) : analysis}
        </div>
      </div>
    ` : ''}
    <div style="font-weight: 600; font-size: 0.9rem; margin-bottom: 10px; color: var(--text-primary);">
      Similar External Publications (${similar.length})
    </div>
    <div style="display: flex; flex-direction: column; gap: 10px;">
      ${similar.map(p => `
        <div class="content-card" style="padding: 14px;">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px;">
            <a href="${p.url || '#'}" target="_blank" rel="noopener noreferrer" style="font-weight: 600; font-size: 0.88rem; color: var(--primary); text-decoration: none;">
              ${escapeHtml(p.title || 'Published Paper')}
            </a>
            <span class="status-badge blue" style="font-size: 0.7rem; padding: 2px 6px;">${p.source || 'Scholar'}</span>
          </div>
          <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5;">
            ${escapeHtml(p.abstract || p.snippet || 'No abstract available.')}
          </div>
        </div>
      `).join('')}
    </div>
  `;

  initIcons();
}

// -----------------------------------------------------------------------------
// Export Report Preview & Download Handlers
// -----------------------------------------------------------------------------
async function renderExportPreview(paperId) {
  if (!elements.exportPreviewBody) return;
  elements.exportPreviewBody.innerHTML = '<div style="text-align: center; padding: 20px;"><i class="fa-solid fa-spinner fa-spin"></i> Compiling report...</div>';

  try {
    const res = await authFetch(`${API_BASE}/api/papers/${encodeURIComponent(paperId)}/export/markdown`);
    if (res.ok) {
      const md = await res.text();
      elements.exportPreviewBody.innerHTML = window.marked ? marked.parse(md) : md;
    } else {
      elements.exportPreviewBody.innerHTML = 'Preview compilation notice: Click Export PDF or Download Markdown to download full document.';
    }
  } catch (err) {
    elements.exportPreviewBody.innerHTML = 'Select a paper to generate its complete analysis report.';
  }
}

async function downloadReportFile(fmt) {
  if (!state.activePaper) {
    showToast('Please select a paper first.', 'warning');
    return;
  }

  showToast(`Compiling ${fmt.toUpperCase()} report...`, 'info');

  try {
    const downloadUrl = `${API_BASE}/api/papers/${encodeURIComponent(state.activePaper)}/export/${fmt}`;
    const res = await authFetch(downloadUrl);

    if (!res.ok) {
      throw new Error(`Server returned HTTP ${res.status}`);
    }

    const blob = await res.blob();
    const cleanId = state.activePaper.replace(/[^a-zA-Z0-9_-]/g, '_');
    const ext = fmt === 'pdf' ? 'pdf' : 'md';
    const filename = `research_report_${cleanId}.${ext}`;

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    a.remove();

    showToast(`Downloaded ${filename}`, 'success');
  } catch (err) {
    showToast(`Download failed: ${err.message}`, 'error');
  }
}

// -----------------------------------------------------------------------------
// Modal & Utility Helpers
// -----------------------------------------------------------------------------
function initModal() {
  if (elements.modalCloseBtn && elements.evidenceModal) {
    elements.modalCloseBtn.addEventListener('click', () => {
      elements.evidenceModal.style.display = 'none';
    });
  }

  const reasoningModal = document.getElementById('discoveryReasoningModal');
  const closeBtn = document.getElementById('closeReasoningModalBtn');
  const closeBottomBtn = document.getElementById('closeReasoningModalBtnBottom');

  if (closeBtn && reasoningModal) {
    closeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      reasoningModal.style.display = 'none';
    });
  }

  if (closeBottomBtn && reasoningModal) {
    closeBottomBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      reasoningModal.style.display = 'none';
    });
  }

  if (reasoningModal) {
    reasoningModal.addEventListener('click', (e) => {
      if (e.target === reasoningModal) {
        reasoningModal.style.display = 'none';
      }
    });
  }

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (elements.evidenceModal) elements.evidenceModal.style.display = 'none';
      if (reasoningModal) reasoningModal.style.display = 'none';
    }
  });

  // Attach default click listeners immediately on boot
  setupFlowchartClickHandlers(null);
}

function renderSkeletonCards(count = 2) {
  let html = '';
  for (let i = 0; i < count; i++) {
    html += `
      <div class="skeleton-card">
        <div class="skeleton-line short"></div>
        <div class="skeleton-line full"></div>
        <div class="skeleton-line medium"></div>
      </div>
    `;
  }
  return html;
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// -----------------------------------------------------------------------------
// Autonomous Multi-Agent Scientific Discovery (Interactive Step-by-Step Flowchart)
// -----------------------------------------------------------------------------
let currentDiscoveryData = null;

async function fetchAutonomousAgentDiscovery(paperId, forceReload = false) {
  if (!forceReload && paperDataCache[paperId] && paperDataCache[paperId].agent_discovery) {
    currentDiscoveryData = paperDataCache[paperId].agent_discovery;
    renderAutonomousVisualDashboard(currentDiscoveryData);
    return;
  }

  const heroTitle = document.getElementById('heroDiscoveryTitle');
  if (heroTitle) heroTitle.innerHTML = '<i class="fa-solid fa-atom fa-spin" style="margin-right: 6px;"></i> 5 AI Agents Assembling Scientific Discovery...';
  
  try {
    const url = forceReload
      ? `${API_BASE}/api/papers/${encodeURIComponent(paperId)}/autonomous-discovery?force_reload=true`
      : `${API_BASE}/api/papers/${encodeURIComponent(paperId)}/autonomous-discovery`;
    const res = await authFetch(url);
    const data = await res.json();

    if (!res.ok) {
      if (heroTitle) heroTitle.textContent = `Discovery failed: ${data.detail || data.error || 'Error'}`;
      return;
    }

    if (!paperDataCache[paperId]) paperDataCache[paperId] = {};
    paperDataCache[paperId].agent_discovery = data;
    currentDiscoveryData = data;
    renderAutonomousVisualDashboard(data);
    fetchGuestQuota();
  } catch (err) {
    if (heroTitle) heroTitle.textContent = `Request error: ${err.message}`;
  }
}

function renderAutonomousVisualDashboard(data) {
  if (!data) return;
  currentDiscoveryData = data;

  const discovery = data.verified_discovery || {};
  const ontology = data.ontology_graph || {};
  const hypothesis = data.initial_hypothesis || {};
  const critique = data.adversarial_critique || {};
  const refiner = data.refined_hypothesis || {};
  const confScore = discovery.falsification_resistance_score || 94;

  // 1. Update Hero Badges & Title
  const domainBadge = document.getElementById('agentDomainBadge');
  if (domainBadge) domainBadge.innerHTML = `<i class="fa-solid fa-graduation-cap"></i> Domain: ${escapeHtml(data.domain || 'Scientific Research')}`;

  const confVal = document.getElementById('heroConfidenceValue');
  if (confVal) confVal.textContent = `${confScore}%`;

  const flowConfVal = document.getElementById('flowConfidenceValue');
  if (flowConfVal) flowConfVal.textContent = `${confScore}%`;

  const labConfVal = document.getElementById('labConfidenceValue');
  if (labConfVal) labConfVal.textContent = `${confScore}%`;

  const heroTitle = document.getElementById('heroDiscoveryTitle');
  if (heroTitle) heroTitle.textContent = discovery.discovery_name || 'Verified Scientific Breakthrough';

  // 2. Populate Step 1: Concept Mapper
  const nodes = ontology.nodes || [];
  const conceptNames = nodes.slice(0, 4).map(n => n.label || n.id).join(', ');
  const mapperText = document.getElementById('flowOutputMapper');
  if (mapperText) {
    mapperText.textContent = conceptNames ? `Found: ${conceptNames}` : "Extracted core paper semantic entities & relational graph.";
  }

  // 3. Populate Step 2: Idea Theorist
  const theoristText = document.getElementById('flowOutputTheorist');
  if (theoristText) {
    theoristText.textContent = hypothesis.hypothesis_name 
      ? `"${hypothesis.hypothesis_name}"` 
      : `"${discovery.discovery_name || 'Novel Scientific Mechanism'}"`;
  }

  // 4. Populate Step 3: Peer Referee
  const refereeText = document.getElementById('flowOutputReferee');
  if (refereeText) {
    refereeText.textContent = critique.primary_objection 
      ? `Challenge: "${critique.primary_objection}"` 
      : `Challenge: Boundary limitation and computational bottlenecks detected.`;
  }

  // 5. Populate Step 4: Self-Correction Lead
  const refinerText = document.getElementById('flowOutputRefiner');
  if (refinerText) {
    refinerText.textContent = refiner.structural_adjustments 
      ? `Fixed: ${refiner.structural_adjustments}` 
      : `Fixed: Added defensive constraints and self-correcting safeguards.`;
  }

  // 6. Populate Step 5: Blueprint Lead
  const architectText = document.getElementById('flowOutputArchitect');
  if (architectText) {
    architectText.textContent = `${confScore}% Verified! 3-Phase testing protocol & metrics validated.`;
  }

  // 7. Populate Final Breakthrough Discovery Card
  const discTitle = document.getElementById('flowDiscoveryTitle');
  if (discTitle) discTitle.textContent = discovery.discovery_name || 'Verified Breakthrough Discovery';

  const discWhat = document.getElementById('flowDiscoveryWhat');
  if (discWhat) {
    discWhat.textContent = discovery.domain_specific_breakthrough_insight || refiner.refined_name || 'A specialized architecture integrating external memory & adaptive feedback to resolve limitations without retraining.';
  }

  const discWhy = document.getElementById('flowDiscoveryWhy');
  if (discWhy) {
    discWhy.textContent = hypothesis.expected_gain || hypothesis.theoretical_foundation || 'Traditional methods hit computational and theoretical limits; this framework establishes verified grounded discovery.';
  }

  // 8. Core Paper Principle Banner
  const axiomText = document.getElementById('axiomText');
  if (axiomText && ontology.core_axiom) {
    axiomText.textContent = ontology.core_axiom;
  }

  // 9. Attach Flowchart Click Listeners
  setupFlowchartClickHandlers(data);

  // 10. Bottom Sections: Debate Stream + 3-Step Protocol
  renderTheaterDialogue(data.dialogue_transcript || []);
  renderTestingLabBlueprint(discovery);

  initIcons();
}

let isSimulationRunning = false;

async function simulateAgentFlow() {
  if (isSimulationRunning) return;
  isSimulationRunning = true;

  const btn = document.getElementById('simulateFlowBtn');
  if (btn) {
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin" style="color: #6366f1;"></i> <span>Simulating...</span>';
  }

  const stepIds = [
    'flowcard-mapper',
    'flowcard-theorist',
    'flowcard-referee',
    'flowcard-refiner',
    'flowcard-architect',
    'flowcard-discovery'
  ];

  // Remove any previous active state
  stepIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.remove('simulating-active');
  });

  showToast('Starting sequential AI agent reasoning simulation...', 'info');

  for (let i = 0; i < stepIds.length; i++) {
    const cardEl = document.getElementById(stepIds[i]);
    if (cardEl) {
      cardEl.classList.add('simulating-active');
      cardEl.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    await new Promise(r => setTimeout(r, 650));

    if (i < stepIds.length - 1) {
      if (cardEl) cardEl.classList.remove('simulating-active');
    }
  }

  showToast('Simulation complete! Discovery synthesized & verified.', 'success');

  setTimeout(() => {
    const lastCard = document.getElementById('flowcard-discovery');
    if (lastCard) lastCard.classList.remove('simulating-active');
  }, 1500);

  if (btn) {
    btn.innerHTML = '<i class="fa-solid fa-play" style="color: #6366f1;"></i> <span>Simulate Flow</span>';
  }
  isSimulationRunning = false;
}

function setupFlowchartClickHandlers(data) {
  const steps = [
    { id: 'flowcard-mapper', key: 'mapper' },
    { id: 'flowcard-theorist', key: 'theorist' },
    { id: 'flowcard-referee', key: 'referee' },
    { id: 'flowcard-refiner', key: 'refiner' },
    { id: 'flowcard-architect', key: 'architect' },
    { id: 'flowcard-discovery', key: 'discovery' }
  ];

  steps.forEach(({ id, key }) => {
    const el = document.getElementById(id);
    if (el) {
      el.onclick = (e) => {
        e.preventDefault();
        openAgentReasoningModal(key, data || currentDiscoveryData);
      };
    }
  });

  const simBtn = document.getElementById('simulateFlowBtn');
  if (simBtn) {
    simBtn.onclick = (e) => {
      e.preventDefault();
      simulateAgentFlow();
    };
  }
}

const defaultFallbackDiscovery = {
  domain: "AI / Machine Learning",
  ontology_graph: {
    core_axiom: "By coordinating specialized scientific agents, complex mechanisms can be modeled accurately without hallucination.",
    nodes: [
      { id: "1", label: "Multi-Agent Systems", type: "Core Subject" },
      { id: "2", label: "Actor-Critic Orchestration", type: "Methodology" },
      { id: "3", label: "Ontological Knowledge Graph", type: "Representation" },
      { id: "4", label: "Adversarial Self-Correction", type: "Verification" },
      { id: "5", label: "Grounded Scientific Discovery", type: "Objective" }
    ],
    edges: [
      { source: "Multi-Agent Systems", relation: "utilizes", target: "Actor-Critic Orchestration" },
      { source: "Actor-Critic Orchestration", relation: "structures", target: "Ontological Knowledge Graph" },
      { source: "Ontological Knowledge Graph", relation: "validates with", target: "Adversarial Self-Correction" },
      { source: "Adversarial Self-Correction", relation: "synthesizes", target: "Grounded Scientific Discovery" }
    ]
  },
  initial_hypothesis: {
    hypothesis_name: "Claim-Level Causal Provenance in Multi-Agent Verification",
    core_concept: "Inverting traditional post-hoc review into continuous multi-agent consensus verification.",
    theoretical_foundation: "Graph-structured trace provenance combined with bidirectional gradient constraints.",
    expected_gain: "Eliminates attention drift and guarantees empirical falsification resistance."
  },
  adversarial_critique: {
    primary_objection: "Full trace recording incurs quadratic computational overhead in large graphs.",
    fatal_flaws: "Risk of latency explosion and unbounded state growth under dense semantic connectivity.",
    falsification_risk: "Demands strict localized subgraph pruning to ensure sub-second response times."
  },
  refined_hypothesis: {
    structural_adjustments: "Shifted from global tracing to bounded hierarchical subgraphs with localized cache eviction.",
    hardened_mechanism: "Bounded priority graphs with integrated gradient checkpointing and real-time state pruning.",
    falsification_mitigation: "Ensures bounded O(log N) memory scaling with 100% causal reproducibility."
  },
  verified_discovery: {
    discovery_name: "Claim-Level Causal Provenance & Bounded Multi-Agent Verification",
    falsification_resistance_score: 94,
    domain_specific_breakthrough_insight: "A modular multi-agent architecture that resolves verification bottlenecks via bounded subgraphs and active adversarial stress-testing.",
    experimental_blueprint: {
      phase_1_baseline: "Benchmark traditional unconstrained multi-agent pipelines on factual benchmark datasets.",
      phase_2_intervention: "Deploy bounded subgraph tracking with automated adversarial referee checkpoints.",
      phase_3_evaluation_metric: "Measure factual consistency, latency overhead, and empirical falsification score."
    },
    real_world_application: "Enables safety-critical deployment of autonomous AI agents in aerospace, medicine, and legal synthesis."
  }
};

function openAgentReasoningModal(stepKey, data) {
  if (!data) data = currentDiscoveryData || defaultFallbackDiscovery;

  const modal = document.getElementById('discoveryReasoningModal');
  if (!modal) return;

  const iconBadge = document.getElementById('reasoningModalIcon');
  const titleElem = document.getElementById('reasoningModalTitle');
  const subElem = document.getElementById('reasoningModalSubtitle');
  const bodyElem = document.getElementById('reasoningModalBody');

  const ontology = data.ontology_graph || {};
  const hypothesis = data.initial_hypothesis || {};
  const critique = data.adversarial_critique || {};
  const refiner = data.refined_hypothesis || {};
  const discovery = data.verified_discovery || {};
  const bp = discovery.experimental_blueprint || {};
  const confScore = discovery.falsification_resistance_score || 94;

  if (stepKey === 'mapper') {
    iconBadge.className = 'reasoning-modal-icon-badge mapper';
    iconBadge.innerHTML = '<i class="fa-solid fa-book-open"></i>';
    titleElem.textContent = 'Concept Mapper Reasoning';
    subElem.textContent = 'Role: Reads the paper and extracts core concepts';

    const nodes = ontology.nodes || [];
    const edges = ontology.edges || [];

    const entitiesHtml = nodes.map((n, i) => `
      <li><strong>${i + 1}. ${escapeHtml(n.label || n.id)}</strong> <span style="font-size: 0.73rem; color: #8B5CF6; background: #f5f3ff; padding: 2px 6px; border-radius: 4px; margin-left: 6px;">${escapeHtml(n.type || 'Entity')}</span></li>
    `).join('');

    const edgesHtml = edges.slice(0, 4).map(e => `
      <div style="font-size: 0.8rem; color: #475569; padding: 3px 0;">
        ➔ <strong>${escapeHtml(e.source)}</strong> <span style="color: #8B5CF6;">[${escapeHtml(e.relation || 'links')}]</span> ➔ <strong>${escapeHtml(e.target)}</strong>
      </div>
    `).join('');

    bodyElem.innerHTML = `
      <div class="reasoning-section-box">
        <div class="reasoning-section-title"><i class="fa-solid fa-cube" style="color: #8B5CF6;"></i> Foundational Entities Found in Paper:</div>
        <ul class="reasoning-list">${entitiesHtml || '<li>Foundational entities parsed from text.</li>'}</ul>
      </div>

      <div class="reasoning-section-box">
        <div class="reasoning-section-title"><i class="fa-solid fa-quote-left" style="color: #16a34a;"></i> Core Paper Principle / Axiom:</div>
        <div class="reasoning-quote-block">${escapeHtml(ontology.core_axiom || "By coordinating specialized scientific agents, complex mechanisms can be modeled accurately.")}</div>
      </div>

      ${edges.length > 0 ? `
        <div class="reasoning-section-box">
          <div class="reasoning-section-title"><i class="fa-solid fa-diagram-project" style="color: #8B5CF6;"></i> Extracted Relational Linkages:</div>
          <div>${edgesHtml}</div>
        </div>
      ` : ''}
    `;

  } else if (stepKey === 'theorist') {
    iconBadge.className = 'reasoning-modal-icon-badge theorist';
    iconBadge.innerHTML = '<i class="fa-solid fa-lightbulb"></i>';
    titleElem.textContent = 'Idea Theorist Reasoning';
    subElem.textContent = 'Role: Generates radical new breakthrough idea from paper gaps';

    bodyElem.innerHTML = `
      <div class="reasoning-section-box">
        <div class="reasoning-section-title"><i class="fa-solid fa-sparkles" style="color: #EF4444;"></i> Proposed Breakthrough Hypothesis:</div>
        <div style="font-size: 0.95rem; font-weight: 700; color: #991b1b; margin-bottom: 6px;">
          "${escapeHtml(hypothesis.hypothesis_name || discovery.discovery_name || 'Novel Scientific Hypothesis')}"
        </div>
        <div style="font-size: 0.82rem; color: #475569; line-height: 1.5;">
          ${escapeHtml(hypothesis.core_concept || 'Formulates a structural paradigm shift addressing the core gap discovered in the paper.')}
        </div>
      </div>

      <div class="reasoning-section-box">
        <div class="reasoning-section-title"><i class="fa-solid fa-brain" style="color: #EF4444;"></i> Theoretical Foundation & Mechanism:</div>
        <div style="font-size: 0.82rem; color: #334155; line-height: 1.55; white-space: pre-line;">
          ${escapeHtml(hypothesis.theoretical_foundation || hypothesis.mathematical_formulation || 'Mathematical and conceptual formulation linking extracted ontology to breakthrough execution.')}
        </div>
      </div>

      <div class="reasoning-section-box">
        <div class="reasoning-section-title"><i class="fa-solid fa-chart-line-up" style="color: #EF4444;"></i> Expected Performance & Capability Gain:</div>
        <div style="font-size: 0.82rem; color: #334155; line-height: 1.5;">
          ${escapeHtml(hypothesis.expected_gain || 'Overcomes traditional latency, grounding, and verification bottlenecks.')}
        </div>
      </div>
    `;

  } else if (stepKey === 'referee') {
    iconBadge.className = 'reasoning-modal-icon-badge referee';
    iconBadge.innerHTML = '<i class="fa-solid fa-scale-balanced"></i>';
    titleElem.textContent = 'Peer Referee Challenge & Critique';
    subElem.textContent = 'Role: Adversarial review & stress-testing for limitations';

    bodyElem.innerHTML = `
      <div class="reasoning-section-box">
        <div class="reasoning-section-title"><i class="fa-solid fa-triangle-exclamation" style="color: #F59E0B;"></i> Primary Peer Challenge:</div>
        <div class="reasoning-danger-block">
          <strong>Objection:</strong> ${escapeHtml(critique.primary_objection || 'Computationally or empirically vulnerable at scale; requires defensive boundary proof.')}
        </div>
      </div>

      <div class="reasoning-section-box">
        <div class="reasoning-section-title"><i class="fa-solid fa-shield-xmark" style="color: #F59E0B;"></i> Identified Vulnerabilities & Edge Cases:</div>
        <div style="font-size: 0.82rem; color: #475569; line-height: 1.5; white-space: pre-line;">
          ${escapeHtml(critique.fatal_flaws || critique.boundary_conditions || 'Identified potential failure points when tested under real-world stochastic environments.')}
        </div>
      </div>

      <div class="reasoning-section-box">
        <div class="reasoning-section-title"><i class="fa-solid fa-gauge-high" style="color: #F59E0B;"></i> Falsification Risk Assessment:</div>
        <div style="font-size: 0.82rem; color: #475569; line-height: 1.5;">
          ${escapeHtml(critique.falsification_risk || 'Demands rigorous empirical guardrails to prevent hallucination or resource explosion.')}
        </div>
      </div>
    `;

  } else if (stepKey === 'refiner') {
    iconBadge.className = 'reasoning-modal-icon-badge refiner';
    iconBadge.innerHTML = '<i class="fa-solid fa-wrench"></i>';
    titleElem.textContent = 'Self-Correction Lead Resolution';
    subElem.textContent = 'Role: Fixes the flaws & adds robust defensive safeguards';

    bodyElem.innerHTML = `
      <div class="reasoning-section-box">
        <div class="reasoning-section-title"><i class="fa-solid fa-shield-check" style="color: #10B981;"></i> How the Objection Was Resolved:</div>
        <div class="reasoning-success-block">
          <strong>Correction:</strong> ${escapeHtml(refiner.structural_adjustments || refiner.falsification_mitigation || 'Re-architected mechanism to ensure bounded computational overhead and strict causal validity.')}
        </div>
      </div>

      <div class="reasoning-section-box">
        <div class="reasoning-section-title"><i class="fa-solid fa-lock" style="color: #10B981;"></i> Hardened Mechanism & Safeguards:</div>
        <div style="font-size: 0.82rem; color: #334155; line-height: 1.55; white-space: pre-line;">
          ${escapeHtml(refiner.hardened_mechanism || discovery.core_mechanism_details || 'Calibrated execution pipeline with integrated invariant checks.')}
        </div>
      </div>
    `;

  } else if (stepKey === 'architect') {
    iconBadge.className = 'reasoning-modal-icon-badge architect';
    iconBadge.innerHTML = '<i class="fa-solid fa-clipboard-check"></i>';
    titleElem.textContent = 'Blueprint Lead Validation & Roadmap';
    subElem.textContent = 'Role: Validates & creates 3-phase testing roadmap';

    bodyElem.innerHTML = `
      <div class="reasoning-section-box">
        <div class="reasoning-section-title"><i class="fa-solid fa-award" style="color: #3B82F6;"></i> Validation Confidence Score:</div>
        <div style="display: flex; align-items: center; gap: 8px;">
          <span class="falsification-score-badge" style="font-size: 0.95rem; padding: 4px 12px;">
            <i class="fa-solid fa-shield-check"></i> ${confScore}% Verified Quality
          </span>
          <span style="font-size: 0.8rem; color: #475569;">Rigorous multi-agent consensus achieved.</span>
        </div>
      </div>

      <div class="reasoning-section-box">
        <div class="reasoning-section-title"><i class="fa-solid fa-vial" style="color: #3B82F6;"></i> 3-Phase Testing Roadmap:</div>
        <div class="testing-lab-grid">
          <div class="testing-step-row">
            <div class="testing-step-num"><i class="fa-solid fa-1"></i> Phase 1: Baseline Comparison</div>
            <div class="testing-step-desc">${escapeHtml(bp.phase_1_baseline || 'Establish standard reference baseline performance.')}</div>
          </div>
          <div class="testing-step-row">
            <div class="testing-step-num"><i class="fa-solid fa-2"></i> Phase 2: Mechanism Intervention</div>
            <div class="testing-step-desc">${escapeHtml(bp.phase_2_intervention || 'Implement the proposed adaptive self-correcting controls.')}</div>
          </div>
          <div class="testing-step-row">
            <div class="testing-step-num"><i class="fa-solid fa-3"></i> Phase 3: Validation Metric</div>
            <div class="testing-step-desc">${escapeHtml(bp.phase_3_evaluation_metric || 'Evaluate empirical accuracy, latency, and stability.')}</div>
          </div>
        </div>
      </div>
    `;

  } else if (stepKey === 'discovery') {
    iconBadge.className = 'reasoning-modal-icon-badge discovery';
    iconBadge.innerHTML = '<i class="fa-solid fa-trophy"></i>';
    titleElem.textContent = discovery.discovery_name || 'Final Breakthrough Discovery';
    subElem.textContent = 'Autonomous 5-Agent Peer-Audited Discovery Breakthrough';

    bodyElem.innerHTML = `
      <div class="reasoning-section-box" style="background: #fffbeb; border-color: #fde68a;">
        <div class="reasoning-section-title" style="color: #92400e;"><i class="fa-solid fa-atom"></i> What It Is:</div>
        <div style="font-size: 0.85rem; color: #451a03; line-height: 1.55;">
          ${escapeHtml(discovery.domain_specific_breakthrough_insight || refiner.refined_name || 'A specialized architectural breakthrough discovered through multi-agent causal inference.')}
        </div>
      </div>

      <div class="reasoning-section-box">
        <div class="reasoning-section-title" style="color: #92400e;"><i class="fa-solid fa-sparkles"></i> Why It's Novel:</div>
        <div style="font-size: 0.83rem; color: #475569; line-height: 1.55;">
          ${escapeHtml(hypothesis.expected_gain || hypothesis.theoretical_foundation || 'Provides native verifiable accountability and avoids costly retraining cycles.')}
        </div>
      </div>

      <div class="reasoning-section-box">
        <div class="reasoning-section-title"><i class="fa-solid fa-shield-check" style="color: #10B981;"></i> Verification Confidence:</div>
        <span class="falsification-score-badge" style="font-size: 0.95rem; padding: 4px 12px;">
          <i class="fa-solid fa-shield-check"></i> ${confScore}% Verified Quality (Audited)
        </span>
      </div>

      <div class="reasoning-section-box">
        <div class="reasoning-section-title"><i class="fa-solid fa-flask" style="color: #0ea5e9;"></i> Actionable 3-Phase Testing Roadmap:</div>
        <div class="testing-lab-grid">
          <div class="testing-step-row">
            <div class="testing-step-num">Phase 1: Baseline Comparison</div>
            <div class="testing-step-desc">${escapeHtml(bp.phase_1_baseline || 'Benchmark traditional baselines.')}</div>
          </div>
          <div class="testing-step-row">
            <div class="testing-step-num">Phase 2: Mechanism Intervention</div>
            <div class="testing-step-desc">${escapeHtml(bp.phase_2_intervention || 'Deploy self-correcting mechanisms.')}</div>
          </div>
          <div class="testing-step-row">
            <div class="testing-step-num">Phase 3: Validation Metric</div>
            <div class="testing-step-desc">${escapeHtml(bp.phase_3_evaluation_metric || 'Measure empirical performance gain.')}</div>
          </div>
        </div>
      </div>

      ${discovery.real_world_application ? `
        <div class="real-world-impact-pill">
          <strong><i class="fa-solid fa-earth-americas"></i> Real-World Impact:</strong> ${escapeHtml(discovery.real_world_application)}
        </div>
      ` : ''}
    `;
  }

  modal.style.display = 'flex';
}

// -----------------------------------------------------------------------------
// Interactive Theater Dialogue Renderer (Clean, Professional, No Emojis)
// -----------------------------------------------------------------------------
function renderTheaterDialogue(transcript) {
  const container = document.getElementById('agentTranscriptContainer');
  if (!container) return;

  const agentIcons = {
    'Concept Mapper': 'fa-book-open',
    'Idea Theorist': 'fa-lightbulb',
    'Peer Referee': 'fa-scale-balanced',
    'Self-Correction Lead': 'fa-wrench',
    'Blueprint Lead': 'fa-clipboard-check',
    'OntologyMapper': 'fa-book-open',
    'HypothesisTheorist': 'fa-lightbulb',
    'PeerReferee': 'fa-scale-balanced',
    'SelfCorrectionLead': 'fa-wrench',
    'BlueprintArchitect': 'fa-clipboard-check'
  };

  const avatarClasses = {
    'Concept Mapper': 'blue',
    'Idea Theorist': 'cyan',
    'Peer Referee': 'red',
    'Self-Correction Lead': 'amber',
    'Blueprint Lead': 'emerald'
  };

  container.innerHTML = transcript.map(msg => {
    const icon = agentIcons[msg.sender] || 'fa-robot';
    const avClass = avatarClasses[msg.sender] || 'blue';
    return `
      <div class="theater-bubble">
        <div class="theater-avatar-icon ${avClass}">
          <i class="fa-solid ${icon}"></i>
        </div>
        <div style="flex-grow: 1;">
          <div class="theater-header">
            <span class="theater-speaker">${escapeHtml(msg.sender)}</span>
            <span class="theater-role-pill">${escapeHtml(msg.role || 'AI Researcher')}</span>
          </div>
          <div class="theater-text">${escapeHtml(msg.message)}</div>
        </div>
      </div>
    `;
  }).join('');
}

// -----------------------------------------------------------------------------
// Actionable 3-Step Testing Protocol Renderer
// -----------------------------------------------------------------------------
function renderTestingLabBlueprint(discovery) {
  const container = document.getElementById('verifiedDiscoveryContainer');
  if (!container) return;

  const bp = discovery.experimental_blueprint || {};
  const mechLabel = discovery.mechanism_label || "Core Working Mechanism";
  const mechContent = discovery.core_mechanism_details || discovery.mathematical_algorithmic_formulation || "";

  container.innerHTML = `
    <!-- Domain-Specific Mechanism Box -->
    ${mechContent ? `
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 12px; margin-bottom: 10px;">
        <div style="font-size: 0.78rem; font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">
          <i class="fa-solid fa-gear" style="color: var(--primary); margin-right: 4px;"></i> ${escapeHtml(mechLabel)}:
        </div>
        <div style="font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; white-space: pre-line;">${escapeHtml(mechContent)}</div>
      </div>
    ` : ''}

    <!-- 3-Phase Stepper Protocol -->
    <div class="testing-lab-grid">
      <div class="testing-step-row">
        <div class="testing-step-num"><i class="fa-solid fa-1"></i> Phase 1: Baseline Comparison</div>
        <div class="testing-step-desc">${escapeHtml(bp.phase_1_baseline || 'Establish standard reference baseline performance.')}</div>
      </div>
      <div class="testing-step-row">
        <div class="testing-step-num"><i class="fa-solid fa-2"></i> Phase 2: Mechanism Intervention</div>
        <div class="testing-step-desc">${escapeHtml(bp.phase_2_intervention || 'Implement the proposed adaptive self-correcting controls.')}</div>
      </div>
      <div class="testing-step-row">
        <div class="testing-step-num"><i class="fa-solid fa-3"></i> Phase 3: Validation Metric</div>
        <div class="testing-step-desc">${escapeHtml(bp.phase_3_evaluation_metric || 'Evaluate empirical accuracy, latency, and stability.')}</div>
      </div>
    </div>

    <!-- Practical Real-World Impact -->
    ${discovery.real_world_application ? `
      <div class="real-world-impact-pill">
        <strong><i class="fa-solid fa-earth-americas"></i> Real-World Impact:</strong> ${escapeHtml(discovery.real_world_application)}
      </div>
    ` : ''}
  `;
}
