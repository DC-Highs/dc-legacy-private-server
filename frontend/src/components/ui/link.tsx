import type { ComponentProps, FC } from "react"
import { Link as RouterLink } from "react-router-dom"

import { cn } from "@/lib/utils"

type LinkProps = Omit<ComponentProps<"a">, "href"> & { href: string }

const EXTERNAL = /^(https?:)?\/\//

/** Internal paths use the router; external URLs open in a new tab safely. */
export const Link: FC<LinkProps> = ({ href, className, children, ...props }) => {
  const classes = cn("font-medium text-primary underline-offset-4 hover:underline", className)

  if (EXTERNAL.test(href)) {
    return (
      <a href={href} target="_blank" rel="noopener noreferrer" className={classes} {...props}>
        {children}
      </a>
    )
  }

  return (
    <RouterLink to={href} className={classes} {...props}>
      {children}
    </RouterLink>
  )
}
