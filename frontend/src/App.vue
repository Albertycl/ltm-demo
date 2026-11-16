<template>
  <q-layout view="hHh lpR fFf">
    <q-header elevated class="bg-primary">
      <q-toolbar>
        <q-icon name="dns" size="sm" class="q-mr-sm" />
        <q-toolbar-title>LTM Node Control <span class="text-caption">demo</span></q-toolbar-title>
        <q-badge color="orange" label="MOCK · no real LTM" />
      </q-toolbar>
    </q-header>

    <q-page-container>
      <q-page padding>
        <div class="row q-col-gutter-md">
          <!-- Left: input -->
          <div class="col-12 col-md-4">
            <q-card flat bordered>
              <q-card-section class="text-subtitle1">1. Node IPs</q-card-section>
              <q-card-section class="q-pt-none">
                <q-input v-model="ipText" type="textarea" outlined :input-style="{ height: '420px', fontFamily: 'monospace' }" />
                <div class="text-caption text-grey-7 q-mt-xs">{{ ipCount }} unique IPs</div>
              </q-card-section>
              <q-card-actions>
                <q-btn flat label="Reset" icon="restart_alt" @click="ipText = DEFAULT_IPS" />
                <q-space />
                <q-btn color="primary" label="Confirm" icon="check" :loading="loading" :disable="!ipCount" @click="onConfirm" />
              </q-card-actions>
            </q-card>
          </div>

          <!-- Right: result -->
          <div class="col-12 col-md-8">
            <q-card flat bordered>
              <q-card-section class="text-subtitle1">2. LTM status</q-card-section>

              <q-card-section v-if="!rows.length" class="text-center text-grey-6 q-py-xl">
                <q-icon name="fact_check" size="64px" />
                <div>Click <b>Confirm</b> to check which IPs belong to LTM.</div>
              </q-card-section>

              <template v-else>
                <q-card-section class="q-pt-none row q-gutter-sm items-center">
                  <q-chip>Total {{ rows.length }}</q-chip>
                  <q-chip color="blue-1" text-color="blue-9">In LTM {{ inLtm.length }}</q-chip>
                  <q-chip color="grey-3">Not in LTM {{ rows.length - inLtm.length }}</q-chip>
                  <q-chip color="green-1" text-color="green-9" icon="check_circle">Enabled {{ count('enabled') }}</q-chip>
                  <q-chip color="red-1" text-color="red-9" icon="block">Disabled {{ count('disabled') }}</q-chip>
                  <q-space />
                  <q-btn-toggle v-model="filter" dense no-caps toggle-color="primary" :options="filterOptions" />
                </q-card-section>

                <q-table flat dense :rows="shown" :columns="columns" row-key="ip" :pagination="{ rowsPerPage: 0 }" hide-bottom style="max-height: 460px">
                  <template #body="props">
                    <q-tr :props="props" :class="{ 'bg-grey-2 text-grey-6': !props.row.in_ltm }">
                      <q-td key="ip" :props="props" class="text-mono">{{ props.row.ip }}</q-td>
                      <q-td key="name" :props="props">{{ props.row.name || '—' }}</q-td>
                      <q-td key="partition" :props="props">{{ props.row.partition || '—' }}</q-td>
                      <q-td key="status" :props="props">
                        <q-badge v-if="!props.row.in_ltm" color="grey-5" label="Not in LTM" />
                        <q-badge v-else :color="props.row.status === 'enabled' ? 'positive' : 'negative'" :label="props.row.status" />
                      </q-td>
                    </q-tr>
                  </template>
                </q-table>

                <q-card-actions class="q-pa-md">
                  <q-btn color="negative" icon="block" :label="`Disable ${inLtm.length} nodes`" :loading="acting" @click="onAct('disabled')" />
                  <q-btn color="positive" icon="check_circle" :label="`Enable ${inLtm.length} nodes`" :loading="acting" @click="onAct('enabled')" />
                </q-card-actions>
              </template>
            </q-card>
          </div>
        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useQuasar } from 'quasar'
import { DEFAULT_IPS, check, setStatus } from './mock'

const $q = useQuasar()
const ipText = ref(DEFAULT_IPS)
const rows = ref([])
const loading = ref(false)
const acting = ref(false)
const filter = ref('all')

const columns = [
  { name: 'ip', label: 'IP', field: 'ip', align: 'left' },
  { name: 'name', label: 'Node name', field: 'name', align: 'left' },
  { name: 'partition', label: 'Partition', field: 'partition', align: 'left' },
  { name: 'status', label: 'Status', field: 'status', align: 'left' },
]
const filterOptions = [
  { label: 'All', value: 'all' },
  { label: 'In LTM', value: 'in' },
  { label: 'Not in LTM', value: 'out' },
]

const ipCount = computed(() => new Set(ipText.value.split(/[\s,;]+/).filter(Boolean)).size)
const inLtm = computed(() => rows.value.filter(r => r.in_ltm))
const shown = computed(() => rows.value.filter(r => filter.value === 'all' || (filter.value === 'in') === r.in_ltm))
const count = s => inLtm.value.filter(r => r.status === s).length

async function onConfirm() {
  loading.value = true
  try { rows.value = await check(ipText.value) } finally { loading.value = false }
}

function onAct(status) {
  const verb = status === 'disabled' ? 'Disable' : 'Enable'
  $q.dialog({ title: `${verb} nodes`, message: `${verb} ${inLtm.value.length} nodes in LTM?`, cancel: true })
    .onOk(async () => {
      acting.value = true
      try {
        await setStatus(inLtm.value.map(r => r.ip), status)
        rows.value = await check(ipText.value)
        $q.notify({ type: status === 'disabled' ? 'negative' : 'positive', message: `${inLtm.value.length} nodes ${status}` })
      } finally { acting.value = false }
    })
}
</script>

<style>
.text-mono { font-family: monospace; }
</style>
