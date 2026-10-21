import { zodResolver } from "@hookform/resolvers/zod"
import { useEffect, useState } from "react"
import type { FC } from "react"
import { Controller, useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"
import { Typography } from "@/components/ui/typography"
import { api } from "@/lib/api"
import type { User } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import { applyServerErrors } from "@/lib/forms"
import { FriendsSection } from "@/pages/admin/FriendsSection"

const passwordSchema = z.object({
  password: z.string().min(8, "Use at least 8 characters").max(128, "Use at most 128 characters"),
})

type PasswordFormValues = z.infer<typeof passwordSchema>

const amount = z.string().regex(/^\d{1,10}$/, "Enter a whole number (0 or more)")

const resourcesSchema = z.object({ gold: amount, cash: amount, food: amount })

type ResourcesFormValues = z.infer<typeof resourcesSchema>

type ManageUserDialogProps = {
  user: User | null
  onClose: () => void
  onChanged: (user: User) => void
  onDeleted: () => void
}

type Confirmation = "reset" | "delete" | null

const errorMessage = (error: unknown) => (error instanceof Error ? error.message : "Something went wrong")

export const ManageUserDialog: FC<ManageUserDialogProps> = ({ user, onClose, onChanged, onDeleted }) => {
  const { user: me } = useAuth()
  const [confirm, setConfirm] = useState<Confirmation>(null)
  const isSelf = user !== null && me?.id === user.id

  const passwordForm = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { password: "" },
  })
  const resourcesForm = useForm<ResourcesFormValues>({
    resolver: zodResolver(resourcesSchema),
    defaultValues: { gold: "0", cash: "0", food: "0" },
  })

  useEffect(() => {
    setConfirm(null)
    passwordForm.reset({ password: "" })
    resourcesForm.reset({
      gold: String(user?.player?.gold ?? 0),
      cash: String(user?.player?.cash ?? 0),
      food: String(user?.player?.food ?? 0),
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id, user?.player?.gold, user?.player?.cash, user?.player?.food])

  if (!user) return <Dialog open={false} />

  const update = async (changes: Record<string, unknown>, success: string) => {
    try {
      const data = await api.patch<{ user: User }>(`/api/admin/users/${user.id}`, changes)
      toast.success(success)
      onChanged(data.user)
    } catch (error) {
      toast.error(errorMessage(error))
    }
  }

  const submitPassword = passwordForm.handleSubmit(async (values) => {
    try {
      const data = await api.patch<{ user: User }>(`/api/admin/users/${user.id}`, values)
      toast.success("Password changed, the user was logged out")
      passwordForm.reset({ password: "" })
      onChanged(data.user)
    } catch (error) {
      const message = applyServerErrors(error, passwordForm.setError, ["password"])
      if (message) passwordForm.setError("root", { message })
    }
  })

  const submitResources = resourcesForm.handleSubmit(async (values) => {
    try {
      const body = { gold: Number(values.gold), cash: Number(values.cash), food: Number(values.food) }
      const data = await api.patch<{ user: User }>(`/api/admin/users/${user.id}/resources`, body)
      toast.success("Resources updated")
      onChanged(data.user)
    } catch (error) {
      toast.error(errorMessage(error))
    }
  })

  const resetSave = async () => {
    try {
      const data = await api.post<{ user: User }>(`/api/admin/users/${user.id}/reset-player`)
      toast.success("Game save reset")
      setConfirm(null)
      onChanged(data.user)
    } catch (error) {
      toast.error(errorMessage(error))
    }
  }

  const deleteUser = async () => {
    try {
      await api.delete(`/api/admin/users/${user.id}`)
      toast.success(`Deleted ${user.email}`)
      onDeleted()
    } catch (error) {
      toast.error(errorMessage(error))
    }
  }

  return (
    <Dialog open onOpenChange={(open) => (open ? undefined : onClose())}>
      <DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{user.email}</DialogTitle>
          <DialogDescription>
            Account {user.id} · created {new Date(user.createdAt ?? "").toLocaleDateString()}
          </DialogDescription>
        </DialogHeader>

        <FieldGroup>
          <Field orientation="horizontal">
            <Switch
              id="manage-active"
              checked={user.isActive}
              disabled={isSelf}
              onCheckedChange={(checked) =>
                update({ isActive: checked }, checked ? "Account enabled" : "Account disabled and logged out")
              }
            />
            <FieldLabel htmlFor="manage-active">Active</FieldLabel>
          </Field>
          <Field orientation="horizontal">
            <Switch
              id="manage-admin"
              checked={user.isAdmin}
              disabled={isSelf}
              onCheckedChange={(checked) => update({ isAdmin: checked }, checked ? "Promoted to admin" : "Admin removed")}
            />
            <FieldLabel htmlFor="manage-admin">Administrator</FieldLabel>
          </Field>
          {isSelf ? <FieldDescription>You cannot disable or demote your own account.</FieldDescription> : null}
        </FieldGroup>

        <Separator />

        <form onSubmit={submitPassword} noValidate>
          <FieldGroup>
            <Controller
              name="password"
              control={passwordForm.control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="manage-password">New password</FieldLabel>
                  <Input
                    {...field}
                    id="manage-password"
                    type="password"
                    autoComplete="new-password"
                    aria-invalid={fieldState.invalid}
                  />
                  {fieldState.invalid ? <FieldError errors={[fieldState.error]} /> : null}
                </Field>
              )}
            />
            {passwordForm.formState.errors.root ? (
              <FieldError errors={[passwordForm.formState.errors.root]} />
            ) : null}
            <Button type="submit" variant="outline" disabled={passwordForm.formState.isSubmitting}>
              Change password
            </Button>
          </FieldGroup>
        </form>

        <Separator />

        <form onSubmit={submitResources} noValidate>
          <FieldGroup>
            <Typography.Small>Resources</Typography.Small>
            <div className="grid grid-cols-3 gap-2">
              {(["gold", "cash", "food"] as const).map((name) => (
                <Controller
                  key={name}
                  name={name}
                  control={resourcesForm.control}
                  render={({ field, fieldState }) => (
                    <Field data-invalid={fieldState.invalid}>
                      <FieldLabel htmlFor={`manage-${name}`}>{name === "cash" ? "Gems" : name}</FieldLabel>
                      <Input {...field} id={`manage-${name}`} inputMode="numeric" aria-invalid={fieldState.invalid} />
                      {fieldState.invalid ? <FieldError errors={[fieldState.error]} /> : null}
                    </Field>
                  )}
                />
              ))}
            </div>
            <Button type="submit" variant="outline" disabled={resourcesForm.formState.isSubmitting}>
              Save resources
            </Button>
          </FieldGroup>
        </form>

        <Separator />

        <FriendsSection userId={user.id} />

        <Separator />

        <div className="flex flex-col gap-2">
          <Typography.Small className="text-destructive">Danger zone</Typography.Small>
          {confirm === null ? (
            <div className="flex flex-wrap gap-2">
              <Button variant="outline" onClick={() => setConfirm("reset")}>
                Reset game save
              </Button>
              <Button variant="destructive" disabled={isSelf} onClick={() => setConfirm("delete")}>
                Delete user
              </Button>
            </div>
          ) : (
            <div className="flex flex-wrap items-center gap-2">
              <Typography.Muted>
                {confirm === "reset"
                  ? "This erases all progress of the player."
                  : "This deletes the account and its save."}
              </Typography.Muted>
              <Button variant="destructive" onClick={confirm === "reset" ? resetSave : deleteUser}>
                Confirm
              </Button>
              <Button variant="outline" onClick={() => setConfirm(null)}>
                Cancel
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
