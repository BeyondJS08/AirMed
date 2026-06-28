const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface ApiFetchOptions extends RequestInit {
  auth?: boolean
}

export async function apiFetch<T = unknown>(
  path: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const { auth = true, ...fetchOptions } = options

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(fetchOptions.headers as Record<string, string>),
  }

  if (auth) {
    const token = localStorage.getItem("accessToken")
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }
  }

  const url = `${API_BASE_URL}${path}`
  let response = await fetch(url, { ...fetchOptions, headers })

  if (response.status === 401 && auth) {
    const refreshToken = localStorage.getItem("refreshToken")
    if (refreshToken) {
      const refreshRes = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })
      if (refreshRes.ok) {
        const tokens = await refreshRes.json()
        localStorage.setItem("accessToken", tokens.access_token)
        localStorage.setItem("refreshToken", tokens.refresh_token)
        headers["Authorization"] = `Bearer ${tokens.access_token}`
        response = await fetch(url, { ...fetchOptions, headers })
      } else {
        localStorage.removeItem("accessToken")
        localStorage.removeItem("refreshToken")
        if (typeof window !== "undefined") {
          window.location.href = "/login"
        }
      }
    }
  }

  if (!response.ok) {
    const body = await response.text()
    throw new Error(body || `API error: ${response.status}`)
  }

  if (response.status === 204) return undefined as T
  return response.json()
}
