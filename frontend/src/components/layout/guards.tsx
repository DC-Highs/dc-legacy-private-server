import type { FC } from "react"
import { Navigate, Outlet } from "react-router-dom"

import { Skeleton } from "@/components/ui/skeleton"
import { useAuth } from "@/lib/auth"

const Loading: FC = () => (
  <div className="p-8">
    <Skeleton className="h-8 w-48" />
  </div>
)

export const RequireUser: FC = () => {
  const { user, loading } = useAuth()
  if (loading) return <Loading />
  if (!user) return <Navigate to="/login" replace />
  return <Outlet />
}

export const RequireAdmin: FC = () => {
  const { user, loading } = useAuth()
  if (loading) return <Loading />
  if (!user) return <Navigate to="/login" replace />
  if (!user.isAdmin) return <Navigate to="/" replace />
  return <Outlet />
}

export const GuestOnly: FC = () => {
  const { user, loading } = useAuth()
  if (loading) return <Loading />
  if (user) return <Navigate to="/" replace />
  return <Outlet />
}
