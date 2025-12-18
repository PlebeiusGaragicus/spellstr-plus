<script>
  import { cyphertap } from 'cyphertap';

  const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

  let isAuthenticated = $state(false);
  let authError = $state(null);
  let isLoading = $state(false);
  
  let stats = $state(null);
  let proofs = $state(null);
  let statsError = $state(null);
  
  let sweepResult = $state(null);
  let payoutResult = $state(null);
  let actionLoading = $state(null);

  function getAuthHeaders() {
    if (!cyphertap?.npub) return {};
    return { 'x-npub': cyphertap.npub };
  }

  async function login() {
    isLoading = true;
    authError = null;
    
    try {
      const res = await fetch(`${API_URL}/admin/verify`, {
        method: 'POST',
        headers: {
          ...getAuthHeaders(),
        },
      });
      
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Authentication failed');
      }
      
      isAuthenticated = true;
      await loadStats();
    } catch (err) {
      authError = err.message;
    } finally {
      isLoading = false;
    }
  }

  async function loadStats() {
    statsError = null;
    try {
      const [statsRes, proofsRes] = await Promise.all([
        fetch(`${API_URL}/admin/stats`, {
          headers: { ...getAuthHeaders() },
        }),
        fetch(`${API_URL}/admin/proofs`, {
          headers: { ...getAuthHeaders() },
        }),
      ]);
      
      if (!statsRes.ok || !proofsRes.ok) {
        throw new Error('Failed to load stats');
      }
      
      stats = await statsRes.json();
      proofs = await proofsRes.json();
    } catch (err) {
      statsError = err.message;
    }
  }

  async function triggerPayout() {
    actionLoading = 'payout';
    payoutResult = null;
    
    try {
      const res = await fetch(`${API_URL}/admin/payout`, {
        method: 'POST',
        headers: { ...getAuthHeaders() },
      });
      
      payoutResult = await res.json();
      await loadStats();
    } catch (err) {
      payoutResult = { success: false, error: err.message };
    } finally {
      actionLoading = null;
    }
  }

  async function triggerSweep() {
    actionLoading = 'sweep';
    sweepResult = null;
    
    try {
      const res = await fetch(`${API_URL}/admin/sweep`, {
        method: 'POST',
        headers: { ...getAuthHeaders() },
      });
      
      sweepResult = await res.json();
      await loadStats();
    } catch (err) {
      sweepResult = { success: false, error: err.message };
    } finally {
      actionLoading = null;
    }
  }

  function logout() {
    isAuthenticated = false;
    stats = null;
    proofs = null;
    sweepResult = null;
    payoutResult = null;
  }

  function copyToken() {
    if (sweepResult?.token) {
      navigator.clipboard.writeText(sweepResult.token);
    }
  }
</script>

<div class="admin-container">
  {#if !isAuthenticated}
    <div class="login-card">
      <h2>🔐 Admin Login</h2>
      
      <form onsubmit={(e) => { e.preventDefault(); login(); }}>
        {#if authError}
          <p class="error">{authError}</p>
        {/if}
        
        <button
          type="submit"
          disabled={isLoading || !cyphertap.isLoggedIn || !cyphertap.npub}
          class="btn btn-primary"
        >
          {#if !cyphertap.isLoggedIn}
            Login with Nostr first
          {:else if isLoading}
            Verifying...
          {:else}
            Verify Admin Access
          {/if}
        </button>
      </form>
    </div>
  {:else}
    <div class="dashboard">
      <div class="dashboard-header">
        <h2>📊 Admin Dashboard</h2>
        <button onclick={logout} class="btn btn-secondary btn-sm">
          Logout
        </button>
      </div>

      {#if statsError}
        <p class="error">{statsError}</p>
      {:else if stats}
        <div class="stats-grid">
          <div class="stat-card">
            <p class="stat-label">Wallet Balance</p>
            <p class="stat-value orange">{stats.wallet_balance} <span class="stat-unit">sats</span></p>
          </div>
          
          <div class="stat-card">
            <p class="stat-label">Sessions Created</p>
            <p class="stat-value green">{stats.sessions_count}</p>
          </div>
          
          <div class="stat-card">
            <p class="stat-label">Proof Count</p>
            <p class="stat-value blue">{stats.proof_count}</p>
          </div>
        </div>

        <div class="config-card">
          <h3>Configuration</h3>
          <div class="config-grid">
            <div class="config-item">
              <span class="config-label">Default Mint:</span>
              <span class="config-value mono">{stats.default_mint}</span>
            </div>
            <div class="config-item">
              <span class="config-label">Wallet DB:</span>
              <span class="config-value mono">{stats.wallet_db}</span>
            </div>
          </div>
        </div>

        <div class="actions-card">
          <h3>Actions</h3>
          <div class="actions-buttons">
            <button
              onclick={triggerSweep}
              disabled={actionLoading}
              class="btn btn-warning"
            >
              {actionLoading === 'sweep' ? 'Processing...' : '💰 Sweep to Token'}
            </button>
            
            <button
              onclick={loadStats}
              disabled={actionLoading}
              class="btn btn-secondary"
            >
              🔄 Refresh
            </button>
          </div>
          
          {#if sweepResult}
            <div class="result-box {sweepResult.success ? 'success' : 'error'}">
              {#if sweepResult.success}
                <p>Swept {sweepResult.amount} sats to token:</p>
                <div class="token-row">
                  <input
                    type="text"
                    readonly
                    value={sweepResult.token}
                    class="token-input"
                  />
                  <button onclick={copyToken} class="btn btn-secondary btn-sm">
                    Copy
                  </button>
                </div>
              {:else}
                <p>Sweep failed: {sweepResult.error}</p>
              {/if}
            </div>
          {/if}
        </div>

        {#if proofs && proofs.proofs?.length > 0}
          <div class="proofs-card">
            <h3>Proofs ({proofs.count})</h3>
            <div class="table-container">
              <table>
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Amount</th>
                    <th>Keyset ID</th>
                  </tr>
                </thead>
                <tbody>
                  {#each proofs.proofs as proof, i}
                    <tr>
                      <td class="muted">{i + 1}</td>
                      <td class="amount">{proof.amount} sats</td>
                      <td class="mono">{proof.keyset_id}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        {/if}
      {:else}
        <p class="muted">Loading stats...</p>
      {/if}
    </div>
  {/if}
</div>

<style>
  .admin-container {
    max-width: 900px;
    margin: 40px auto;
    padding: 0 20px;
  }

  .login-card {
    max-width: 400px;
    margin: 0 auto;
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 32px;
    text-align: center;
  }

  .login-card h2 {
    margin: 0 0 24px 0;
    font-size: 24px;
  }

  .login-card form {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .dashboard {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .dashboard-header h2 {
    margin: 0;
    font-size: 24px;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
  }

  .stat-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }

  .stat-label {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: var(--muted);
  }

  .stat-value {
    margin: 0;
    font-size: 32px;
    font-weight: 700;
  }

  .stat-value.orange { color: #f97316; }
  .stat-value.green { color: #22c55e; }
  .stat-value.blue { color: #3b82f6; }

  .stat-unit {
    font-size: 16px;
    color: var(--muted);
    font-weight: 400;
  }

  .config-card, .actions-card, .proofs-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }

  .config-card h3, .actions-card h3, .proofs-card h3 {
    margin: 0 0 16px 0;
    font-size: 18px;
  }

  .config-grid {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .config-item {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .config-label {
    color: var(--muted);
    font-size: 14px;
  }

  .config-value {
    font-size: 14px;
    word-break: break-all;
  }

  .mono {
    font-family: monospace;
    font-size: 12px;
  }

  .actions-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
  }

  .result-box {
    margin-top: 16px;
    padding: 16px;
    border-radius: 8px;
  }

  .result-box.success {
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.3);
  }

  .result-box.error {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
  }

  .result-box p {
    margin: 0 0 12px 0;
  }

  .token-row {
    display: flex;
    gap: 8px;
  }

  .token-input {
    flex: 1;
    padding: 8px 12px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    font-family: monospace;
    font-size: 11px;
  }

  .table-container {
    overflow-x: auto;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }

  th, td {
    text-align: left;
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
  }

  th {
    color: var(--muted);
    font-weight: 500;
  }

  .muted {
    color: var(--muted);
  }

  .amount {
    color: #f97316;
    font-weight: 600;
  }

  .error {
    color: var(--warn);
    font-size: 14px;
  }

  .btn {
    padding: 12px 20px;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-primary {
    background: linear-gradient(135deg, #8b5cf6, #6366f1);
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    transform: translateY(-1px);
  }

  .btn-secondary {
    background: var(--border);
    color: var(--text);
  }

  .btn-secondary:hover:not(:disabled) {
    background: #3a4a6b;
  }

  .btn-warning {
    background: #d97706;
    color: white;
  }

  .btn-warning:hover:not(:disabled) {
    background: #b45309;
  }

  .btn-sm {
    padding: 8px 14px;
    font-size: 13px;
  }
</style>
