export const DEFAULT_IPS = [
  '10.10.1.11', '10.10.1.12', '10.10.1.13', '10.10.1.14',
  '10.10.2.21', '10.10.2.22', '10.10.2.23', '10.10.2.24',
  '10.10.3.31', '10.10.3.32', '10.10.3.33', '10.10.3.34',
  '10.20.1.41', '10.20.1.42', '10.20.1.43', '10.20.1.44',
  '10.20.2.51', '10.20.2.52', '10.20.2.53', '10.20.2.54',
  '10.30.1.61', '10.30.1.62', '10.30.1.63', '10.30.1.64',
  '10.99.9.1', '10.99.9.2', '10.99.9.3', '192.168.50.7', '172.16.8.20', '10.99.9.6',
].join('\n')

async function post(path, body) {
  const res = await fetch(`/api/${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new Error(`${path}: HTTP ${res.status}`)
  return res.json()
}

export async function check(text) {
  return (await post('check', { text })).rows
}

export const setStatus = (ips, status) =>
  post(status === 'disabled' ? 'disable' : 'enable', { ips })
