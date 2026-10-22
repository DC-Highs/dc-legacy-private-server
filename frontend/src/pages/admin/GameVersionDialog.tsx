import { zodResolver } from "@hookform/resolvers/zod"
import { useEffect, useState } from "react"
import type { FC } from "react"
import { Controller, useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import { api } from "@/lib/api"
import type { GameVersions } from "@/lib/api"
import { applyServerErrors } from "@/lib/forms"

const gameVersionSchema = z.object({
  file: z.string().min(1, "Choose a version"),
})

type GameVersionFormValues = z.infer<typeof gameVersionSchema>

type GameVersionDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export const GameVersionDialog: FC<GameVersionDialogProps> = ({ open, onOpenChange }) => {
  const [data, setData] = useState<GameVersions | null>(null)
  const {
    control,
    handleSubmit,
    reset,
    setError,
    formState: { isSubmitting, errors },
  } = useForm<GameVersionFormValues>({
    resolver: zodResolver(gameVersionSchema),
    defaultValues: { file: "" },
  })

  useEffect(() => {
    if (!open) return
    let cancelled = false
    api
      .get<GameVersions>("/api/admin/game-version")
      .then((loaded) => {
        if (cancelled) return
        setData(loaded)
        reset({ file: loaded.selected })
      })
      .catch((error) => {
        if (cancelled) return
        toast.error(error instanceof Error ? error.message : "Could not load the game versions")
        onOpenChange(false)
      })
    return () => {
      cancelled = true
      setData(null)
    }
  }, [open, reset, onOpenChange])

  const onSubmit = handleSubmit(async (values) => {
    try {
      const saved = await api.put<GameVersions>("/api/admin/game-version", values)
      toast.success(`The game now loads ${saved.selected}. Players get it the next time they open the game.`)
      onOpenChange(false)
    } catch (error) {
      const message = applyServerErrors(error, setError, ["file"])
      if (message) setError("root", { message })
    }
  })

  const items = (data?.versions ?? []).map((item) => ({
    value: item.file,
    label: item.file === data?.default ? `${item.version} (default)` : item.version,
  }))

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Game version</DialogTitle>
          <DialogDescription>The Flash client every player loads. Taken from flash/versions.</DialogDescription>
        </DialogHeader>
        {data === null ? (
          <Skeleton className="h-9 w-full" />
        ) : (
          <form onSubmit={onSubmit} noValidate>
            <FieldGroup>
              <Controller
                name="file"
                control={control}
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="game-version">Version</FieldLabel>
                    <Select items={items} value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger id="game-version" className="w-full" aria-invalid={fieldState.invalid}>
                        <SelectValue placeholder="Choose a version" />
                      </SelectTrigger>
                      <SelectContent>
                        {items.map((item) => (
                          <SelectItem key={item.value} value={item.value}>
                            {item.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FieldDescription>Players already in the game keep their version until they reload.</FieldDescription>
                    {fieldState.invalid ? <FieldError errors={[fieldState.error]} /> : null}
                  </Field>
                )}
              />
              {errors.root ? <FieldError errors={[errors.root]} /> : null}
            </FieldGroup>
            <DialogFooter className="mt-4">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting || items.length === 0}>
                {isSubmitting ? "Saving..." : "Save"}
              </Button>
            </DialogFooter>
          </form>
        )}
      </DialogContent>
    </Dialog>
  )
}
