import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"
import type { FC, ReactNode } from "react"

import { ApiError, api } from "@/lib/api"
import type { User } from "@/lib/api"

type AuthContextValue = {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, confirmPassword: string) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

type AuthProviderProps = { children: ReactNode }

export const AuthProvider: FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get<{ user: User }>("/api/auth/me")
      .then((data) => setUser(data.user))
      .catch((error: unknown) => {
        if (!(error instanceof ApiError) || error.status !== 401) console.error(error)
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const data = await api.post<{ user: User }>("/api/auth/login", { email, password })
    setUser(data.user)
  }, [])

  const register = useCallback(async (email: string, password: string, confirmPassword: string) => {
    const data = await api.post<{ user: User }>("/api/auth/register", { email, password, confirmPassword })
    setUser(data.user)
  }, [])

  const logout = useCallback(async () => {
    await api.post("/api/auth/logout")
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext)
  if (!context) throw new Error("useAuth must be used inside AuthProvider")
  return context
}
