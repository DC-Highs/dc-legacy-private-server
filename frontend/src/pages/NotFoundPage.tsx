import type { FC } from "react"

import { Link } from "@/components/ui/link"
import { Typography } from "@/components/ui/typography"

export const NotFoundPage: FC = () => (
  <div className="flex h-full flex-col items-center justify-center gap-2 p-6 text-center">
    <Typography.H2>Page not found</Typography.H2>
    <Typography.Muted>
      <Link href="/">Back to the game</Link>
    </Typography.Muted>
  </div>
)
