// --- SHADOW AI — CSP COMPLIANT VERSION ---
console.log("🛡️ SHADOW AI: Running on", window.location.hostname);

// --- CONFIG ---
const supabaseUrl = typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.supabaseUrl : "";
const supabaseKey = typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.supabaseKey : "";
let COMPANY_ID = "";

// --- LOAD ID ---
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

// --- FETCH RULES ---
async function fetchCompanySecrets() {
  if (!COMPANY_ID) return;
  try {
    const res = await fetch(`${supabaseUrl}/rest/v1/company_secrets?select=*&company_id=eq.${COMPANY_ID}`, {
      headers: { apikey: supabaseKey, Authorization: `Bearer ${supabaseKey}` }
    });
    customSecrets = await res.json() || [];
  } catch (e) {}
}

// --- LOG ---
async function reportLeak(type, detail, blockedText = "") {
  if (!COMPANY_ID) return;
  try {
    await fetch(`${supabaseUrl}/rest/v1/security_logs`, {
      method: "POST",
      headers: { apikey: supabaseKey, Authorization: `Bearer ${supabaseKey}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        event_type: type, violation_type: detail, site_url: window.location.hostname,
        blocked_content: blockedText.substring(0, 300), company_id: COMPANY_ID, compliance_flag: "NHS_IG_GDPR"
      })
    });
  } catch (e) {}
}

// --- ✅ CSP-SAFE BADGE ---
function addBadge() {
  if (document.getElementById('shadow-ai-badge')) return;
  try {
    const badge = document.createElement('div');
    badge.id = 'shadow-ai-badge';
    badge.textContent = '🛡️ Shadow AI | ACTIVE';
    Object.assign(badge.style, {
      position: 'fixed', top: '10px', right: '10px',
      background: '#003087', color: '#fff', padding: '8px 16px',
      borderRadius: '4px', fontWeight: 'bold', fontSize: '12px',
      zIndex: '2147483647', boxShadow: '0 0 10px rgba(0,0,0,0.5)',
      border: '2px solid #005EB8', fontFamily: 'Arial, sans-serif',
      pointerEvents: 'none'
    });
    (document.documentElement || document.body).appendChild(badge);
  } catch (e) { /* fail silently if blocked */ }
}

// --- ✅ CSP-SAFE SCAN ---
function scanAndBlock() {
  let leakFound = false;
  addBadge();

  const inputs = document.querySelectorAll(`
    textarea, [contenteditable="true"], input[type="text"],
    div[role="textbox"], .cib-text-input, .cib-serp-input,
    div[class*="input"], div[class*="prompt"]
  `);

  inputs.forEach(input => {
    const original = input.value || input.innerText || "";
    if (original.length < 3) return;

    let redacted = original;
    let matched = false;

    customSecrets.forEach(rule => {
      try {
        const rx = new RegExp(`\\b${rule.secret_word.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&')}\\b`, 'gi');
        if (rx.test(original)) {
          redacted = redacted.replace(rx, '██████████');
          matched = true;
          leakFound = true;
          reportLeak("BLOCKED", `Custom: ${rule.secret_word}`, original);
        }
      } catch (e) {}
    });

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

    if (matched) {
      if (input.value !== undefined) {
        input.value = redacted;
      } else {
        input.innerText = redacted;
        input.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }
  });

  const sendBtn = document.querySelector(`
    [data-testid="send-button"], button[type="submit"], .send-button,
    .cib-submit-button, button[aria-label*="Send"], div[class*="send"]
  `);
  if (sendBtn) {
    sendBtn.disabled = leakFound;
    sendBtn.style.pointerEvents = leakFound ? 'none' : 'auto';
    sendBtn.style.opacity = leakFound ? '0.5' : '1';
  }
}

// --- START ---
function initProtection() {
  fetchCompanySecrets();
  setInterval(scanAndBlock, 200);
  setInterval(fetchCompanySecrets, 30000);
}

loadIdFromStorage();

const obs = new MutationObserver(() => scanAndBlock());
obs.observe(document.documentElement, { childList: true, subtree: true, attributes: true, characterData: true });

setTimeout(scanAndBlock, 800);
setTimeout(scanAndBlock, 1800);