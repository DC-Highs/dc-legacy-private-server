import { LogOutIcon, ShieldIcon, UsersIcon } from "lucide-react"
import type { FC } from "react"
import { Link as RouterLink, useNavigate } from "react-router-dom"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Typography } from "@/components/ui/typography"
import { useAuth } from "@/lib/auth"
import { usePending } from "@/lib/pending"

type AppHeaderProps = { saved?: boolean }

export const AppHeader: FC<AppHeaderProps> = ({ saved = false }) => {
  const { user, logout } = useAuth()
  const { incoming } = usePending()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate("/login")
  }

  return (
    <header className="flex h-12 shrink-0 items-center justify-between gap-3 border-b bg-card px-4">
      <RouterLink to="/" className="flex items-center gap-2">
        <Typography.Text className="text-lg">🐉</Typography.Text>
        <Typography.Large>Dragon City</Typography.Large>
      </RouterLink>

      <nav className="flex items-center gap-2">
        {saved ? <Typography.Small className="animate-pulse text-emerald-500">Saved</Typography.Small> : null}

        {user ? (
          <>
            <Typography.Muted className="hidden sm:block">{user.playerName || user.email}</Typography.Muted>
            <Button variant="ghost" size="sm" render={<RouterLink to="/friends" />}>
              <UsersIcon /> Friends
              {incoming > 0 ? <Badge variant="destructive">{incoming}</Badge> : null}
            </Button>
            {user.isAdmin ? (
              <Button variant="ghost" size="sm" render={<RouterLink to="/admin" />}>
                <ShieldIcon /> Admin
              </Button>
            ) : null}
            <Button variant="outline" size="sm" onClick={handleLogout}>
              <LogOutIcon /> Log out
            </Button>
          </>
        ) : (
          <>
            <Button variant="ghost" size="sm" render={<RouterLink to="/login" />}>
              Log in
            </Button>
            <Button size="sm" render={<RouterLink to="/register" />}>
              Sign up
            </Button>
          </>
        )}
      </nav>
    </header>
  )
}
