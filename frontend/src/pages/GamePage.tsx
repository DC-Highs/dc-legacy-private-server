import type { FC } from "react"
import { Link as RouterLink } from "react-router-dom"

import { GamePlayer } from "@/components/game/GamePlayer"
import { useLayout } from "@/components/layout/AppLayout"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Typography } from "@/components/ui/typography"
import { useAuth } from "@/lib/auth"

export const GamePage: FC = () => {
  const { user, loading } = useAuth()
  const { flashSaved } = useLayout()

  if (loading) {
    return (
      <div className="p-8">
        <Skeleton className="h-8 w-48" />
      </div>
    )
  }

  if (!user) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-4 p-6 text-center">
        <Typography.H2>Welcome back, dragon master</Typography.H2>
        <Typography.Muted>Log in or create an account to play Dragon City.</Typography.Muted>
        <div className="flex gap-2">
          <Button render={<RouterLink to="/login" />}>Log in</Button>
          <Button variant="outline" render={<RouterLink to="/register" />}>
            Sign up
          </Button>
        </div>
      </div>
    )
  }

  return <GamePlayer onSaved={flashSaved} />
}
