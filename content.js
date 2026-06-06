// --- SHADOW AI CORE ENGINE ---
// --- NHS COMPLIANT | AI ONLY VERSION ---
console.log("🚀 SHADOW AI: Script injected and RUNNING");

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
  initProtection();
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
    position: fixed !important; top: 10px !important; right: 10px !important;
    background: #003087 !important; color: #ffffff !important;
    padding: 8px 16px !important; border-radius: 4px !important;
    font-weight: bold !important; font-size: 12px !important;
    z-index: 2147483647 !important;
    box-shadow: 0 0 10px rgba(0,0,0,0.5) !important;
    border: 2px solid #005EB8 !important;
    font-family: Arial, sans-serif !important;
    pointer-events: none !important;
  `;
  (document.documentElement || document.body).appendChild(badge);
  console.log("✅ Shadow AI Badge ADDED");
}

// --- ✅ FIXED SCAN — NOW WORKS ON COPILOT ---
function scanAndBlock() {
  let leakFound = false;
  addBadge();

  // ✅ COPILOT-SPECIFIC SELECTORS + ALL OTHERS
  const inputs = document.querySelectorAll(`
    textarea,
    [contenteditable="true"],
    input[type="text"],
    div[role="textbox"],
    .cib-text-input,
    .cib-serp-input,
    div[class*="cib-"],
    div[class*="input"],
    div[class*="prompt"]
  `);

  inputs.forEach(input => {
    const original = input.value || input.innerText || "";
    if (original.length < 3) return;

    let redacted = original;
    let matched = false;

    // Custom rules
    customSecrets.forEach(rule => {
      try {
        const regex = new RegExp(`\\b${rule.secret_word.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')}\\b`, 'gi');
        if (regex.test(original)) {
          redacted = redacted.replace(regex, '██████████');
          matched = true;
          leakFound = true;
          reportLeak("BLOCKED", `Custom Rule: ${rule.secret_word}`, original);
        }
      } catch (e) {}
    });

    // System rules
    if (!matched) {
      securityPatterns.forEach(p => {
        if (p.regex.test(original)) {
          redacted = redacted.replace(p.regex, '██████████');
          matched = true;
          leakFound = true;
          reportLeak("BLOCKED", `Pattern: ${p.name}`, original);
        }
      });
    }

    // ✅ FORCE UPDATE FOR REACT/COPILOT
    if (matched) {
      if (input.value !== undefined) {
        input.value = redacted;
      } else {
        input.innerText = redacted;
        // Critical: Tell React/Microsoft framework content changed
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        input.dispatchEvent(new Event('blur', { bubbles: true }));
      }
    }
  });

  // ✅ COPILOT SEND BUTTON DETECTION
  const sendBtn = document.querySelector(`
    [data-testid="send-button"],
    button[type="submit"],
    .send-button,
    .cib-submit-button,
    button[aria-label*="Send"],
    button[title*="Send"],
    div[class*="send"],
    div[class*="submit"]
  `);

  if (sendBtn) {
    sendBtn.disabled = leakFound;
    sendBtn.style.pointerEvents = leakFound ? "none" : "auto";
    sendBtn.style.opacity = leakFound ? "0.5" : "1";
    sendBtn.style.filter = leakFound ? "grayscale(100%)" : "none";
    sendBtn.style.cursor = leakFound ? "not-allowed" : "pointer";
  }
}

// --- START PROTECTION ---
function initProtection() {
  fetchCompanySecrets();
  setInterval(scanAndBlock, 200); // Even faster: every 0.2s
  setInterval(fetchCompanySecrets, 30000);
}

// Load ID then start
loadIdFromStorage();

// ✅ DEEPER OBSERVER — catches Copilot's dynamic DOM changes
const obs = new MutationObserver(() => scanAndBlock());
obs.observe(document.documentElement, { 
  childList: true, 
  subtree: true, 
  attributes: true, 
  characterData: true,
  attributeFilter: ['class', 'contenteditable']
});