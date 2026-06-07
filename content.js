// --- SHADOW AI — NHS COMPLIANT DLP ENGINE ---
console.log("🛡️ Shadow AI: Protection initialized");

// --- CONFIG ---
const supabaseUrl = typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.supabaseUrl : "";
const supabaseKey = typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.supabaseKey : "";
let COMPANY_ID = "";

// --- ✅ DELAY START UNTIL PAGE IS READY — THIS FIXES THE FLASH ---
window.addEventListener('DOMContentLoaded', () => {
  loadIdFromStorage();
});

// --- LOAD SETTINGS ---
async function loadIdFromStorage() {
  try {
    const data = await (chrome || browser).storage.local.get(['shadow_company_id']);
    COMPANY_ID = data.shadow_company_id || (typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.companyId : "");
  } catch (e) {
    COMPANY_ID = typeof SHADOW_AI_CONFIG !== 'undefined' ? SHADOW_AI_CONFIG.companyId : "";
  }

  // ✅ CHECK LICENSE — SILENT, NO PAGE CHANGES UNLESS NEEDED
  await checkLicenseAndRegisterDevice();
  initProtection();
}

let customSecrets = [];
const deviceFingerprint = `${navigator.platform} | ${navigator.userAgent.substring(0, 100)}`;

// --- ✅ LICENSE CHECK — NO FLASH, NO ERRORS, NO BLOCK ON CONNECTION FAIL ---
async function checkLicenseAndRegisterDevice(retryCount = 0) {
  // ❌ ONLY BLOCK FOR REAL LICENSE ISSUES / DEMO VERSION
  if (
    !supabaseUrl || !supabaseKey || !COMPANY_ID ||
    supabaseUrl === "YOUR_SUPABASE_URL_HERE" ||
    supabaseKey === "YOUR_SUPABASE_ANON_KEY_HERE" ||
    COMPANY_ID === "YOUR_COMPANY_ID_HERE"
  ) {
    showBlockMessage("NOT LICENSED", "This is a public demo only. Please purchase a license from shadowaisecurity.co.uk to use.");
    return false;
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    const res = await fetch(`${supabaseUrl}/functions/v1/register-device`, {
      method: "POST",
      headers: {
        "apikey": supabaseKey,
        "Authorization": `Bearer ${supabaseKey}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        company_id: COMPANY_ID,
        device_id: btoa(deviceFingerprint)
      }),
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!res.ok) throw new Error(`Server error: ${res.status}`);
    const result = await res.json();

    // ✅ ONLY BLOCK IF EXPLICITLY OVER LIMIT OR INVALID
    if (result.status === "over_limit") {
      showBlockMessage("LICENSE LIMIT REACHED", `You paid for ${result.allowed} devices — currently using ${result.used}. Protection paused. Contact support to upgrade.`);
      return false;
    }
    if (result.status === "invalid") {
      showBlockMessage("INVALID LICENSE", "This organisation license is not valid or has been revoked.");
      return false;
    }

    localStorage.setItem("shadow_ai_last_check", Date.now().toString());
    console.log("✅ Shadow AI: License verified");
    return true;

  } catch (err) {
    // ✅ CONNECTION FAILED — 100% SILENT, NO PAGE CHANGES
    console.warn("⚠️ Shadow AI: Could not connect — protection still active");
    if (retryCount < 2) {
      await new Promise(r => setTimeout(r, 1500));
      return checkLicenseAndRegisterDevice(retryCount + 1);
    }
    return true;
  }
}

// --- ✅ SHOW BLOCK MESSAGE — ONLY WHEN REQUIRED, NO EARLY PAGE EDITS ---
function showBlockMessage(title, text) {
  // ❌ ONLY EDIT PAGE IF WE ACTUALLY NEED TO BLOCK — THIS IS THE MAIN FIX FOR FLASH
  if (document.body) {
    document.body.innerHTML = "";
    document.body.style.background = "#141E3C";
    document.body.style.color = "white";
    document.body.style.padding = "3rem";
    document.body.style.fontFamily = "Arial, sans-serif";
    document.body.innerHTML = `
      <div style="max-width: 600px; margin: 0 auto; background: #141E3C; color: white; border-radius: 8px; border: 2px solid #DA291C; padding: 2rem;">
        <h2 style="color: #DA291C; margin-top: 0;">🛡️ Shadow AI — ${title}</h2>
        <p style="font-size: 16px; line-height: 1.6;">${text}</p>
      </div>
    `;
  }
  // ❌ NO throw new Error — NO ERRORS IN EXTENSIONS
}

// --- ✅ NHS & SECURITY RULES — FIXED REGEX ---
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

// --- FETCH ORG-SPECIFIC RULES ---
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

// --- AUDIT LOGGING ---
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

// --- STATUS BADGE ---
function addBadge() {
  if (document.getElementById('shadow-ai-badge')) return;
  const badge = document.createElement('div');
  badge.id = 'shadow-ai-badge';
  badge.textContent = '🛡️ Shadow AI | ACTIVE';
  badge.style.position = 'fixed';
  badge.style.top = '10px';
  badge.style.right = '10px';
  badge.style.background = '#003087';
  badge.style.color = '#ffffff';
  badge.style.padding = '8px 16px';
  badge.style.borderRadius = '4px';
  badge.style.fontWeight = 'bold';
  badge.style.fontSize = '12px';
  badge.style.zIndex = '2147483647';
  badge.style.boxShadow = '0 0 10px rgba(0,0,0,0.5)';
  badge.style.border = '2px solid #005EB8';
  badge.style.fontFamily = 'Arial, sans-serif';
  badge.style.pointerEvents = 'none';
  if (document.body) document.body.appendChild(badge);
}

// --- SCAN & BLOCK ---
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
          reportLeak("BLOCKED", `Custom Rule: ${rule.secret_word}`, original);
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
        input.dispatchEvent(new Event('change', { bubbles: true }));
      }
    }
  });

  const sendBtn = document.querySelector(`
    [data-testid="send-button"], button[type="submit"], .send-button,
    .cib-submit-button, button[aria-label*="Send"], div[class*="send"]
  `);
  if (sendBtn) {
    sendBtn.disabled = leakFound;
    sendBtn.style.pointerEvents = leakFound ? "none" : "auto";
    sendBtn.style.opacity = leakFound ? "0.5" : "1";
  }
}

// --- START ---
function initProtection() {
  fetchCompanySecrets();
  setInterval(scanAndBlock, 200);
  setInterval(fetchCompanySecrets, 30000);
}

const obs = new MutationObserver(() => scanAndBlock());
obs.observe(document.documentElement, { childList: true, subtree: true, attributes: true, characterData: true });

setTimeout(scanAndBlock, 800);
setTimeout(scanAndBlock, 2000);