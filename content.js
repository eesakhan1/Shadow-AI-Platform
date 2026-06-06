// --- SHADOW AI CORE ENGINE ---
// --- NHS COMPLIANT | AI ONLY VERSION ---

// --- CONFIG ---
const supabaseUrl = typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.supabaseUrl : "";
const supabaseKey = typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.supabaseKey : "";
let COMPANY_ID = "";

// --- LOAD COMPANY ID ---
async function loadIdFromStorage() {
  try {
    const data = await (chrome || browser).storage.local.get(['shadow_company_id']);
    COMPANY_ID = data.shadow_company_id || (typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.companyId : "");
  } catch (e) {
    COMPANY_ID = typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.companyId : "";
  }
}

let customSecrets = [];
const deviceFingerprint = `${navigator.platform} | ${navigator.userAgent.substring(0, 100)}`;

// --- NHS RULES ---
const securityPatterns = [
  { name: "SENSITIVE_TERM", regex: /\b(confidential|patient|nhs|gp|hospital|clinic|referral|appointment|diagnosis|treatment|prescription|dosage|allergies|condition|symptoms|consultant|nurse|ward|bed|icb|trust|ods|nhs number|patient id|dob|date of birth|next of kin)\b/gi },
  { name: "NHS_NUMBER", regex: /\b\d{3}[-\s]?\d{3}[-\s]?\d{4}\b/g },
  { name: "PATIENT_ID", regex: /\b(PAT|PT|patient)[-\s]?[A-Z0-9]{6,12}\b/gi },
  { name: "ODS_CODE", regex: /\b[A-Z0-9]{3,5}\b/g },
  { name: "CLINICAL_REF", regex: /\b(REF|CLIN|clin)[-\s]?[A-Z0-9]{5,15}\b/gi },
  { name: "DOB", regex: /\b\d{1,2}\/\d{1,2}\/\d{4}\b/g },
  { name: "EMAIL_ADDRESS", regex: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/gi },
  { name: "PHONE_NUMBER", regex: /\b(?:\+44\s?\d{4}|\(?0\d{4}\)?)\s?\d{3}\s?\d{3}\b/g },
  { name: "POSTCODE", regex: /\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b/gi },
  { name: "FULL_NAME", regex: /\b[A-Z][a-z]+\s[A-Z][a-z]+\b/g },
  { name: "CREDIT_CARD", regex: /\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b/g },
  { name: "API_KEY", regex: /(api|key|token|secret|password|bearer|auth)[^\s]{0,10}['"]?[a-zA-Z0-9_\-+/]{10,}['"]?/gi }
];

// --- FETCH CUSTOM RULES ---
async function fetchCompanySecrets() {
  if (!COMPANY_ID) return;
  try {
    const res = await fetch(`${supabaseUrl}/rest/v1/company_secrets?select=*&company_id=eq.${COMPANY_ID}`, {
      headers: { apikey: supabaseKey, Authorization: `Bearer ${supabaseKey}` }
    });
    const data = await res.json();
    customSecrets = Array.isArray(data) ? data : [];
  } catch (e) {}
}

// --- LOG EVENTS ---
async function reportLeak(type, detail, blockedText = "") {
  if (!COMPANY_ID) return;
  try {
    await fetch(`${supabaseUrl}/rest/v1/security_logs`, {
      method: "POST",
      headers: { apikey: supabaseKey, Authorization: `Bearer ${supabaseKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        event_type: type,
        user_device: deviceFingerprint,
        violation_type: detail,
        site_url: window.location.hostname,
        blocked_content: blockedText.substring(0, 300),
        created_at: new Date(),
        company_id: COMPANY_ID,
        compliance_flag: "NHS_IG_GDPR"
      })
    });
  } catch (e) {}
}

// --- ✅ GUARANTEED BADGE ---
function addBadge() {
  if (document.getElementById('shadow-ai-badge')) return;
  const badge = document.createElement('div');
  badge.id = 'shadow-ai-badge';
  badge.textContent = '🛡️ Shadow AI | AI PROTECTION ACTIVE';
  badge.style.cssText = `
    position: fixed !important;
    top: 15px !important;
    right: 15px !important;
    background: #003087 !important;
    color: #ffffff !important;
    padding: 10px 20px !important;
    border-radius: 4px !important;
    font-weight: bold !important;
    font-size: 13px !important;
    z-index: 999999999 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
    border: 2px solid #005EB8 !important;
    font-family: Arial, sans-serif !important;
  `;
  document.documentElement.appendChild(badge);
}

// --- SCAN & BLOCK ---
function scanAndBlock() {
  let globalLeakDetected = false;
  addBadge(); // Force add every time

  const inputs = document.querySelectorAll('textarea, [contenteditable="true"], input[type="text"]');
  inputs.forEach(input => {
    let text = input.value || input.innerText || "";
    if (text.length < 3) return;

    let redactedText = text;
    let localLeak = false;

    // Custom rules
    customSecrets.forEach(secret => {
      try {
        const regex = new RegExp(`\\b${secret.secret_word.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')}\\b`, 'gi');
        if (regex.test(text)) {
          redactedText = redactedText.replace(regex, '██████████');
          localLeak = true;
          globalLeakDetected = true;
          reportLeak("PREVENTED", `Custom Rule: ${secret.secret_word}`, text);
        }
      } catch (e) {}
    });

    // System rules
    if (!localLeak) {
      securityPatterns.forEach(p => {
        if (p.regex.test(text)) {
          redactedText = redactedText.replace(p.regex, '██████████');
          localLeak = true;
          globalLeakDetected = true;
          reportLeak("PREVENTED", `Pattern: ${p.name}`, text);
        }
      });
    }

    if (localLeak) {
      if (input.value !== undefined) input.value = redactedText;
      else input.innerText = redactedText;
    }
  });

  // Block send button
  const sendBtn = document.querySelector('[data-testid="send-button"], button[type="submit"], .send-button');
  if (sendBtn) {
    sendBtn.disabled = globalLeakDetected;
    sendBtn.style.opacity = globalLeakDetected ? "0.5" : "1";
    sendBtn.style.border = globalLeakDetected ? "2px solid #DA291C" : "";
    sendBtn.style.cursor = globalLeakDetected ? "not-allowed" : "pointer";
  }
}

// --- START ---
loadIdFromStorage().then(() => {
  fetchCompanySecrets();
  setInterval(scanAndBlock, 500); // Run every 0.5s — faster
  setInterval(fetchCompanySecrets, 60000);
});

const observer = new MutationObserver(() => scanAndBlock());
observer.observe(document.body, { childList: true, subtree: true });

console.log("%c ✅ SHADOW AI LOADED — AI PLATFORM ONLY ", "background:#003087;color:white;padding:4px");