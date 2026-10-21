import type { ComponentProps, FC } from "react"

import { cn } from "@/lib/utils"

const H1: FC<ComponentProps<"h1">> = ({ className, ...props }) => (
  <h1 className={cn("scroll-m-20 text-3xl font-extrabold tracking-tight text-balance", className)} {...props} />
)

const H2: FC<ComponentProps<"h2">> = ({ className, ...props }) => (
  <h2 className={cn("scroll-m-20 text-2xl font-semibold tracking-tight", className)} {...props} />
)

const H3: FC<ComponentProps<"h3">> = ({ className, ...props }) => (
  <h3 className={cn("scroll-m-20 text-xl font-semibold tracking-tight", className)} {...props} />
)

const H4: FC<ComponentProps<"h4">> = ({ className, ...props }) => (
  <h4 className={cn("scroll-m-20 text-lg font-semibold tracking-tight", className)} {...props} />
)

const P: FC<ComponentProps<"p">> = ({ className, ...props }) => (
  <p className={cn("leading-7", className)} {...props} />
)

const Lead: FC<ComponentProps<"p">> = ({ className, ...props }) => (
  <p className={cn("text-lg text-muted-foreground", className)} {...props} />
)

const Large: FC<ComponentProps<"div">> = ({ className, ...props }) => (
  <div className={cn("text-lg font-semibold", className)} {...props} />
)

const Small: FC<ComponentProps<"small">> = ({ className, ...props }) => (
  <small className={cn("text-sm leading-none font-medium", className)} {...props} />
)

const Muted: FC<ComponentProps<"p">> = ({ className, ...props }) => (
  <p className={cn("text-sm text-muted-foreground", className)} {...props} />
)

const Code: FC<ComponentProps<"code">> = ({ className, ...props }) => (
  <code className={cn("relative rounded bg-muted px-[0.3rem] py-[0.2rem] font-mono text-sm", className)} {...props} />
)

const Text: FC<ComponentProps<"span">> = ({ className, ...props }) => <span className={className} {...props} />

export const Typography = { H1, H2, H3, H4, P, Lead, Large, Small, Muted, Code, Text }
