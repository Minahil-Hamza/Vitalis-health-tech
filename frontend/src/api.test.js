import { describe, it, expect, vi, afterEach } from 'vitest'
import { api, ApiError } from './api'

describe('api client', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('sends Accept: application/json and returns parsed JSON on success', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      headers: { get: () => 'application/json' },
      json: async () => ({ hello: 'world' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const result = await api.get('/auth/me')

    expect(result).toEqual({ hello: 'world' })
    const [path, options] = fetchMock.mock.calls[0]
    expect(path).toBe('/auth/me')
    expect(options.headers.Accept).toBe('application/json')
    expect(options.credentials).toBe('same-origin')
  })

  it('sends a JSON body and Content-Type for POST', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      headers: { get: () => 'application/json' },
      json: async () => ({ id: '1' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await api.post('/auth/login', { email: 'a@b.com', password: 'x' })

    const [, options] = fetchMock.mock.calls[0]
    expect(options.method).toBe('POST')
    expect(options.headers['Content-Type']).toBe('application/json')
    expect(JSON.parse(options.body)).toEqual({ email: 'a@b.com', password: 'x' })
  })

  it('throws an ApiError with the response detail on failure', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      headers: { get: () => 'application/json' },
      json: async () => ({ detail: 'Invalid email or password' }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(api.get('/auth/me')).rejects.toMatchObject({
      status: 401,
      detail: 'Invalid email or password',
    })
    await expect(api.get('/auth/me')).rejects.toBeInstanceOf(ApiError)
  })
})
