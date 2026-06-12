const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
let authHandlers = {
  getAccessToken: () => null,
  getRefreshToken: () => null,
  refreshAccessToken: async () => false
}

class ApiError extends Error {
  constructor(message, { status, data } = {}) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.data = data
  }
}

async function parseResponse(response) {
  if (response.status === 204) {
    return null
  }

  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return response.json()
  }

  return response.text()
}

function buildUrl(path) {
  if (/^https?:\/\//i.test(path)) {
    return path
  }

  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${API_BASE_URL}${normalizedPath}`
}

function getErrorMessage(data, fallback) {
  if (!data) {
    return fallback
  }

  if (typeof data === 'string') {
    return data || fallback
  }

  if (typeof data.detail === 'string') {
    return data.detail
  }

  if (typeof data.error === 'string') {
    return data.error
  }

  const firstField = Object.values(data)[0]
  if (Array.isArray(firstField) && firstField.length > 0) {
    return firstField.join(' ')
  }

  if (typeof firstField === 'string') {
    return firstField
  }

  return fallback
}

async function rawRequest(path, options = {}, accessToken = null) {
  const headers = new Headers(options.headers || {})
  const hasBody = options.body !== undefined && options.body !== null

  if (hasBody && !(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`)
  }

  const response = await fetch(buildUrl(path), {
    ...options,
    headers
  })
  const data = await parseResponse(response)

  if (!response.ok) {
    throw new ApiError(getErrorMessage(data, 'Ошибка запроса'), {
      status: response.status,
      data
    })
  }

  return data
}

async function rawBlobRequest(url, accessToken = null) {
  const headers = new Headers()
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`)
  }

  const response = await fetch(url, { headers })
  if (!response.ok) {
    throw new ApiError('Не удалось загрузить файл', { status: response.status })
  }

  return response.blob()
}

async function getBlob(url) {
  const accessToken = authHandlers.getAccessToken()

  try {
    return await rawBlobRequest(url, accessToken)
  } catch (error) {
    if (error.status !== 401 || !authHandlers.getRefreshToken()) {
      throw error
    }

    const refreshed = await authHandlers.refreshAccessToken()
    if (!refreshed) {
      throw error
    }

    return rawBlobRequest(url, authHandlers.getAccessToken())
  }
}

async function request(path, options = {}) {
  const accessToken = authHandlers.getAccessToken()

  try {
    return await rawRequest(path, options, accessToken)
  } catch (error) {
    if (error.status !== 401 || options.skipAuthRetry || !authHandlers.getRefreshToken()) {
      throw error
    }

    const refreshed = await authHandlers.refreshAccessToken()
    if (!refreshed) {
      throw error
    }

    return rawRequest(path, { ...options, skipAuthRetry: true }, authHandlers.getAccessToken())
  }
}

function configureApiAuth(handlers) {
  authHandlers = {
    ...authHandlers,
    ...handlers
  }
}

function jsonRequest(path, method, payload, options = {}) {
  return request(path, {
    ...options,
    method,
    body: payload === undefined ? undefined : JSON.stringify(payload)
  })
}

function formRequest(path, method, formData, options = {}) {
  return request(path, {
    ...options,
    method,
    body: formData
  })
}

export const api = {
  get: (path, options) => request(path, { ...options, method: 'GET' }),
  post: (path, payload, options) => jsonRequest(path, 'POST', payload, options),
  patch: (path, payload, options) => jsonRequest(path, 'PATCH', payload, options),
  postForm: (path, formData, options) => formRequest(path, 'POST', formData, options),
  patchForm: (path, formData, options) => formRequest(path, 'PATCH', formData, options),
  delete: (path, options) => request(path, { ...options, method: 'DELETE' }),
  rawRequest,
  getBlob
}

export { ApiError, configureApiAuth }
