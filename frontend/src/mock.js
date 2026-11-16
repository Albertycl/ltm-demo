// Mock API for the layout phase. Swapped for real Flask calls in step C.
const nodes = [
  ['10.10.1.11', 'web-node-01', 'Prod'], ['10.10.1.12', 'web-node-02', 'Prod'],
  ['10.10.1.13', 'web-node-03', 'Prod'], ['10.10.1.14', 'web-node-04', 'Prod'],
  ['10.10.2.21', 'app-node-01', 'Prod'], ['10.10.2.22', 'app-node-02', 'Prod'],
  ['10.10.2.23', 'app-node-03', 'Prod'], ['10.10.2.24', 'app-node-04', 'Prod'],
  ['10.10.3.31', 'api-node-01', 'Prod'], ['10.10.3.32', 'api-node-02', 'Prod'],
  ['10.10.3.33', 'api-node-03', 'Prod'], ['10.10.3.34', 'api-node-04', 'Prod'],
  ['10.20.1.41', 'db-proxy-01', 'Common'], ['10.20.1.42', 'db-proxy-02', 'Common'],
  ['10.20.1.43', 'cache-node-01', 'Common'], ['10.20.1.44', 'cache-node-02', 'Common'],
  ['10.20.2.51', 'auth-node-01', 'Common'], ['10.20.2.52', 'auth-node-02', 'Common'],
  ['10.20.2.53', 'pay-node-01', 'Common'], ['10.20.2.54', 'pay-node-02', 'Common'],
  ['10.30.1.61', 'uat-web-01', 'UAT'], ['10.30.1.62', 'uat-web-02', 'UAT'],
  ['10.30.1.63', 'uat-app-01', 'UAT'], ['10.30.1.64', 'uat-app-02', 'UAT'],
]
const db = new Map(nodes.map(([ip, name, partition], i) => [
  ip, { ip, name, partition, status: i % 6 === 5 ? 'disabled' : 'enabled' },
]))

export const DEFAULT_IPS = [
  ...nodes.map(n => n[0]),
  '10.99.9.1', '10.99.9.2', '10.99.9.3', '192.168.50.7', '172.16.8.20', '10.99.9.6',
].sort(() => 0) // keep order; unknown IPs appended at the end
  .join('\n')

const delay = (ms = 400) => new Promise(r => setTimeout(r, ms))
const parse = text => [...new Set(text.split(/[\s,;]+/).map(s => s.trim()).filter(Boolean))]

export async function check(text) {
  await delay()
  return parse(text).map(ip => db.get(ip) ? { ...db.get(ip), in_ltm: true } : { ip, in_ltm: false })
}

export async function setStatus(ips, status) {
  await delay()
  ips.forEach(ip => db.has(ip) && (db.get(ip).status = status))
}
