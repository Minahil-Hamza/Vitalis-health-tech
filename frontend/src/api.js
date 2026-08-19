// Thin fetch wrapper for the Vitalis backend. Always sends Accept: application/json so
// the content-negotiated backend routes (see PROGRESS.md, Phase 7) return JSON instead
// of HTML, and always includes the auth cookie via credentials: 'same-origin'.

class ApiError extends Error {
  constructor(status, detail) {
    super(typeof detail === 'string' ? detail : 'Request failed')
    this.status = status
    this.detail = detail
  }
}

async function request(path, { method = 'GET', body } = {}) {
  const res = await fetch(path, {
    method,
    credentials: 'same-origin',
    headers: {
      Accept: 'application/json',
      ...(body ? { 'Content-Type': 'application/json' } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  })

  const isJson = (res.headers.get('content-type') || '').includes('application/json')
  const data = isJson ? await res.json().catch(() => null) : null

  if (!res.ok) {
    throw new ApiError(res.status, data ? data.detail : null)
  }
  return data
}

export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body }),
}

export { ApiError }
