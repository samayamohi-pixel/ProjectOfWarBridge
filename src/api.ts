let csrfToken: string | null = null

async function ensureCsrf() {
  if (!csrfToken) {
    const response = await fetch('/api/csrf', { credentials: 'same-origin' })
    if (!response.ok) throw new Error('Could not initialize the API session')
    const data = await response.json() as { csrfToken: string }
    csrfToken = data.csrfToken
  }
  return csrfToken
}

async function readResponse(response: Response) {
  const data = await response.json().catch(() => ({ error: 'Unexpected server response' }))
  if (!response.ok) throw new Error(data.error || 'Request failed')
  return data
}

export const api = {
  async get<T>(path: string): Promise<T> {
    const response = await fetch(path, { credentials: 'same-origin' })
    return readResponse(response) as Promise<T>
  },
  async post<T = unknown>(path: string, body: Record<string, unknown> = {}): Promise<T> {
    const token = await ensureCsrf()
    const response = await fetch(path, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': token },
      body: JSON.stringify(body),
    })
    return readResponse(response) as Promise<T>
  },
  async resetCsrf() {
    csrfToken = null
    await ensureCsrf()
  },
  setCsrfToken(token: string) {
    csrfToken = token
  },
}
