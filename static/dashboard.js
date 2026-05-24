(function () {
  function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
  }

  async function loadOverview() {
    try {
      const [overviewResp, vantaResp] = await Promise.all([
        fetch('/api/dashboard/overview'),
        fetch('/api/vanta/status')
      ]);
      if (!overviewResp.ok) throw new Error('Failed to load overview');
      const data = await overviewResp.json();
      renderFrameworkCoverage(data.frameworks);
      renderEvidenceSummary(data.evidence);
      renderPolicies(data.policies);
      renderApprovals(data.approvals);
      renderActivity(data.recent_activity);

      const vantaConfig = vantaResp.ok ? await vantaResp.json() : null;
      renderVanta(vantaConfig);
    } catch (e) {
      document.querySelectorAll('.dash-placeholder').forEach(el => {
        el.textContent = 'Error loading data: ' + e.message;
      });
    }
  }

  function renderFrameworkCoverage(frameworks) {
    const container = document.getElementById('frameworkCoverage');
    if (!frameworks || frameworks.length === 0) {
      container.innerHTML = '<div class="dash-empty">No framework data yet.</div>';
      return;
    }
    const FRAMEWORK_LABELS = {
      'iso-27001': 'ISO 27001',
      'soc-2': 'SOC 2',
      'gdpr': 'GDPR',
      'dora': 'DORA',
      'fedramp': 'FedRAMP'
    };
    const html = frameworks.map(fw => {
      const label = FRAMEWORK_LABELS[fw.id] || fw.id;
      const pct = Math.round(fw.coverage * 100);
      return `<div class="fw-row">
        <div class="fw-header">
          <span class="fw-label">${escapeHtml(label)}</span>
          <span class="fw-pct">${pct}%</span>
        </div>
        <div class="fw-bar-bg">
          <div class="fw-bar-fill" style="width:${pct}%" role="progressbar" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100"></div>
        </div>
        <div class="fw-meta">
          <span>${fw.evidence_count} evidence items</span>
          <span>${fw.control_count} controls mapped</span>
        </div>
      </div>`;
    }).join('');
    container.innerHTML = html;
  }

  function renderEvidenceSummary(evidence) {
    const container = document.getElementById('dashEvidence');
    if (!evidence) {
      container.innerHTML = '<div class="dash-empty">No evidence loaded.</div>';
      return;
    }
    container.innerHTML = `<div class="stat-row">
      <div class="stat-block"><strong>${evidence.total}</strong><span>Total Evidence</span></div>
      <div class="stat-block"><strong>${evidence.fresh}</strong><span>Fresh (≤180d)</span></div>
      <div class="stat-block"><strong>${evidence.stale}</strong><span>Stale (≥365d)</span></div>
      <div class="stat-block"><strong>${evidence.frameworks_covered}</strong><span>Frameworks</span></div>
    </div>`;
  }

  function renderPolicies(policies) {
    const container = document.getElementById('dashPolicies');
    if (!policies) {
      container.innerHTML = '<div class="dash-empty">No policies yet.</div>';
      return;
    }
    container.innerHTML = `<div class="stat-row">
      <div class="stat-block"><strong>${policies.total}</strong><span>Total Policies</span></div>
      <div class="stat-block"><strong>${policies.active}</strong><span>Active</span></div>
      <div class="stat-block"><strong>${policies.draft}</strong><span>Draft</span></div>
      <div class="stat-block"><strong>${policies.upcoming_reviews}</strong><span>Review Due</span></div>
    </div>
    <div style="margin-top:0.75rem"><a href="/static/policies.html" style="font-size:0.9rem">Manage Policies →</a></div>`;
  }

  function renderApprovals(approvals) {
    const container = document.getElementById('dashApprovals');
    if (!approvals) {
      container.innerHTML = '<div class="dash-empty">No approvals yet.</div>';
      return;
    }
    container.innerHTML = `<div class="stat-row">
      <div class="stat-block"><strong>${approvals.total}</strong><span>Total</span></div>
      <div class="stat-block"><strong>${approvals.approved}</strong><span>Approved</span></div>
      <div class="stat-block"><strong>${approvals.rejected}</strong><span>Rejected</span></div>
      <div class="stat-block"><strong>${approvals.unreviewed}</strong><span>Unreviewed</span></div>
    </div>`;
  }

  function renderVanta(config) {
    const container = document.getElementById('dashVanta');
    if (!config || !config.connected) {
      container.innerHTML = '<div class="vanta-disconnected">' +
        '<p style="margin:0 0 10px;color:var(--muted)">Not connected to Vanta. Evidence can be imported automatically from your Vanta workspace.</p>' +
        '<button id="vantaConnectBtn" class="button-primary">Connect Vanta</button>' +
        '<div id="vantaConnectForm" style="display:none;margin-top:10px">' +
          '<input type="text" id="vantaApiKey" placeholder="Vanta API Key" style="margin-bottom:8px">' +
          '<input type="text" id="vantaOrgId" placeholder="Organization ID" style="margin-bottom:8px">' +
          '<button id="vantaSyncBtn" class="button-primary">Sync Evidence</button>' +
        '</div>' +
      '</div>';
      const connectBtn = document.getElementById('vantaConnectBtn');
      const form = document.getElementById('vantaConnectForm');
      const syncBtn = document.getElementById('vantaSyncBtn');
      connectBtn.addEventListener('click', function () {
        form.style.display = 'block';
        connectBtn.style.display = 'none';
      });
      syncBtn.addEventListener('click', vantaSync);
      return;
    }
    const lastSync = config.last_sync ? new Date(config.last_sync).toLocaleString() : 'Never';
    container.innerHTML = '<div class="vanta-connected">' +
      '<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">' +
        '<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#2f7d32"></span>' +
        '<strong>Connected</strong>' +
      '</div>' +
      '<p style="margin:0 0 4px;font-size:13px;color:var(--muted)">Last sync: ' + escapeHtml(lastSync) + '</p>' +
      '<p style="margin:0 0 10px;font-size:13px;color:var(--muted)">Org: ' + escapeHtml(config.organization_id || '—') + '</p>' +
      '<button id="vantaSyncBtn" class="button-primary">Resync Evidence</button>' +
    '</div>';
    document.getElementById('vantaSyncBtn').addEventListener('click', vantaSync);
  }

  async function vantaSync() {
    const btn = document.getElementById('vantaSyncBtn');
    if (btn) btn.disabled = true;
    const apiKey = document.getElementById('vantaApiKey') ? document.getElementById('vantaApiKey').value : '';
    const orgId = document.getElementById('vantaOrgId') ? document.getElementById('vantaOrgId').value : '';
    try {
      const resp = await fetch('/api/vanta/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: apiKey, organization_id: orgId })
      });
      if (!resp.ok) throw new Error('Sync failed');
      const result = await resp.json();
      alert('Vanta sync complete: ' + result.synced_count + ' evidence records imported.');
      loadOverview();
    } catch (e) {
      alert('Vanta sync error: ' + e.message);
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  function renderActivity(activities) {
    const container = document.getElementById('dashActivity');
    if (!activities || activities.length === 0) {
      container.innerHTML = '<div class="dash-empty">No recent activity.</div>';
      return;
    }
    const html = activities.slice(0, 10).map(a => {
      const time = a.timestamp ? new Date(a.timestamp).toLocaleString() : '';
      return `<div class="activity-item">
        <span class="activity-action">${escapeHtml(a.action)}</span>
        <span class="activity-detail">${escapeHtml(a.detail || '')}</span>
        <span class="activity-time">${escapeHtml(time)}</span>
      </div>`;
    }).join('');
    container.innerHTML = html;
  }

  loadOverview();
})();
