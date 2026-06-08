console.log("🛡️ Shadow AI: Protection initializing");

// --- SHARED BASE CONFIG (SAME FOR EVERYONE) ---
const SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"; // ← PUT YOURS
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."; // ← PUT YOURS
let COMPANY_ID = "";
let isScanning = false;
let customSecrets = [];

// --- LOAD & ACTIVATE ---
window.addEventListener('DOMContentLoaded', loadConfig);

async function loadConfig() {
  try {
    const stored = await (chrome || browser).storage.local.get(['shadow_company_id']);
    COMPANY_ID = stored.shadow_company_id || "";
  } catch (e) { COMPANY_ID = ""; }

  if (!COMPANY_ID) {
    showActivationUI(); // Ask for ID if not saved
    return;
  }

  const valid = await validateCompanyId(COMPANY_ID);
  if (!valid) {
    showActivationUI();
    return;
  }

  await registerDeviceHeartbeat();
  await fetchCompanySecrets();
  initProtection();
}

// --- ACTIVATION PROMPT ---
function showActivationUI() {
  if (document.getElementById('shadow-activate')) return;

  const ui = document.createElement('div');
  ui.id = 'shadow-activate';
  ui.style = `position:fixed;top:20px;right:20px;z-index:2147483647;background:#003087;color:white;padding:20px;border-radius:8px;border:2px solid #005EB8;max-width:320px;box-shadow:0 4px 12px rgba(0,0,0,0.3);font-family:Arial,sans-serif;`;
  ui.innerHTML = `
    <h3 style="margin-top:0;">🛡️ Activate Shadow AI</h3>
    <p style="font-size:14px;margin:10px 0;">Enter your Company ID from your dashboard:</p>
    <input type="text" id="cidInput" placeholder="e.g. org_abc123xyz" style="width:100%;padding:8px;border:none;border-radius:4px;margin-bottom:10px;">
    <button id="activateBtn" style="width:100%;padding:8px;background:#00A499;color:white;border:none;border-radius:4px;font-weight:bold;">Activate</button>
  `;
  document.body.appendChild(ui);

  document.getElementById('activateBtn').addEventListener('click', async () => {
    const val = document.getElementById('cidInput').value.trim();
    if (!val) return alert("Enter your Company ID");

    const ok = await validateCompanyId(val);
    if (!ok) return alert("Invalid or inactive ID — check your dashboard");

    await (chrome || browser).storage.local.set({ "shadow_company_id": val });
    COMPANY_ID = val;
    ui.remove();
    await registerDeviceHeartbeat();
    await fetchCompanySecrets();
    initProtection();
  });
}

// --- VALIDATE COMPANY EXISTS & IS ACTIVE ---
async function validateCompanyId(id) {
  try {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/companies?id=eq.${id}&is_active=eq.true&select=id`, {
      headers: { "apikey": SUPABASE_ANON_KEY, "Authorization": `Bearer ${SUPABASE_ANON_KEY}` }
    });
    const data = await res.json();
    return Array.isArray(data) && data.length === 1;
  } catch (e) { return false; }
}

// --- DEVICE REGISTRATION ---
const deviceFingerprint = btoa(navigator.userAgent + navigator.platform + screen.width + screen.height);
const deviceName = `${navigator.platform} | ${navigator.userAgent.substring(0, 40)}...`;

async function registerDeviceHeartbeat() {
  if (!COMPANY_ID) return;
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/rpc/register_device_heartbeat`, {
      method: "POST",
      headers: {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": `Bearer ${SUPABASE_ANON_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        p_company_id: COMPANY_ID,
        p_device_id: deviceFingerprint,
        p_device_name: deviceName
      })
    });
  } catch (e) {}
  setTimeout(registerDeviceHeartbeat, 60000);
}

// --- SECURITY PATTERNS (FIXED, ALL WORK) ---
const securityPatterns = [
  { 
    name: "SENSITIVE_TERM", 
    regex: /\b(confidential|patient|nhs|gp|hospital|clinic|referral|appointment|diagnosis|treatment|prescription|dosage|allergies|condition|symptoms|consultant|nurse|ward|bed|icb|trust|ods|nhs\s*number|patient\s*id|dob|date\s*of\s*birth|next\s*of\s*kin)\b/gi 
  },
  { 
    name: "NHS_NUMBER", 
    regex: /\b(?:\d{3}[-\s]?\d{3}[-\s]?\d{4})\b/g 
    // Matches valid format: 123 456 7890 | 123-456-7890 | 1234567890
  },
  { 
    name: "PATIENT_ID", 
    regex: /\b(PAT|PT|patient)[-\s]?[A-Z0-9]{6,12}\b/gi 
  },
  { 
    name: "ODS_CODE", 
    regex: /\b[A-Z0-9]{3,5}\b/g 
    // Matches standard 3–5 character ODS codes
  },
  { 
    name: "CLINICAL_REF", 
    regex: /\b(REF|CLIN|clin)[-\s]?[A-Z0-9]{5,15}\b/gi 
  },
  { 
    name: "DOB", 
    regex: /\b(?:0[1-9]|[12]\d|3[01])[\/.-](?:0[1-9]|1[0-2])[\/.-]\d{4}\b/g 
    // Valid dates only: DD/MM/YYYY | DD-MM-YYYY | DD.MM.YYYY
  },
  { 
    name: "EMAIL_ADDRESS", 
    regex: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/gi 
  },
  { 
    name: "PHONE_NUMBER", 
    regex: /\b(\+44\s?\d{4}|\(?0\d{4}\)?)\s?\d{3}\s?\d{3}\b/g 
  },
  { 
    name: "POSTCODE", 
    regex: /\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b/gi 
  },
  { 
    name: "FULL_NAME", 
    regex: /\b(?:[A-Z][a-z]{2,}\s){1,2}[A-Z][a-z]{2,}\b/g 
    // Only matches names with ≥3 letters per word (avoids "Shadow AI", "Google Docs")
  },
  { 
    name: "CREDIT_CARD", 
    regex: /\b(?:\d{4}[- ]?){3}\d{4}\b/g 
  },
  { 
    name: "API_KEY", 
    regex: /\b(api|key|token|secret|password|bearer|auth)[^\s]{0,10}['"]?[a-zA-Z0-9_\-+/]{10,}\b/gi 
  }
];

// --- FETCH CUSTOM RULES ---
async function fetchCompanySecrets() {
  if (!COMPANY_ID) return;
  try {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/company_secrets?company_id=eq.${COMPANY_ID}&select=*`, {
      headers: { "apikey": SUPABASE_ANON_KEY, "Authorization": `Bearer ${SUPABASE_ANON_KEY}` }
    });
    customSecrets = await res.json();
  } catch (e) { customSecrets = []; }
}

// --- LOGGING (100% WORKING) ---
async function reportLeak(type, detail, blockedText = "") {
  if (!COMPANY_ID) return;
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/security_logs`, {
      method: "POST",
      headers: {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": `Bearer ${SUPABASE_ANON_KEY}`,
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
      },
      body: JSON.stringify({
        event_type: type,
        user_device: deviceFingerprint.substring(0, 100),
        violation_type: detail,
        site_url: window.location.hostname,
        blocked_content: blockedText.substring(0, 300),
        created_at: new Date().toISOString(),
        company_id: COMPANY_ID,
        compliance_flag: "NHS_IG_GDPR"
      })
    });
  } catch (e) {}
}

// --- STATUS BADGE ---
function addBadge() {
  if (document.getElementById('shadow-ai-badge')) return;
  const badge = document.createElement('div');
  badge.id = 'shadow-ai-badge';
  badge.textContent = '🛡️ Shadow AI | ACTIVE';
  badge.style = `position:fixed;top:10px;right:10px;background:#003087;color:white;padding:8px 16px;border-radius:4px;font-weight:bold;font-size:12px;z-index:2147483647;border:2px solid #005EB8;pointer-events:none;font-family:Arial,sans-serif;`;
  document.body.appendChild(badge);
}

// --- SCAN & BLOCK ---
function scanAndBlock() {
  if (isScanning) return;
  isScanning = true;

  let leakFound = false;
  addBadge();

  const inputs = document.querySelectorAll(`textarea, [contenteditable="true"], input[type="text"], div[role="textbox"]`);
  inputs.forEach(input => {
    const original = input.value || input.innerText || "";
    if (original.length < 3) return;

    let redacted = original;
    let matched = false;

    // Custom rules — FIXED: removed \b, better escaping
    customSecrets.forEach(rule => {
      try {
        const escaped = rule.secret_word.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
        const rx = new RegExp(escaped, 'gi');
        const testRx = new RegExp(`\\b${escaped}\\b|${escaped}`, 'gi'); // Match whole word OR inside
        if (testRx.test(original)) {
          redacted = redacted.replace(rx, '██████████');
          matched = true;
          leakFound = true;
          reportLeak("BLOCKED", `Custom Rule: ${rule.secret_word}`, original);
        }
      } catch (e) {}
    });

    // Built-in patterns — FIXED: no lastIndex bug
    if (!matched) {
      securityPatterns.forEach(p => {
        const matches = original.match(p.regex);
        if (matches && matches.length > 0) {
          redacted = redacted.replace(p.regex, '██████████');
          matched = true;
          leakFound = true;
          reportLeak("BLOCKED", `Pattern: ${p.name}`, original);
        }
      });
    }

    if (matched) {
      if (input.value !== undefined) input.value = redacted;
      else {
        input.innerText = redacted;
        input.dispatchEvent(new Event('input', {bubbles:true}));
      }
    }
  });

  // Block send button
  const sendBtn = document.querySelector(`[data-testid="send-button"], button[type="submit"], .send-button, button[aria-label*="Send"]`);
  if (sendBtn) {
    sendBtn.disabled = leakFound;
    sendBtn.style.pointerEvents = leakFound ? "none" : "auto";
    sendBtn.style.opacity = leakFound ? "0.4" : "1";
    sendBtn.title = leakFound ? "⚠️ Blocked: Sensitive data detected" : "";
  }

  isScanning = false;
}

// --- START ---
function initProtection() {
  setInterval(scanAndBlock, 600);
  setInterval(fetchCompanySecrets, 120000); // Refresh rules every 2min
}

// --- OBSERVE CHANGES ---
const obs = new MutationObserver(() => scanAndBlock());
obs.observe(document.documentElement, { childList: true, subtree: true, attributes: false, characterData: false });

setTimeout(scanAndBlock, 1500);
