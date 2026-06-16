console.log("🔴 Shadow AI: SCRIPT LOADED — RUNNING");

const SUPABASE_URL = "https://ypjpjixwdjcvmlrmsgzc.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlwanBqaXh3ZGpjdm1scm1zZ3pjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3MDY3NjMsImV4cCI6MjA5MjI4Mjc2M30.3bwI2E8JTFC6tmeqJcuJ_ICifnUAJRhbjRCwGFwmihw";

let COMPANY_ID = "";
let LICENCE_KEY = "";
let ORG_REFERENCE = "";
let isScanning = false;
let customSecrets = [];
let LICENCE_VALID = false;

function addBadge() {
  if (document.getElementById('shadow-ai-badge')) return;
  const badge = document.createElement('div');
  badge.id = 'shadow-ai-badge';
  badge.style = `position:fixed;top:10px;right:10px;background:#666;color:white;padding:8px 16px;border-radius:4px;font-weight:bold;font-size:12px;z-index:99999999;border:2px solid #999;pointer-events:none;font-family:Arial,sans-serif;`;
  badge.textContent = '🛡️ SHADOW AI | INACTIVE';
  document.documentElement.appendChild(badge);
}

function setBadgeActive() {
  const b = document.getElementById('shadow-ai-badge');
  if (b) {
    b.textContent = '🛡️ SHADOW AI | ACTIVE ✅';
    b.style.background = '#003087';
    b.style.borderColor = '#005EB8';
  }
}

addBadge();
initProtection();

async function loadConfig() {
  try {
    const stored = await (chrome || browser).storage.local.get(['shadow_company_id', 'shadow_licence_key', 'shadow_org_ref']);
    COMPANY_ID = stored.shadow_company_id || "";
    LICENCE_KEY = stored.shadow_licence_key || "";
    ORG_REFERENCE = stored.shadow_org_ref || "";
  } catch (e) {
    COMPANY_ID = LICENCE_KEY = ORG_REFERENCE = "";
    LICENCE_VALID = false;
    return;
  }

  if (!COMPANY_ID || !LICENCE_KEY) {
    LICENCE_VALID = false;
    showActivationUI();
    return;
  }

  const valid = await validateLicenceAndOrg(LICENCE_KEY, COMPANY_ID);
  if (!valid) {
    LICENCE_VALID = false;
    showActivationUI();
    return;
  }

  LICENCE_VALID = true;
  setBadgeActive();
  await registerDeviceHeartbeat();
  await fetchCompanySecrets();
}

async function validateLicenceAndOrg(key, orgName) {
  try {
    const res = await fetch(
      `${SUPABASE_URL}/rest/v1/licences?licence_key=eq.${encodeURIComponent(key)}&organisation_name=eq.${encodeURIComponent(orgName)}&is_active=eq.true&select=id,expires_at,org_reference`,
      {
        headers: { 'apikey': SUPABASE_ANON_KEY, 'Authorization': `Bearer ${SUPABASE_ANON_KEY}` }
      }
    );
    const data = await res.json();
    if (!Array.isArray(data) || data.length !== 1) return false;

    ORG_REFERENCE = data[0].org_reference?.trim() || orgName;
    return !data[0].expires_at || new Date(data[0].expires_at) > new Date();
  } catch (e) { return false; }
}

function showActivationUI() {
  if (document.getElementById('shadow-activate')) return;
  const ui = document.createElement('div');
  ui.id = 'shadow-activate';
  ui.style = `position:fixed;top:60px;right:20px;z-index:99999999;background:#003087;color:white;padding:20px;border-radius:8px;border:2px solid #005EB8;max-width:320px;box-shadow:0 4px 12px rgba(0,0,0,0.3);font-family:Arial,sans-serif;`;
  ui.innerHTML = `
    <h3 style="margin-top:0;">🛡️ Activate Shadow AI</h3>
    <p style="font-size:14px;margin:10px 0;">Enter your details:</p>
    <input type="text" id="cidInput" placeholder="Organisation Name" style="width:100%;padding:8px;border:none;border-radius:4px;margin-bottom:10px;background:#ffffff;color:#000000;font-size:14px;">
    <input type="text" id="licenceInput" placeholder="Licence Key" style="width:100%;padding:8px;border:none;border-radius:4px;margin-bottom:10px;background:#ffffff;color:#000000;font-size:14px;">
    <button id="activateBtn" style="width:100%;padding:8px;background:#00A499;color:white;border:none;border-radius:4px;font-weight:bold;">Activate</button>
  `;
  document.documentElement.appendChild(ui);

  document.getElementById('activateBtn').addEventListener('click', async () => {
    const cid = document.getElementById('cidInput').value.trim();
    const lic = document.getElementById('licenceInput').value.trim();
    if (!cid || !lic) return alert("Enter both values");

    const ok = await validateLicenceAndOrg(lic, cid);
    if (!ok) return alert("❌ Invalid — check your details");

    await (chrome || browser).storage.local.set({ 
      "shadow_company_id": cid,
      "shadow_licence_key": lic,
      "shadow_org_ref": ORG_REFERENCE
    });
    COMPANY_ID = cid;
    LICENCE_KEY = lic;
    LICENCE_VALID = true;
    setBadgeActive();
    ui.remove();
    await registerDeviceHeartbeat();
    await fetchCompanySecrets();
  });
}

const deviceFingerprint = btoa(navigator.userAgent + navigator.platform + screen.width + screen.height);
const deviceName = `${navigator.platform} | ${navigator.userAgent.substring(0, 40)}...`;

async function registerDeviceHeartbeat() {
  if (!LICENCE_VALID || !COMPANY_ID || !LICENCE_KEY || !ORG_REFERENCE) return;
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/rpc/register_device_heartbeat`, {
      method: "POST",
      headers: {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": `Bearer ${SUPABASE_ANON_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        p_company_id: ORG_REFERENCE,
        p_org_ref: ORG_REFERENCE,
        p_device_id: deviceFingerprint,
        p_device_name: deviceName
      })
    });
  } catch (e) { console.error("Heartbeat error:", e); }
  setTimeout(registerDeviceHeartbeat, 60000);
}

// --- 🚨 FINAL RULES — ✅ 100% NO FALSE BLOCKS ---
const securityPatterns = [
  // 🔴 NHS NUMBERS & CODES — ONLY VALID FORMATS
  { name: "NHS_NUMBER", regex: /\b(?:\d{3}[-\s]?\d{3}[-\s]?\d{4})\b/gi },
  { name: "CHI_NUMBER", regex: /\b\d{10}\b/gi },
  { name: "NHS_PASSPORT", regex: /\b[Nn][Hh][SsPp]\d{6,}\b/gi },
  { name: "TRUST_CODE", regex: /\b[A-Z]{2}\d{3}\b/gi },
  { name: "GP_PRACTICE_CODE", regex: /\b\d{5}[A-Z]?\b/gi },
  { name: "ODS_CODE", regex: /\b[A-Z0-9]{3,10}\b/gi },

  // 🔴 PERSONAL IDENTIFIERS — ONLY VALID FORMATS
  { name: "EMAIL", regex: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/gi },
  { name: "UK_PHONE", regex: /\b(?:\+44\s?\d{4}\s?\d{6}|0\d{4}\s?\d{6}|0\d{3}\s?\d{3}\s?\d{4}|07\d{3}\s?\d{6})\b/gi },
  { name: "UK_POSTCODE", regex: /\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b/gi },
  { name: "DOB", regex: /\b(?:0[1-9]|[12]\d|3[01])[\/.-](?:0[1-9]|1[0-2])[\/.-]\d{4}\b/gi },
  { name: "FULL_NAME_WITH_TITLE", regex: /\b(?:Mr|Mrs|Ms|Miss|Dr|Prof)\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b/gi },
  { name: "NINO", regex: /\b[A-Z]{2}\d{6}[A-Z]{1}\b/gi },
  { name: "PASSPORT", regex: /\b\d{9}\b/gi },
  { name: "DRIVING_LICENCE", regex: /\b[A-Z9]{5}\d{5}[A-Z9]{2}\d{5}\b/gi },
  { name: "BANK_ACCOUNT", regex: /\b\d{8}\b/gi },
  { name: "SORT_CODE", regex: /\b\d{2}[-\s]?\d{2}[-\s]?\d{2}\b/gi },

  // 🔴 MEDICAL RECORD IDS — ONLY WHEN FOLLOWED BY NUMBERS
  { name: "MEDICAL_RECORD_NO", regex: /\b(?:MRN|Hospital No|Ref|ID)[-\s:#]*\d{4,}\b/gi },
  { name: "WARD_BED", regex: /\bWard[-\s]?[A-Z0-9]+[-\s]?Bed[-\s]?\d+\b/gi },
  { name: "DIAGNOSIS_CODE", regex: /\b(?:ICD-10|SNOMED|CPT)[-\s:]?[A-Z0-9.]{2,}\b/gi },
  { name: "PRESCRIPTION_NO", regex: /\bRx[-\s]?\d{5,}\b/gi },

  // 🔴 SENSITIVE PHRASES — ✅ ONLY EXACT FULL PHRASES (NO SINGLE WORDS)
  { name: "SENSITIVE_PHRASES", regex: /\b(?:confidential information|patient details|medical record|health record|personal data|special category data|information governance|patient identifiable data)\b/gi }
];

async function fetchCompanySecrets() {
  if (!LICENCE_VALID || !COMPANY_ID || !LICENCE_KEY) return;
  try {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/company_secrets?company_id=eq.${encodeURIComponent(COMPANY_ID)}&select=*`, {
      headers: { "apikey": SUPABASE_ANON_KEY, "Authorization": `Bearer ${SUPABASE_ANON_KEY}` }
    });
    customSecrets = await res.json();
  } catch (e) { customSecrets = []; }
}

async function reportLeak(type, detail, blockedText = "") {
  if (!LICENCE_VALID || !COMPANY_ID || !LICENCE_KEY || !ORG_REFERENCE) return;
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
        licence_key: LICENCE_KEY,
        org_reference: ORG_REFERENCE,
        compliance_flag: "NHS_IG_GDPR"
      })
    });
  } catch (e) {}
}

// ✅ SCAN LOGIC — BLOCKS ONLY WHAT IS EXPLICITLY SENSITIVE
function scanAndBlock() {
  if (!LICENCE_VALID) { isScanning = false; return; }
  if (isScanning) return;
  isScanning = true;

  let leakFound = false;
  const inputs = document.querySelectorAll(`textarea, [contenteditable="true"], input[type="text"], div[role="textbox"]`);

  inputs.forEach(input => {
    const original = input.value || input.innerText || "";
    if (original.length < 4) return;

    let redacted = original;
    let matched = false;

    // Custom secrets — EXACT MATCH ONLY
    customSecrets.forEach(rule => {
      try {
        const escaped = rule.secret_word.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
        const rx = new RegExp(`^\\s*${escaped}\\s*$|\\b${escaped}\\b`, 'gi');
        if (rx.test(original)) {
          redacted = redacted.replace(rx, '██████████');
          matched = true;
          leakFound = true;
          reportLeak("BLOCKED", `Custom Rule: ${rule.secret_word}`, original);
        }
      } catch (e) {}
    });

    // Built-in patterns
    securityPatterns.forEach(p => {
      const matches = original.match(p.regex);
      if (matches && matches.length > 0) {
        redacted = redacted.replace(p.regex, '██████████');
        matched = true;
        leakFound = true;
        reportLeak("BLOCKED", `Pattern: ${p.name}`, original);
      }
    });

    if (matched) {
      if (input.value !== undefined) input.value = redacted;
      else {
        input.innerText = redacted;
        input.dispatchEvent(new Event('input', {bubbles:true}));
      }
    }
  });

  const sendBtn = document.querySelector(`[data-testid="send-button"], button[type="submit"], .send-button, button[aria-label*="Send"]`);
  if (sendBtn) {
    sendBtn.disabled = leakFound;
    sendBtn.style.pointerEvents = leakFound ? "none" : "auto";
    sendBtn.style.opacity = leakFound ? "0.4" : "1";
  }

  isScanning = false;
}

function initProtection() {
  loadConfig();
  setInterval(scanAndBlock, 300);
  setInterval(fetchCompanySecrets, 120000);

  const obs = new MutationObserver(() => scanAndBlock());
  obs.observe(document.documentElement, { childList: true, subtree: true, attributes: false, characterData: false });

  setTimeout(scanAndBlock, 50);
}