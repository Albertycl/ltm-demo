<template>
  <div class="shell">
    <header class="topbar">
      <div class="brand">
        <div class="logo">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="3" y="4" width="18" height="6" rx="2" /><rect x="3" y="14" width="18" height="6" rx="2" />
            <path d="M7 7h.01M7 17h.01" />
          </svg>
        </div>
        <div>
          <h1>LTM Node Control</h1>
          <p>Bulk enable / disable pool nodes</p>
        </div>
      </div>
      <span class="env"><i></i>Demo · simulated LTM</span>
    </header>

    <main class="grid">
      <!-- Step 1: targets -->
      <section class="card input">
        <div class="card-head">
          <span class="step">1</span>
          <div>
            <h2>Target nodes</h2>
            <p>One IP per line. Commas and spaces work too.</p>
          </div>
        </div>
        <textarea v-model="ipText" spellcheck="false" aria-label="Node IPs"></textarea>
        <div class="input-foot">
          <span class="count"><b>{{ ipCount }}</b> unique IPs</span>
          <div class="btns">
            <button class="btn ghost" @click="ipText = DEFAULT_IPS">Reset</button>
            <button class="btn primary" :disabled="!ipCount || loading" @click="onConfirm">
              <span v-if="loading" class="spin"></span>
              {{ loading ? 'Checking…' : 'Confirm' }}
            </button>
          </div>
        </div>
      </section>

      <!-- Step 2: result -->
      <section class="card result">
        <div class="card-head">
          <span class="step">2</span>
          <div>
            <h2>LTM status</h2>
            <p>Which of these IPs belong to LTM, and their state.</p>
          </div>
        </div>

        <div v-if="!rows.length" class="empty">
          <svg viewBox="0 0 120 90" width="140" fill="none">
            <rect x="10" y="12" width="100" height="22" rx="6" fill="var(--brand-soft)" stroke="var(--brand)" stroke-width="1.5" />
            <rect x="10" y="40" width="100" height="22" rx="6" fill="var(--surface-2)" stroke="var(--border)" stroke-width="1.5" />
            <rect x="10" y="68" width="100" height="14" rx="6" fill="var(--surface-2)" stroke="var(--border)" stroke-width="1.5" />
            <circle cx="24" cy="23" r="4" fill="var(--ok)" /><circle cx="24" cy="51" r="4" fill="var(--neutral)" />
            <rect x="36" y="20" width="46" height="6" rx="3" fill="var(--brand)" opacity=".35" />
            <rect x="36" y="48" width="34" height="6" rx="3" fill="var(--neutral)" opacity=".35" />
          </svg>
          <h3>No results yet</h3>
          <p>Press <b>Confirm</b> to check the IPs against LTM.</p>
        </div>

        <template v-else>
          <div class="stats">
            <div class="stat"><span>Total</span><b>{{ rows.length }}</b></div>
            <div class="stat"><span>In LTM</span><b>{{ inLtm.length }}</b><em>{{ pct(inLtm.length) }}%</em></div>
            <div class="stat"><span>Not in LTM</span><b>{{ rows.length - inLtm.length }}</b><em>{{ pct(rows.length - inLtm.length) }}%</em></div>
            <div class="stat ok"><span>Enabled</span><b>{{ count('enabled') }}</b></div>
            <div class="stat bad"><span>Disabled</span><b>{{ count('disabled') }}</b></div>
          </div>

          <div class="bar" role="img" :aria-label="`${count('enabled')} enabled, ${count('disabled')} disabled, ${rows.length - inLtm.length} not in LTM`">
            <i class="s-ok" :style="{ width: pct(count('enabled')) + '%' }"></i>
            <i class="s-bad" :style="{ width: pct(count('disabled')) + '%' }"></i>
            <i class="s-na" :style="{ width: pct(rows.length - inLtm.length) + '%' }"></i>
          </div>

          <div class="toolbar">
            <div class="seg">
              <button v-for="o in filterOptions" :key="o.value" :class="{ on: filter === o.value }" @click="filter = o.value">{{ o.label }}</button>
            </div>
            <input v-model="search" class="search" type="search" placeholder="Search IP or name" />
          </div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th class="chk">
                    <input type="checkbox" aria-label="Select all" :checked="allSelected" :indeterminate="someSelected && !allSelected"
                      :disabled="!selectable.length" @change="toggleAll($event.target.checked)" />
                  </th>
                  <th>IP address</th><th>Node</th><th>Partition</th><th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in shown" :key="r.ip" :class="{ na: !r.in_ltm, sel: selected.includes(r.ip) }">
                  <td class="chk">
                    <input type="checkbox" :aria-label="`Select ${r.ip}`" :value="r.ip" v-model="selected" :disabled="!r.in_ltm" />
                  </td>
                  <td class="mono">{{ r.ip }}</td>
                  <td>{{ r.name || '—' }}</td>
                  <td>{{ r.partition || '—' }}</td>
                  <td>
                    <span v-if="!r.in_ltm" class="pill na">{{ r.valid === false ? 'Invalid IP' : 'Not in LTM' }}</span>
                    <span v-else class="pill" :class="r.status"><i></i>{{ r.status === 'enabled' ? 'Enabled' : 'Disabled' }}</span>
                  </td>
                </tr>
                <tr v-if="!shown.length"><td colspan="5" class="none">No matching rows</td></tr>
              </tbody>
            </table>
          </div>

          <div class="actions">
            <span><b>{{ selected.length }}</b> of {{ inLtm.length }} LTM nodes selected.</span>
            <div class="btns">
              <button class="btn danger" :disabled="acting || !selected.length" @click="ask('disabled')">Disable {{ selected.length }} selected</button>
              <button class="btn ok" :disabled="acting || !selected.length" @click="ask('enabled')">Enable {{ selected.length }} selected</button>
            </div>
          </div>
        </template>
      </section>
    </main>

    <!-- Confirm dialog -->
    <div v-if="dialog" class="overlay" @click.self="dialog = null">
      <div class="modal" role="dialog" aria-modal="true">
        <div class="modal-ico" :class="dialog">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path v-if="dialog === 'disabled'" d="M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" />
            <path v-else d="M20 6 9 17l-5-5" />
          </svg>
        </div>
        <h3>{{ dialog === 'disabled' ? 'Disable' : 'Enable' }} {{ selected.length }} nodes?</h3>
        <p>This changes the state of the selected nodes in LTM{{ dialog === 'disabled' ? '. New connections stop going to them.' : '.' }}</p>
        <div class="btns end">
          <button class="btn ghost" @click="dialog = null">Cancel</button>
          <button class="btn" :class="dialog === 'disabled' ? 'danger-solid' : 'ok-solid'" @click="onAct">
            {{ dialog === 'disabled' ? 'Disable' : 'Enable' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Toast -->
    <transition name="toast">
      <div v-if="toast" class="toast" :class="toast.type">{{ toast.msg }}</div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { DEFAULT_IPS, check, setStatus } from './api'

const ipText = ref(DEFAULT_IPS)
const rows = ref([])
const loading = ref(false)
const acting = ref(false)
const filter = ref('all')
const search = ref('')
const dialog = ref(null)
const toast = ref(null)
const selected = ref([])

const filterOptions = [
  { label: 'All', value: 'all' },
  { label: 'In LTM', value: 'in' },
  { label: 'Not in LTM', value: 'out' },
]

const ipCount = computed(() => new Set(ipText.value.split(/[\s,;]+/).filter(Boolean)).size)
const inLtm = computed(() => rows.value.filter(r => r.in_ltm))
const count = s => inLtm.value.filter(r => r.status === s).length
const pct = n => (rows.value.length ? Math.round((n / rows.value.length) * 100) : 0)

const shown = computed(() => {
  const q = search.value.trim().toLowerCase()
  return rows.value.filter(r =>
    (filter.value === 'all' || (filter.value === 'in') === r.in_ltm) &&
    (!q || r.ip.includes(q) || (r.name || '').toLowerCase().includes(q)))
})

// rows that can be ticked: LTM nodes currently visible after filter/search
const selectable = computed(() => shown.value.filter(r => r.in_ltm).map(r => r.ip))
const allSelected = computed(() => selectable.value.length > 0 && selectable.value.every(ip => selected.value.includes(ip)))
const someSelected = computed(() => selectable.value.some(ip => selected.value.includes(ip)))

function toggleAll(on) {
  const rest = selected.value.filter(ip => !selectable.value.includes(ip))
  selected.value = on ? [...rest, ...selectable.value] : rest
}

let toastTimer
function notify(type, msg) {
  toast.value = { type, msg }
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.value = null), 3200)
}

async function onConfirm() {
  loading.value = true
  try {
    rows.value = await check(ipText.value)
    selected.value = rows.value.filter(r => r.in_ltm).map(r => r.ip)   // all LTM nodes ticked by default
  } catch (e) { notify('bad', e.message) }
  finally { loading.value = false }
}

const ask = status => (dialog.value = status)

async function onAct() {
  const status = dialog.value
  dialog.value = null
  acting.value = true
  try {
    const n = selected.value.length
    await setStatus(selected.value, status)
    rows.value = await check(ipText.value)
    notify(status === 'enabled' ? 'ok' : 'bad', `${n} nodes ${status}`)
  } catch (e) { notify('bad', e.message) }
  finally { acting.value = false }
}
</script>

<style scoped>
.shell { max-width: 1280px; margin: 0 auto; padding: 0 20px 40px; }

/* top bar */
.topbar { display: flex; align-items: center; justify-content: space-between; padding: 22px 0; gap: 12px; flex-wrap: wrap; }
.brand { display: flex; align-items: center; gap: 12px; }
.logo { width: 40px; height: 40px; border-radius: 11px; display: grid; place-items: center; color: #fff;
  background: linear-gradient(135deg, #6366f1, #4338ca); box-shadow: 0 6px 16px rgba(79, 70, 229, .35); }
h1 { font-size: 18px; margin: 0; letter-spacing: -.01em; }
.brand p { margin: 0; color: var(--muted); font-size: 12.5px; }
.env { display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; border-radius: 999px; font-size: 12px; font-weight: 500;
  background: var(--surface); border: 1px solid var(--border); color: var(--muted); }
.env i { width: 7px; height: 7px; border-radius: 50%; background: #f59e0b; box-shadow: 0 0 0 3px rgba(245, 158, 11, .2); }

/* layout */
.grid { display: grid; grid-template-columns: 380px 1fr; gap: 20px; align-items: start; }
@media (max-width: 960px) { .grid { grid-template-columns: 1fr; } }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); box-shadow: var(--shadow); padding: 20px; }
.card-head { display: flex; gap: 12px; align-items: flex-start; margin-bottom: 16px; }
.card-head h2 { font-size: 15px; margin: 0; }
.card-head p { margin: 2px 0 0; color: var(--muted); font-size: 12.5px; }
.step { flex: none; width: 26px; height: 26px; border-radius: 8px; display: grid; place-items: center; font-weight: 600; font-size: 12.5px;
  background: var(--brand-soft); color: var(--brand); }

/* input */
textarea { width: 100%; height: 440px; resize: vertical; padding: 12px 14px; border-radius: 10px; border: 1px solid var(--border);
  background: var(--surface-2); color: var(--text); font: 13px/1.7 var(--mono); outline: none; transition: border-color .15s, box-shadow .15s; }
textarea:focus { border-color: var(--brand); box-shadow: 0 0 0 3px var(--brand-soft); }
.input-foot { display: flex; align-items: center; justify-content: space-between; margin-top: 14px; gap: 10px; }
.count { color: var(--muted); font-size: 12.5px; }
.count b { color: var(--text); }

/* buttons */
.btns { display: flex; gap: 8px; }
.btns.end { justify-content: flex-end; margin-top: 20px; }
.btn { display: inline-flex; align-items: center; justify-content: center; gap: 8px; padding: 9px 16px; border-radius: 9px; font-weight: 600; font-size: 13px;
  border: 1px solid transparent; transition: transform .05s, background .15s, box-shadow .15s, opacity .15s; }
.btn:active:not(:disabled) { transform: translateY(1px); }
.btn:disabled { opacity: .5; cursor: not-allowed; }
.btn.primary { background: var(--brand-600); color: #fff; box-shadow: 0 4px 12px rgba(79, 70, 229, .3); }
.btn.primary:hover:not(:disabled) { background: var(--brand); }
.btn.ghost { background: transparent; color: var(--muted); border-color: var(--border); }
.btn.ghost:hover { background: var(--surface-2); color: var(--text); }
.btn.danger { background: var(--bad-soft); color: var(--bad); }
.btn.danger:hover:not(:disabled) { filter: brightness(.96); }
.btn.ok { background: var(--ok-soft); color: var(--ok); }
.btn.ok:hover:not(:disabled) { filter: brightness(.96); }
.btn.danger-solid { background: var(--bad); color: #fff; }
.btn.ok-solid { background: var(--ok); color: #fff; }
.spin { width: 14px; height: 14px; border-radius: 50%; border: 2px solid rgba(255, 255, 255, .4); border-top-color: #fff; animation: r .7s linear infinite; }
@keyframes r { to { transform: rotate(360deg); } }

/* empty */
.empty { text-align: center; padding: 70px 20px; color: var(--muted); }
.empty h3 { color: var(--text); margin: 14px 0 4px; font-size: 15px; }
.empty p { margin: 0; }

/* stats */
.stats { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
@media (max-width: 720px) { .stats { grid-template-columns: repeat(2, 1fr); } }
.stat { background: var(--surface-2); border: 1px solid var(--border); border-radius: 11px; padding: 11px 13px; display: grid; }
.stat span { font-size: 11.5px; color: var(--muted); text-transform: uppercase; letter-spacing: .04em; font-weight: 500; }
.stat b { font-size: 22px; letter-spacing: -.02em; line-height: 1.2; }
.stat em { font-style: normal; font-size: 11.5px; color: var(--muted); }
.stat.ok b { color: var(--ok); }
.stat.bad b { color: var(--bad); }

.bar { display: flex; height: 8px; border-radius: 99px; overflow: hidden; background: var(--neutral-soft); margin: 14px 0 18px; }
.bar i { display: block; transition: width .4s ease; }
.s-ok { background: var(--ok); } .s-bad { background: var(--bad); } .s-na { background: var(--neutral); opacity: .5; }

/* toolbar */
.toolbar { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin-bottom: 12px; }
.seg { display: inline-flex; padding: 3px; background: var(--neutral-soft); border-radius: 10px; }
.seg button { border: 0; background: transparent; padding: 6px 14px; border-radius: 8px; color: var(--muted); font-weight: 500; font-size: 13px; }
.seg button.on { background: var(--surface); color: var(--text); box-shadow: 0 1px 3px rgba(15, 23, 42, .12); }
.search { padding: 8px 12px; border-radius: 10px; border: 1px solid var(--border); background: var(--surface-2); color: var(--text); font: inherit; min-width: 210px; outline: none; }
.search:focus { border-color: var(--brand); box-shadow: 0 0 0 3px var(--brand-soft); }

/* table */
.table-wrap { max-height: 400px; overflow: auto; border: 1px solid var(--border); border-radius: 11px; }
table { width: 100%; border-collapse: collapse; }
th { position: sticky; top: 0; background: var(--surface-2); text-align: left; padding: 10px 14px; font-size: 11.5px; text-transform: uppercase;
  letter-spacing: .05em; color: var(--muted); font-weight: 600; border-bottom: 1px solid var(--border); }
td { padding: 9px 14px; border-bottom: 1px solid var(--border); }
tbody tr:last-child td { border-bottom: 0; }
tbody tr:hover { background: var(--surface-2); }
tr.na td { color: var(--muted); }
tr.sel { background: var(--brand-soft); }
tr.sel:hover { background: var(--brand-soft); }
.chk { width: 44px; padding-right: 0; }
input[type='checkbox'] { width: 16px; height: 16px; accent-color: var(--brand-600); cursor: pointer; vertical-align: middle; }
input[type='checkbox']:disabled { cursor: not-allowed; opacity: .35; }
.mono { font-family: var(--mono); font-size: 13px; }
.none { text-align: center; color: var(--muted); padding: 28px; }

.pill { display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; }
.pill i { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }
.pill.enabled { background: var(--ok-soft); color: var(--ok); }
.pill.disabled { background: var(--bad-soft); color: var(--bad); }
.pill.na { background: var(--neutral-soft); color: var(--muted); font-weight: 500; }

/* action bar */
.actions { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--border); color: var(--muted); }
.actions b { color: var(--text); }

/* modal + toast */
.overlay { position: fixed; inset: 0; background: rgba(8, 12, 28, .55); backdrop-filter: blur(3px); display: grid; place-items: center; z-index: 50; padding: 20px; }
.modal { background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 26px; width: 100%; max-width: 400px; box-shadow: 0 24px 60px rgba(0, 0, 0, .35); }
.modal-ico { width: 44px; height: 44px; border-radius: 12px; display: grid; place-items: center; margin-bottom: 14px; }
.modal-ico.disabled { background: var(--bad-soft); color: var(--bad); }
.modal-ico.enabled { background: var(--ok-soft); color: var(--ok); }
.modal h3 { margin: 0 0 6px; font-size: 17px; }
.modal p { margin: 0; color: var(--muted); }
.toast { position: fixed; bottom: 24px; left: 50%; transform: translateX(-50%); padding: 11px 18px; border-radius: 11px; color: #fff; font-weight: 500; z-index: 60;
  box-shadow: 0 10px 30px rgba(0, 0, 0, .3); }
.toast.ok { background: var(--ok); } .toast.bad { background: var(--bad); }
.toast-enter-active, .toast-leave-active { transition: all .25s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, 12px); }
</style>
