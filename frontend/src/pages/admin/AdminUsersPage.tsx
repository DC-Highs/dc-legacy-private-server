import { PlusIcon, SearchIcon } from "lucide-react"
import { useCallback, useEffect, useState } from "react"
import type { FC } from "react"
import { toast } from "sonner"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Typography } from "@/components/ui/typography"
import { api } from "@/lib/api"
import type { User, UsersPage } from "@/lib/api"
import { CreateUserDialog } from "@/pages/admin/CreateUserDialog"
import { ManageUserDialog } from "@/pages/admin/ManageUserDialog"

const PAGE_SIZE = 15
const SEARCH_DELAY_MS = 300

const formatNumber = (value: number | undefined) => (value === undefined ? "-" : value.toLocaleString())
const formatDate = (value: string | null) => (value ? new Date(value).toLocaleString() : "Never")

export const AdminUsersPage: FC = () => {
  const [search, setSearch] = useState("")
  const [query, setQuery] = useState("")
  const [page, setPage] = useState(1)
  const [data, setData] = useState<UsersPage | null>(null)
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [managed, setManaged] = useState<User | null>(null)

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setQuery(search.trim())
      setPage(1)
    }, SEARCH_DELAY_MS)
    return () => window.clearTimeout(timer)
  }, [search])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({ page: String(page), pageSize: String(PAGE_SIZE) })
      if (query) params.set("query", query)
      setData(await api.get<UsersPage>(`/api/admin/users?${params}`))
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not load the users")
    } finally {
      setLoading(false)
    }
  }, [page, query])

  useEffect(() => {
    void load()
  }, [load])

  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.pageSize)) : 1

  return (
    <div className="mx-auto flex h-full w-full max-w-6xl flex-col gap-4 overflow-y-auto p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <Typography.H2>Users</Typography.H2>
          <Typography.Muted>{data ? `${data.total} accounts` : "Loading..."}</Typography.Muted>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <SearchIcon className="pointer-events-none absolute top-2.5 left-2.5 size-4 text-muted-foreground" />
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search by email or id"
              className="w-64 pl-8"
              aria-label="Search users"
            />
          </div>
          <Button onClick={() => setCreateOpen(true)}>
            <PlusIcon /> New user
          </Button>
        </div>
      </div>

      <div className="rounded-lg border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Email</TableHead>
              <TableHead>Player</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Level</TableHead>
              <TableHead className="text-right">Gold</TableHead>
              <TableHead className="text-right">Gems</TableHead>
              <TableHead>Last login</TableHead>
              <TableHead />
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading && !data
              ? Array.from({ length: 5 }, (_, index) => (
                  <TableRow key={index}>
                    <TableCell colSpan={8}>
                      <Skeleton className="h-5 w-full" />
                    </TableCell>
                  </TableRow>
                ))
              : null}
            {data?.items.map((user) => (
              <TableRow key={user.id}>
                <TableCell>
                  <div className="font-medium">{user.email}</div>
                  <Typography.Muted>id {user.id}</Typography.Muted>
                </TableCell>
                <TableCell>{user.player?.name ?? "-"}</TableCell>
                <TableCell className="space-x-1">
                  <Badge variant={user.isActive ? "secondary" : "destructive"}>
                    {user.isActive ? "Active" : "Disabled"}
                  </Badge>
                  {user.isAdmin ? <Badge>Admin</Badge> : null}
                </TableCell>
                <TableCell className="text-right">{formatNumber(user.player?.level)}</TableCell>
                <TableCell className="text-right">{formatNumber(user.player?.gold)}</TableCell>
                <TableCell className="text-right">{formatNumber(user.player?.cash)}</TableCell>
                <TableCell>{formatDate(user.lastLoginAt)}</TableCell>
                <TableCell className="text-right">
                  <Button variant="outline" size="sm" onClick={() => setManaged(user)}>
                    Manage
                  </Button>
                </TableCell>
              </TableRow>
            ))}
            {data && data.items.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="py-8 text-center text-muted-foreground">
                  No users found.
                </TableCell>
              </TableRow>
            ) : null}
          </TableBody>
        </Table>
      </div>

      <div className="flex items-center justify-end gap-2">
        <Typography.Muted>
          Page {page} of {totalPages}
        </Typography.Muted>
        <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((value) => value - 1)}>
          Previous
        </Button>
        <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((value) => value + 1)}>
          Next
        </Button>
      </div>

      <CreateUserDialog open={createOpen} onOpenChange={setCreateOpen} onCreated={load} />
      <ManageUserDialog
        user={managed}
        onClose={() => setManaged(null)}
        onChanged={(user) => {
          setManaged(user)
          void load()
        }}
        onDeleted={() => {
          setManaged(null)
          void load()
        }}
      />
    </div>
  )
}
