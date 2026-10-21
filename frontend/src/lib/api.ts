export type FieldErrors = Record<string, string>

export class ApiError extends Error {
  status: number
  code: string
  fields: FieldErrors

  constructor(status: number, code: string, message: string, fields: FieldErrors = {}) {
    super(message)
    this.status = status
    this.code = code
    this.fields = fields
  }
}

type Method = "GET" | "POST" | "PATCH" | "DELETE"

const request = async <T>(method: Method, path: string, body?: unknown): Promise<T> => {
  const response = await fetch(path, {
    method,
    credentials: "same-origin",
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  })

  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    const error = payload?.error
    throw new ApiError(
      response.status,
      error?.code ?? "error",
      error?.message ?? `Request failed (${response.status})`,
      error?.fields ?? {},
    )
  }

  return payload as T
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body ?? {}),
  patch: <T>(path: string, body: unknown) => request<T>("PATCH", path, body),
  delete: <T>(path: string) => request<T>("DELETE", path),
}

export type PlayerSummary = {
  name: string
  level: number
  gold: number
  cash: number
  food: number
  xp: number
  dragons: number
}

export type User = {
  id: number
  email: string
  isAdmin: boolean
  isActive: boolean
  createdAt: string | null
  lastLoginAt: string | null
  playerName?: string
  player?: PlayerSummary
}

export type UsersPage = {
  items: User[]
  total: number
  page: number
  pageSize: number
}

export type Bootstrap = {
  playerId: string
  playerName: string
  loader: string
  servicesPath: string
  flashVars: Record<string, string | boolean>
  legacyHosts: string[]
}

export type Friend = {
  id: number
  email: string
  playerName: string
}

export type FriendProfile = {
  id: number
  playerName: string
  level: number
}

export type FriendsOverview = {
  playerId: number
  friends: FriendProfile[]
  incoming: { requestId: number; createdAt: string; from: FriendProfile }[]
  outgoing: { requestId: number; createdAt: string; to: FriendProfile }[]
  limits: { maxFriends: number; rewardGems: number; rewardLimit: number }
}
