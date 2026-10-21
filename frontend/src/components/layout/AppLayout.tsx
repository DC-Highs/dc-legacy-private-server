import { useCallback, useState } from "react"
import type { FC } from "react"
import { Outlet, useOutletContext } from "react-router-dom"

import { AppHeader } from "@/components/layout/AppHeader"
import { PendingProvider } from "@/lib/pending"

type LayoutContext = { flashSaved: () => void }

export const useLayout = () => useOutletContext<LayoutContext>()

/** Header on top, the page fills the rest of the screen. */
export const AppLayout: FC = () => {
  const [saved, setSaved] = useState(false)

  const flashSaved = useCallback(() => {
    setSaved(true)
    window.setTimeout(() => setSaved(false), 2000)
  }, [])

  return (
    <PendingProvider>
      <div className="flex h-full flex-col overflow-hidden bg-background text-foreground">
        <AppHeader saved={saved} />
        <main className="min-h-0 flex-1 overflow-hidden">
          <Outlet context={{ flashSaved } satisfies LayoutContext} />
        </main>
      </div>
    </PendingProvider>
  )
}
