const TOKEN_KEY = 'resume_analyzer_token'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (token) => localStorage.setItem(TOKEN_KEY, token)
export const clearToken = () => localStorage.removeItem(TOKEN_KEY)

// Called when the API says our token is no longer valid, so the app can return to the login screen.
let onUnauthorized = () => {}
export const setUnauthorizedHandler = (handler) => {
  onUnauthorized = handler
}

// fetch wrapper that adds the bearer token and parses JSON. Throws Error(detail) on failure.
export async function apiFetch(path, options = {}, { auth = true } = {}) {
  const headers = new Headers(options.headers)
  const token = getToken()
  if (auth && token) headers.set('Authorization', `Bearer ${token}`)

  const res = await fetch(path, { ...options, headers })

  let data = null
  try {
    data = await res.json()
  } catch {
    // non-JSON body (e.g. a proxy error page)
  }

  if (!res.ok) {
    if (res.status === 401 && auth) onUnauthorized()
    if (res.status === 429) {
      const wait = res.headers.get('Retry-After')
      throw new Error(
        wait
          ? `Too many requests. Try again in about ${Math.ceil(wait / 60)} min.`
          : 'Too many requests. Try again later.',
      )
    }
    const detail = typeof data?.detail === 'string' ? data.detail : null
    throw new Error(detail || 'Something went wrong. Try again.')
  }

  return data
}
