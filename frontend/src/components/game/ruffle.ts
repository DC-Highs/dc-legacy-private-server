import type { Bootstrap } from "@/lib/api"

type RuffleInstance = {
  load: (options: Record<string, unknown>) => Promise<void>
  destroy?: () => void
}

export type RufflePlayerElement = HTMLElement & { ruffle: () => RuffleInstance }

type RuffleApi = {
  newest: () => { createPlayer: () => RufflePlayerElement } | null
}

declare global {
  interface Window {
    RufflePlayer?: RuffleApi & { config?: Record<string, unknown> }
  }
}

const SCRIPT_WAIT_MS = 20000

/** Ruffle is loaded with a script tag in index.html; wait until it is ready. */
export const waitForRuffle = (): Promise<RuffleApi> =>
  new Promise((resolve, reject) => {
    const started = Date.now()
    const check = () => {
      const api = window.RufflePlayer
      if (api && typeof api.newest === "function" && api.newest()) {
        resolve(api)
      } else if (Date.now() - started > SCRIPT_WAIT_MS) {
        reject(new Error("Ruffle did not load. Check your connection and reload the page."))
      } else {
        window.setTimeout(check, 100)
      }
    }
    check()
  })

const escapeRegExp = (text: string) => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")

/** The Flash client has the original servers hardcoded; send those requests to this server. */
const buildRewriteRules = (hosts: string[], origin: string): Array<[RegExp, string]> =>
  hosts.map((host) => [new RegExp(`^https?://${escapeRegExp(host)}/`, "i"), `${origin}/`])

export const buildLoadOptions = (bootstrap: Bootstrap, origin: string): Record<string, unknown> => {
  const parameters: Record<string, string> = {
    urlServicesBase: `${origin}${bootstrap.servicesPath}`,
  }
  for (const [key, value] of Object.entries(bootstrap.flashVars)) {
    parameters[key] = String(value)
  }

  return {
    url: `${origin}/${bootstrap.loader}`,
    base: `${origin}/`,
    parameters,
    allowScriptAccess: true,
    autoplay: "on",
    unmuteOverlay: "hidden",
    letterbox: "on",
    contextMenu: "off",
    urlRewriteRules: buildRewriteRules(bootstrap.legacyHosts, origin),
  }
}
