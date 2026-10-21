import { useEffect, useRef, useState } from "react"
import type { FC } from "react"

import { buildLoadOptions, waitForRuffle } from "@/components/game/ruffle"
import type { RufflePlayerElement } from "@/components/game/ruffle"
import { Skeleton } from "@/components/ui/skeleton"
import { Typography } from "@/components/ui/typography"
import { api } from "@/lib/api"
import type { Bootstrap } from "@/lib/api"

type GamePlayerProps = { onSaved: () => void }

type Status = { kind: "loading" } | { kind: "ready" } | { kind: "error"; message: string }

export const GamePlayer: FC<GamePlayerProps> = ({ onSaved }) => {
  const container = useRef<HTMLDivElement>(null)
  const [status, setStatus] = useState<Status>({ kind: "loading" })

  useEffect(() => {
    let cancelled = false
    let player: RufflePlayerElement | null = null

    const start = async () => {
      try {
        const [bootstrap, ruffle] = await Promise.all([api.get<Bootstrap>("/api/game/bootstrap"), waitForRuffle()])
        if (cancelled || !container.current) return

        player = ruffle.newest()!.createPlayer()
        player.style.width = "100%"
        player.style.height = "100%"
        container.current.appendChild(player)

        await player.ruffle().load(buildLoadOptions(bootstrap, window.location.origin))
        if (!cancelled) setStatus({ kind: "ready" })
      } catch (error) {
        if (!cancelled) {
          setStatus({ kind: "error", message: error instanceof Error ? error.message : "Could not start the game." })
        }
      }
    }

    void start()

    return () => {
      cancelled = true
      player?.ruffle().destroy?.()
      player?.remove()
    }
  }, [])

  // The server announces every saved packet; the header shows a short "Saved" hint.
  useEffect(() => {
    const events = new EventSource("/stream")
    events.onmessage = (event) => {
      if (event.data === "JUEGO_GUARDADO") onSaved()
    }
    return () => events.close()
  }, [onSaved])

  return (
    <div className="relative h-full w-full bg-black">
      <div ref={container} className="h-full w-full" />
      {status.kind === "loading" ? (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-3">
          <Skeleton className="h-6 w-48" />
          <Typography.Muted>Loading the game...</Typography.Muted>
        </div>
      ) : null}
      {status.kind === "error" ? (
        <div className="absolute inset-0 flex items-center justify-center p-6 text-center">
          <Typography.P className="text-destructive">{status.message}</Typography.P>
        </div>
      ) : null}
    </div>
  )
}
