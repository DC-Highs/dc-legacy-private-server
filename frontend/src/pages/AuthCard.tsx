import type { FC, ReactNode } from "react"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

type AuthCardProps = { title: string; description: string; children: ReactNode; footer: ReactNode }

export const AuthCard: FC<AuthCardProps> = ({ title, description, children, footer }) => (
  <div className="flex h-full items-center justify-center overflow-y-auto p-4">
    <Card className="w-full max-w-sm">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {children}
        {footer}
      </CardContent>
    </Card>
  </div>
)
