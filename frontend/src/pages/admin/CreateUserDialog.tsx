import { zodResolver } from "@hookform/resolvers/zod"
import type { FC } from "react"
import { Controller, useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { api } from "@/lib/api"
import { applyServerErrors } from "@/lib/forms"

const createUserSchema = z.object({
  email: z.email("Enter a valid email"),
  password: z.string().min(8, "Use at least 8 characters").max(128, "Use at most 128 characters"),
  isAdmin: z.boolean(),
})

type CreateUserFormValues = z.infer<typeof createUserSchema>

type CreateUserDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  onCreated: () => void
}

export const CreateUserDialog: FC<CreateUserDialogProps> = ({ open, onOpenChange, onCreated }) => {
  const {
    control,
    handleSubmit,
    reset,
    setError,
    formState: { isSubmitting, errors },
  } = useForm<CreateUserFormValues>({
    resolver: zodResolver(createUserSchema),
    defaultValues: { email: "", password: "", isAdmin: false },
  })

  const handleOpenChange = (next: boolean) => {
    if (!next) reset()
    onOpenChange(next)
  }

  const onSubmit = handleSubmit(async (values) => {
    try {
      await api.post("/api/admin/users", values)
      toast.success(`Created ${values.email}`)
      handleOpenChange(false)
      onCreated()
    } catch (error) {
      const message = applyServerErrors(error, setError, ["email", "password", "isAdmin"])
      if (message) setError("root", { message })
    }
  })

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New user</DialogTitle>
          <DialogDescription>Creates the account and a fresh game save.</DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} noValidate>
          <FieldGroup>
            <Controller
              name="email"
              control={control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="create-email">Email</FieldLabel>
                  <Input {...field} id="create-email" type="email" aria-invalid={fieldState.invalid} />
                  {fieldState.invalid ? <FieldError errors={[fieldState.error]} /> : null}
                </Field>
              )}
            />
            <Controller
              name="password"
              control={control}
              render={({ field, fieldState }) => (
                <Field data-invalid={fieldState.invalid}>
                  <FieldLabel htmlFor="create-password">Password</FieldLabel>
                  <Input
                    {...field}
                    id="create-password"
                    type="password"
                    autoComplete="new-password"
                    aria-invalid={fieldState.invalid}
                  />
                  {fieldState.invalid ? <FieldError errors={[fieldState.error]} /> : null}
                </Field>
              )}
            />
            <Controller
              name="isAdmin"
              control={control}
              render={({ field }) => (
                <Field orientation="horizontal">
                  <Checkbox id="create-admin" checked={field.value} onCheckedChange={field.onChange} />
                  <FieldLabel htmlFor="create-admin">Administrator</FieldLabel>
                </Field>
              )}
            />
            {errors.root ? <FieldError errors={[errors.root]} /> : null}
          </FieldGroup>
          <DialogFooter className="mt-4">
            <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? "Creating..." : "Create user"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
