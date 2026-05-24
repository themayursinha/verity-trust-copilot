(function () {
  function escapeHtml(text) {
    const d = document.createElement('div');
    d.textContent = text;
    return d.innerHTML;
  }

  const policyList = document.getElementById('policyList');
  const modal = document.getElementById('policyModal');
  const modalTitle = document.getElementById('modalTitle');
  const form = document.getElementById('policyForm');
  const policyId = document.getElementById('policyId');
  const fieldTitle = document.getElementById('fieldTitle');
  const fieldCategory = document.getElementById('fieldCategory');
  const fieldContent = document.getElementById('fieldContent');
  const fieldReviewInterval = document.getElementById('fieldReviewInterval');
  const btnCloseModal = document.getElementById('btnCloseModal');
  const btnCancelModal = document.getElementById('btnCancelModal');
  const btnNewPolicy = document.getElementById('btnNewPolicy');
  let policiesById = new Map();

  async function loadPolicies() {
    try {
      const resp = await fetch('/api/policies');
      if (!resp.ok) throw new Error('Failed to load policies');
      const policies = await resp.json();
      if (!Array.isArray(policies) || policies.length === 0) {
        policyList.innerHTML = '<div class="dash-empty">No policies yet. Create your first policy above.</div>';
        return;
      }
      policiesById = new Map(policies.map(p => [String(p.id), p]));
      const html = policies.map(p => {
        const statusClass = p.status === 'active' ? 'badge-active' : 'badge-draft';
        const reviewDate = p.next_review ? new Date(p.next_review).toLocaleDateString() : 'Not set';
        const id = escapeHtml(p.id);
        return `<div class="policy-card">
          <div class="policy-card-header">
            <strong>${escapeHtml(p.title)}</strong>
            <span class="badge ${statusClass}">${escapeHtml(p.status)}</span>
          </div>
          <div class="policy-card-meta">
            <span>Category: ${escapeHtml(p.category)}</span>
            <span>Version: ${escapeHtml(p.version)}</span>
            <span>Next review: ${escapeHtml(reviewDate)}</span>
          </div>
          <div class="policy-card-actions">
            <button class="ghost-button" data-edit-id="${id}">Edit</button>
            <button class="ghost-button ghost-danger" data-id="${id}">Delete</button>
          </div>
        </div>`;
      }).join('');
      policyList.innerHTML = html;

      policyList.querySelectorAll('[data-edit-id]').forEach(btn => {
        btn.addEventListener('click', () => {
          const policy = policiesById.get(String(btn.dataset.editId));
          if (policy) openEditModal(policy);
        });
      });
      policyList.querySelectorAll('.ghost-danger').forEach(btn => {
        btn.addEventListener('click', () => deletePolicy(btn.dataset.id));
      });
    } catch (e) {
      policyList.innerHTML = '<div class="dash-empty">Error loading policies.</div>';
    }
  }

  function openNewModal() {
    modalTitle.textContent = 'New Policy';
    policyId.value = '';
    form.reset();
    modal.style.display = 'flex';
  }

  function openEditModal(policy) {
    modalTitle.textContent = 'Edit Policy';
    policyId.value = policy.id;
    fieldTitle.value = policy.title;
    fieldCategory.value = policy.category;
    fieldContent.value = policy.content;
    fieldReviewInterval.value = policy.review_interval_months || 12;
    modal.style.display = 'flex';
  }

  function closeModal() {
    modal.style.display = 'none';
  }

  async function savePolicy(data) {
    const isEdit = !!data.id;
    const url = '/api/policies' + (isEdit ? '/' + data.id : '');
    const method = isEdit ? 'PUT' : 'POST';
    try {
      const resp = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!resp.ok) throw new Error('Save failed');
      closeModal();
      loadPolicies();
    } catch (e) {
      alert('Error saving policy: ' + e.message);
    }
  }

  async function deletePolicy(id) {
    if (!confirm('Delete this policy?')) return;
    try {
      const resp = await fetch('/api/policies/' + id, { method: 'DELETE' });
      if (!resp.ok) throw new Error('Delete failed');
      loadPolicies();
    } catch (e) {
      alert('Error deleting policy: ' + e.message);
    }
  }

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    savePolicy({
      id: policyId.value || undefined,
      title: fieldTitle.value,
      category: fieldCategory.value,
      content: fieldContent.value,
      review_interval_months: parseInt(fieldReviewInterval.value, 10)
    });
  });

  btnNewPolicy.addEventListener('click', openNewModal);
  btnCloseModal.addEventListener('click', closeModal);
  btnCancelModal.addEventListener('click', closeModal);
  modal.addEventListener('click', function (e) {
    if (e.target === modal) closeModal();
  });

  loadPolicies();
})();
