import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react"
import type { FC, ReactNode } from "react"

import { api } from "@/lib/api"
import { useAuth } from "@/lib/auth"

const POLL_MS = 60_000

type PendingContextValue = {
  /** Friend requests waiting for an answer. */
  incoming: number
  refresh: () => Promise<void>
}

const PendingContext = createContext<PendingContextValue | null>(null)

type PendingProviderProps = { children: ReactNode }

export const PendingProvider: FC<PendingProviderProps> = ({ children }) => {
  const { user } = useAuth()
  const [incoming, setIncoming] = useState(0)

  const refresh = useCallback(async () => {
    if (!user) {
      setIncoming(0)
      return
    }
    try {
      const data = await api.get<{ incoming: number }>("/api/friends/summary")
      setIncoming(data.incoming)
    } catch {
      // The badge is a convenience; a failed poll is not worth an error message.
    }
  }, [user])

  useEffect(() => {
    void refresh()
    if (!user) return
    const timer = window.setInterval(() => void refresh(), POLL_MS)
    return () => window.clearInterval(timer)
  }, [refresh, user])

  const value = useMemo(() => ({ incoming, refresh }), [incoming, refresh])

  return <PendingContext.Provider value={value}>{children}</PendingContext.Provider>
}

export const usePending = (): PendingContextValue => {
  const context = useContext(PendingContext)
  if (!context) throw new Error("usePending must be used inside PendingProvider")
  return context
}
