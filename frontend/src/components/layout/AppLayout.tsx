import { useCallback, useState } from "react"
import type { FC } from "react"
import { Outlet, useLocation, useOutletContext } from "react-router-dom"

import { AppHeader } from "@/components/layout/AppHeader"
import { PendingProvider } from "@/lib/pending"

type LayoutContext = { flashSaved: () => void }

export const useLayout = () => useOutletContext<LayoutContext>()

/** Header on top, the page fills the rest of the screen. */
export const AppLayout: FC = () => {
  const [saved, setSaved] = useState(false)
  const location = useLocation()
  const isMainPage = location.pathname === "/"

  const flashSaved = useCallback(() => {
    setSaved(true)
    window.setTimeout(() => setSaved(false), 2000)
  }, [])

  return (
    <PendingProvider>
      <div className="flex h-dvh flex-col bg-background text-foreground">
        <AppHeader saved={saved} />
        <main className={`min-h-0 flex-1 ${isMainPage ? "overflow-hidden" : "overflow-auto"}`}>
          <Outlet context={{ flashSaved } satisfies LayoutContext} />
        </main>
      </div>
    </PendingProvider>
  )
}
