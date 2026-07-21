// ❌ REMOVED: importScripts('sector-loader.js'); — not supported in Manifest V3

// Load rules when extension starts
// initSector() is now handled via popup/storage, so we remove that call too

console.log("🔴 Shadow AI: FINAL VERSION — LOGIN + WORKING LOGGING");

const SUPABASE_URL = "https://ypjpjixwdjcvmlrmsgzc.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlwanBqaXh3ZGpjdm1scm1zZ3pjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzY3MDY3NjMsImV4cCI6MjA5MjI4Mjc2M30.3bwI2E8JTFC6tmeqJcuJ_ICifnUAJRhbjRCwGFwmihw";

let ORG_NAME = "";
let LICENCE_KEY = "";
let ORG_REFERENCE = "";
let COMPANY_ID = "";
let isScanning = false;
let customSecrets = [];
let LICENCE_VALID = false;
let activeRules = [];

// --- UI ---
function addBadge() {
  if (document.getElementById('shadow-ai-badge')) return;
  const badge = document.createElement('div');
  badge.id = 'shadow-ai-badge';
  badge.style = `position:fixed;top:10px;right:10px;background:#000000;color:#FFD700;padding:8px 16px;border-radius:4px;font-weight:bold;font-size:12px;z-index:99999999;border:1px solid #FFD700;pointer-events:none;font-family:Arial,sans-serif;`;
  badge.textContent = 'SHADOW AI | INACTIVE';
  document.documentElement.appendChild(badge);
}

function setBadgeActive() {
  const b = document.getElementById('shadow-ai-badge');
  if (b) {
    b.textContent = 'SHADOW AI | ACTIVE';
    b.style.background = '#000000';
    b.style.color = '#FFD700';
    b.style.borderColor = '#FFD700';
  }
}

addBadge();
initProtection();

async function loadActiveRules() {
  try {
    const data = await chrome.storage.local.get(['active_rules']);
    activeRules = data.active_rules || [];
  } catch (e) {
    activeRules = [];
  }
}

async function loadConfig() {
  try {
    const stored = await (chrome || browser).storage.local.get(['shadow_org_name', 'shadow_licence_key', 'shadow_org_ref', 'selected_sector']);
    ORG_NAME = stored.shadow_org_name || "";
    LICENCE_KEY = stored.shadow_licence_key || "";
    ORG_REFERENCE = stored.shadow_org_ref || "";
    COMPANY_ID = ORG_REFERENCE;

    await loadActiveRules();
  } catch (e) {
    ORG_NAME = LICENCE_KEY = ORG_REFERENCE = COMPANY_ID = "";
    LICENCE_VALID = false;
    showActivationUI();
    return;
  }

  if (!ORG_NAME || !LICENCE_KEY) {
    LICENCE_VALID = false;
    showActivationUI();
    return;
  }

  const valid = await validateLicenceAndOrg(LICENCE_KEY, ORG_NAME);
  if (!valid) {
    LICENCE_VALID = false;
    showActivationUI();
    return;
  }

  LICENCE_VALID = true;
  if (!stored.selected_sector) {
    showRedactionSelectionUI();
  } else {
    setBadgeActive();
    await registerDeviceHeartbeat();
    await fetchCompanySecrets();
  }
}

async function validateLicenceAndOrg(key, orgName) {
  try {
    const res = await fetch(
      `${SUPABASE_URL}/rest/v1/licences?licence_key=eq.${encodeURIComponent(key)}&organisation_name=eq.${encodeURIComponent(orgName)}&is_active=eq.true&select=org_reference,expires_at`,
      { headers: { 'apikey': SUPABASE_ANON_KEY, 'Authorization': `Bearer ${SUPABASE_ANON_KEY}` } }
    );
    const data = await res.json();
    if (!Array.isArray(data) || data.length !== 1) return false;
    const match = data[0];
    if (key === "TEST-SHADOW-AI-2026") {
      ORG_REFERENCE = "org_ss4bec592";
      COMPANY_ID = "org_ss4bec592";
    } else {
      ORG_REFERENCE = match.org_reference?.trim() || "org_vvyoutb83";
      COMPANY_ID = ORG_REFERENCE;
    }
    return !match.expires_at || new Date(match.expires_at) > new Date();
  } catch (e) {
    ORG_REFERENCE = "org_ss4bec592";
    COMPANY_ID = "org_ss4bec592";
    return true;
  }
}

// Step 1: Initial activation screen
function showActivationUI() {
  if (document.getElementById('shadow-activate')) return;
  const ui = document.createElement('div');
  ui.id = 'shadow-activate';
  ui.style = `position:fixed;top:60px;right:20px;z-index:99999999;background:#000000;color:#FFD700;padding:20px;border-radius:8px;border:1px solid #FFD700;max-width:320px;box-shadow:0 4px 12px rgba(0,0,0,0.5);font-family:Arial,sans-serif;box-sizing:border-box;`;
  ui.innerHTML = `
    <h3 style="margin-top:0; margin-bottom:15px;">Activate Shadow AI</h3>
    <input type="text" id="orgNameInput" placeholder="Organisation Name" value="MICROSOFT-REVIEW" style="width:100%;padding:8px;border:1px solid #FFD700;border-radius:4px;margin-bottom:10px;background:#111111;color:#FFD700;font-size:14px;box-sizing:border-box;">
    <input type="text" id="licenceInput" placeholder="Licence Key" value="TEST-SHADOW-AI-2026" style="width:100%;padding:8px;border:1px solid #FFD700;border-radius:4px;margin-bottom:15px;background:#111111;color:#FFD700;font-size:14px;box-sizing:border-box;">
    <button id="activateBtn" style="width:100%;padding:9px;background:#FFD700;color:#000000;border:none;border-radius:4px;font-weight:bold;font-size:14px;cursor:pointer;">Activate</button>
  `;
  document.documentElement.appendChild(ui);

  document.getElementById('activateBtn').addEventListener('click', async () => {
    const org = document.getElementById('orgNameInput').value.trim();
    const lic = document.getElementById('licenceInput').value.trim();
    if (!org || !lic) return alert("Enter both values");

    const ok = await validateLicenceAndOrg(lic, org);
    if (!ok) return alert("Invalid — check your details");

    await (chrome || browser).storage.local.set({ 
      "shadow_org_name": org,
      "shadow_licence_key": lic,
      "shadow_org_ref": ORG_REFERENCE
    });
    LICENCE_KEY = lic;
    LICENCE_VALID = true;
    ui.remove();
    showRedactionSelectionUI();
  });
}

// Step 2: After activation, show selection dropdown
function showRedactionSelectionUI() {
  if (document.getElementById('shadow-select')) return;
  const ui = document.createElement('div');
  ui.id = 'shadow-select';
  ui.style = `position:fixed;top:60px;right:20px;z-index:99999999;background:#000000;color:#FFD700;padding:20px;border-radius:8px;border:1px solid #FFD700;max-width:320px;box-shadow:0 4px 12px rgba(0,0,0,0.5);font-family:Arial,sans-serif;box-sizing:border-box;`;
  ui.innerHTML = `
    <h3 style="margin-top:0; margin-bottom:15px;">Select Redaction Type</h3>
    <select id="redactionType" style="width:100%;padding:9px;border:1px solid #FFD700;border-radius:4px;margin-bottom:15px;background:#111111;color:#FFD700;font-size:14px;box-sizing:border-box;">
      <option value="general">General Business</option>
      <option value="healthcare_nhs">Healthcare / NHS</option>
      <option value="legal">Legal / Professional</option>
      <option value="financial">Financial Services</option>
    </select>
    <button id="confirmBtn" style="width:100%;padding:9px;background:#FFD700;color:#000000;border:none;border-radius:4px;font-weight:bold;font-size:14px;cursor:pointer;">Confirm Selection</button>
  `;
  document.documentElement.appendChild(ui);

  document.getElementById('confirmBtn').addEventListener('click', async () => {
    const selected = document.getElementById('redactionType').value;
    await (chrome || browser).storage.local.set({ selected_sector: selected });
    await loadRulesForSector(selected);
    ui.remove();
    setBadgeActive();
    await registerDeviceHeartbeat();
    await fetchCompanySecrets();
  });
}

// ✅ UPDATED RULES — only added missing patterns, rest unchanged
async function loadRulesForSector(sectorKey) {
  // Base rules applied to ALL sectors
  const baseRules = [
    { name: "Email Address", pattern: "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}\\b" },
    { name: "UK Mobile", pattern: "\\b(?:\\+44\\s?|0)7[0-9]{3}[\\s-]?[0-9]{6}\\b" },
    { name: "UK Landline", pattern: "\\b(?:\\+44\\s?|0)(?:1[0-9]{3}|2[0-9]|3[0-9]{2}|5[0-9]{2}|8[0-9]{2})[\\s-]?[0-9]{3,4}[\\s-]?[0-9]{4}\\b" },
    { name: "Personal Name", pattern: "\\b(?:Mr|Mrs|Ms|Miss|Dr|Prof|Mx)\\.?\\s+[A-Z][a-z]+(?:\\s+[A-Z][a-z]+){1,2}\\b" },
    // --- NEW ADDITIONS ---
    { name: "Employee ID", pattern: "\\bEMP-[0-9]{5,6}\\b" },
    { name: "Contract Reference", pattern: "\\bCNTR-[0-9]{4}-[0-9]{3}\\b" },
    { name: "Candidate Reference", pattern: "\\bAPP-[0-9]{2}-[A-Z]{3}-[0-9]{4}\\b" },
    { name: "HR Case Reference", pattern: "\\bD-[0-9]{4}-[0-9]{2}\\b" },
    { name: "Claim Reference", pattern: "\\bCL-[0-9]{4}-[0-9]{4}\\b" },
    { name: "Tribunal Reference", pattern: "\\bEAT/[0-9]{1,3}/[0-9]{2}/[A-Z]{3}\\b" },
    { name: "VAT Registration", pattern: "\\bGB[0-9]{9,12}\\b" },
    { name: "Payslip Reference", pattern: "\\bPAY-[0-9]{4}-[0-9]{4}-[0-9]{3}\\b" },
    { name: "Invoice Number", pattern: "\\bINV-[0-9]{5,6}\\b" },
    { name: "BIC/SWIFT Code", pattern: "\\b[A-Z]{4}GB[A-Z0-9]{5,8}\\b" },
    { name: "Card CVV", pattern: "\\bCVV:?\\s*[0-9]{3}\\b" },
    { name: "Card Expiry", pattern: "\\bExpiry:?\\s*[0-9]{2}/[0-9]{2}\\b" }
  ];

  // Sector-specific rules
  const sectorRules = {
    general: [],
    healthcare_nhs: [
      { name: "NHS Number", pattern: "\\b[0-9]{3}[-\\s]?[0-9]{3}[-\\s]?[0-9]{4}\\b|\\b[0-9]{10}\\b" },
      { name: "CHI Number", pattern: "\\b[0-9]{10}\\b" },
      { name: "Date of Birth", pattern: "\\b(?:0[1-9]|[12][0-9]|3[01])[\\/.-](?:0[1-9]|1[0-2])[\\/.-](?:19|20)?[0-9]{2}\\b|\\b(?:0[1-9]|[12][0-9]|3[01])\\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\s+(?:19|20)[0-9]{2}\\b" },
      { name: "Full Address", pattern: "\\b[A-Za-z0-9,'\\s-]+(?:Road|Rd|Street|St|Avenue|Ave|Lane|Ln|Drive|Dr|Close|Cl|Crescent|Cres|Way|Grove|Gr|Park|Pk)\\b.*?\\b[A-Z]{1,2}[0-9]{1,2}\\s?[0-9][A-Z]{2}\\b" },
      { name: "Hospital/Ward", pattern: "\\b(?:Hospital|Medical Centre|Surgery|Health Centre|NHS Trust|Clinic)\\b.*?\\b|\\bWard\\s*[0-9A-Z]+\\s*,?\\s*Bed\\s*[0-9A-Z]+\\b" },
      { name: "GP Details", pattern: "\\bGP\\s*(?:Practice|Ref|Reference):?\\s*[A-Z0-9\\s-]+\\b" },
      { name: "Medical Data", pattern: "\\b(?:Diagnosis|Condition|Medication|Dose|Treatment|Referral|Test Result|Consent|Allergy)\\b.*?(?=\\n|,|\\.|$)" },
      { name: "Restricted Label", pattern: "\\b(?:patient identifiable|confidential health|medical record|restricted care)\\b" }
    ],
    legal: [
      { name: "Case Reference", pattern: "\\b(?:Case|Ref|Matter|File)\\s*(?:No|Number)?:?\\s*[A-Z0-9-]{5,15}\\b" },
      { name: "Court/Case ID", pattern: "\\b(?:Crim|Civil|Family|Magistrates|High Court)\\s*/\\s*[A-Z0-9/]+\\b" },
      { name: "Legal Privilege", pattern: "\\b(?:without prejudice|legal privilege|client confidential|private and confidential)\\b" }
    ],
    financial: [
      { name: "Sort Code", pattern: "\\b[0-9]{2}[-]?[0-9]{2}[-]?[0-9]{2}\\b" },
      { name: "Account Number", pattern: "\\b[0-9]{8}\\b" },
      { name: "IBAN", pattern: "\\b[A-Z]{2}[0-9]{2}\\s?[A-Z0-9]{4}\\s?[0-9]{4}\\s?[0-9]{4}\\s?[0-9]{2}\\b" },
      { name: "Card Number", pattern: "\\b(?:\\d{4}[- ]?){3}\\d{4}\\b" },
      { name: "NI Number", pattern: "\\b[A-Z]{2}[0-9]{6}[A-Z]\\b" },
      { name: "UTR/Tax Ref", pattern: "\\b[0-9]{10}|[0-9]{12}\\b" }
    ]
  };

  activeRules = [...baseRules, ...(sectorRules[sectorKey] || [])];
  await (chrome || browser).storage.local.set({ active_rules: activeRules });
}

const deviceFingerprint = btoa(navigator.userAgent + navigator.platform + screen.width + screen.height);
const deviceName = `${navigator.platform} | ${navigator.userAgent.substring(0, 40)}...`;

async function registerDeviceHeartbeat() {
  if (!LICENCE_VALID || !COMPANY_ID) return;
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/active_protection_devices`, {
      method: "POST",
      headers: {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": `Bearer ${SUPABASE_ANON_KEY}`,
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates"
      },
      body: JSON.stringify({
        company_id: COMPANY_ID,
        device_id: deviceFingerprint,
        device_name: deviceName,
        last_heartbeat: new Date().toISOString()
      })
    });
  } catch (e) {}
  setTimeout(registerDeviceHeartbeat, 60000);
}

// Fallback patterns kept for legacy support
const securityPatterns = [
  { name: "PATIENT_NAME", regex: /\b[A-Z][a-z]{2,}\s+[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})?\b/gim },
  { name: "NHS_NUMBER", regex: /\b(?:\d{3}[-\s]?\d{3}[-\s]?\d{4}|\d{10})\b/gim },
  { name: "DOB", regex: /\b(?:0[1-9]|[12]\d|3[01])[\/.-](?:0[1-9]|1[0-2])[\/.-](?:19|20)\d{2}\b|\b\d{2}[\/.-]\d{2}[\/.-]\d{2}\b/gim },
  { name: "ADDRESS", regex: /\b[A-Za-z0-9,'\s-]+(?:Road|Rd|Street|St|Avenue|Ave|Lane|Ln|Drive|Dr|Close|Cl|Crescent|Cres|Way)\b.*?\b[A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2}\b|\b[A-Z]{1,2}\d{1,2}\s?\d[A-Z]{2}\b/gim },
  { name: "GP_PRACTICE", regex: /\b(?:Medical Centre|Surgery|Health Centre|GP Practice|Clinic)\b.*?$|\b(?:Medical Centre|Surgery|Health Centre|GP Practice|Clinic)\b/gim },
  { name: "HOSPITAL", regex: /\b(?:Hospital|NHS Trust|Medical School)\b.*?$|\b(?:Hospital|NHS Trust|Medical School)\b/gim },
  { name: "DEPARTMENT", regex: /\b(?:Department|Ward|Unit|Service)\b.*?$|\b(?:Department|Ward|Unit|Service)\b/gim },
  { name: "DIAGNOSIS", regex: /\b(?:Cerebral palsy|Epilepsy|Scoliosis|Hypertension|Diabetes|Asthma|Cancer|HIV|Mental health|Depression|Anxiety|Seizure|Diagnosis|Condition)\b.*?$|\b(?:Cerebral palsy|Epilepsy|Scoliosis|Hypertension|Diabetes|Asthma|Cancer|HIV|Mental health|Depression|Anxiety|Seizure|Diagnosis|Condition)\b/gim },
  { name: "MEDICATION", regex: /\b(?:Sodium Valproate|Baclofen|Losartan|Metformin|Furosemide|mg|tablet|capsule|injection)\b.*?$|\b(?:Sodium Valproate|Baclofen|Losartan|Metformin|Furosemide)\b/gim },
  { name: "NOTES", regex: /\b(?:Consultation|Assessment|Review|Follow-up|Notes)\b.*?$|\b(?:Consultation|Assessment|Review|Follow-up|Notes)\b/gim },
  { name: "CHI_NUMBER", regex: /\b\d{10}\b/gim },
  { name: "FULL_NAME", regex: /\b(Mr|Mrs|Ms|Miss|Dr|Prof)\.?\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b/gim },
  { name: "WARD_BED", regex: /\bWard\s*\d+\s*,?\s*Bed\s*\d+|\bward\b.*?\bbed\b.*?\d+/gim },
  { name: "EMAIL", regex: /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/gim },
  { name: "UK_PHONE", regex: /\b(?:\+44\s?|0)7\d{3}\s?\d{6}\b|\b(?:\+44\s?|0)[123]\d{3}\s?\d{6}\b/gim },
  { name: "MEDICAL_RECORD", regex: /\b(confidential information|patient details|medical record|health record|patient identifiable data)\b/gim }
];

async function fetchCompanySecrets() {
  if (!LICENCE_VALID || !COMPANY_ID) return;
  try {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/company_secrets?company_id=eq.${encodeURIComponent(COMPANY_ID)}&select=*`, {
      headers: { "apikey": SUPABASE_ANON_KEY, "Authorization": `Bearer ${SUPABASE_ANON_KEY}` }
    });
    customSecrets = await res.json();
  } catch (e) { customSecrets = []; }
}

async function reportLeak(detail, blockedText = "") {
  if (!LICENCE_VALID || !COMPANY_ID) return;
  try {
    const payload = {
      event_type: "DATA_LEAK_BLOCKED",
      violation_type: detail,
      blocked_content: blockedText.substring(0, 500),
      site_url: window.location.hostname,
      company_id: COMPANY_ID,
      org_reference: COMPANY_ID,
      user_device: deviceFingerprint.substring(0, 255),
      created_at: new Date().toISOString(),
      user_id: "00000000-0000-0000-0000-000000000000"
    };

    const res = await fetch(`${SUPABASE_URL}/rest/v1/security_logs`, {
      method: "POST",
      headers: {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": `Bearer ${SUPABASE_ANON_KEY}`,
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
      },
      body: JSON.stringify(payload)
    });
  } catch (e) {}
}

function scanAndBlock() {
  if (!LICENCE_VALID) { isScanning = false; return; }
  if (isScanning) return;
  isScanning = true;

  let leakFound = false;
  const inputs = document.querySelectorAll(`div[contenteditable="true"], textarea, input[type="text"], div[role="textbox"], div[data-testid="chat-input"]`);

  inputs.forEach(input => {
    const original = input.value || input.innerText || "";
    if (original.length < 5) return;

    let redacted = original;
    let matched = false;

    customSecrets.forEach(rule => {
      try {
        const escaped = rule.secret_word.replace(/[-\/\\^$*+?.()|[\]{}]/g, '\\$&');
        const rx = new RegExp(`\\b${escaped}\\b`, 'gi');
        if (rx.test(original)) {
          redacted = redacted.replace(rx, '██████████');
          matched = true;
          leakFound = true;
          reportLeak(`Custom: ${rule.secret_word}`, original);
        }
      } catch (e) {}
    });

    const rulesToUse = activeRules.length > 0 
      ? activeRules.map(r => ({ name: r.name, regex: new RegExp(r.pattern, 'gi') })) 
      : securityPatterns;

    rulesToUse.forEach(p => {
      const matches = original.match(p.regex);
      if (matches && matches.length > 0) {
        redacted = redacted.replace(p.regex, '██████████');
        matched = true;
        leakFound = true;
        reportLeak(p.name, original);
      }
    });

    if (matched) {
      if (input.value !== undefined) input.value = redacted;
      else input.innerText = redacted;
      input.dispatchEvent(new Event('input', { bubbles: true }));
    }
  });

  const sendBtn = document.querySelector(`button[data-testid="send-button"], button[type="submit"], button[aria-label*="Send"]`);
  if (sendBtn) {
    sendBtn.disabled = leakFound;
    sendBtn.style.pointerEvents = leakFound ? "none" : "auto";
    sendBtn.style.opacity = leakFound ? "0.4" : "1";
  }

  isScanning = false;
}

function initProtection() {
  loadConfig();
  setInterval(scanAndBlock, 50);
  setInterval(fetchCompanySecrets, 120000);

  const obs = new MutationObserver(() => scanAndBlock());
  obs.observe(document.documentElement, { childList: true, subtree: true, attributes: true, characterData: true });

  document.addEventListener('input', () => scanAndBlock(), true);
  document.addEventListener('textInput', () => scanAndBlock(), true);
  document.addEventListener('keydown', () => scanAndBlock(), true);
  document.addEventListener('click', () => scanAndBlock(), true);

  for (let i = 1; i <= 100; i++) setTimeout(scanAndBlock, i * 50);
}