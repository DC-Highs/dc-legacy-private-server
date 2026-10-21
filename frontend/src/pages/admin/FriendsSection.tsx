import { zodResolver } from "@hookform/resolvers/zod"
import { useCallback, useEffect, useState } from "react"
import type { FC } from "react"
import { Controller, useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Typography } from "@/components/ui/typography"
import { api } from "@/lib/api"
import type { Friend } from "@/lib/api"
import { applyServerErrors } from "@/lib/forms"

const addFriendSchema = z.object({
  friendId: z.string().regex(/^\d{1,16}$/, "Enter a player id (digits only)"),
})

type AddFriendFormValues = z.infer<typeof addFriendSchema>

type FriendsSectionProps = { userId: number }

export const FriendsSection: FC<FriendsSectionProps> = ({ userId }) => {
  const [friends, setFriends] = useState<Friend[] | null>(null)
  const {
    control,
    handleSubmit,
    reset,
    setError,
    formState: { isSubmitting, errors },
  } = useForm<AddFriendFormValues>({
    resolver: zodResolver(addFriendSchema),
    defaultValues: { friendId: "" },
  })

  const load = useCallback(async () => {
    try {
      const data = await api.get<{ items: Friend[] }>(`/api/admin/users/${userId}/friends`)
      setFriends(data.items)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not load the friends")
    }
  }, [userId])

  useEffect(() => {
    setFriends(null)
    reset({ friendId: "" })
    void load()
  }, [load, reset])

  const onSubmit = handleSubmit(async (values) => {
    try {
      const data = await api.post<{ items: Friend[] }>(`/api/admin/users/${userId}/friends`, {
        friendId: Number(values.friendId),
      })
      setFriends(data.items)
      reset({ friendId: "" })
      toast.success("Friend added")
    } catch (error) {
      const message = applyServerErrors(error, setError, ["friendId"])
      if (message) setError("root", { message })
    }
  })

  const remove = async (friend: Friend) => {
    try {
      const data = await api.delete<{ items: Friend[] }>(`/api/admin/users/${userId}/friends/${friend.id}`)
      setFriends(data.items)
      toast.success(`${friend.email} is no longer a friend`)
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not remove the friend")
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <Typography.Small>Friends (neighbours in the game)</Typography.Small>

      {friends === null ? <Typography.Muted>Loading...</Typography.Muted> : null}
      {friends?.length === 0 ? <Typography.Muted>No friends yet.</Typography.Muted> : null}
      {friends?.map((friend) => (
        <div key={friend.id} className="flex items-center justify-between gap-2">
          <div>
            <Typography.Small>{friend.playerName || friend.email}</Typography.Small>
            <Typography.Muted>
              {friend.email} · id {friend.id}
            </Typography.Muted>
          </div>
          <Button variant="outline" size="sm" onClick={() => remove(friend)}>
            Remove
          </Button>
        </div>
      ))}

      <form onSubmit={onSubmit} noValidate>
        <FieldGroup>
          <Controller
            name="friendId"
            control={control}
            render={({ field, fieldState }) => (
              <Field data-invalid={fieldState.invalid}>
                <FieldLabel htmlFor="friend-id">Add a friend by player id</FieldLabel>
                <Input {...field} id="friend-id" inputMode="numeric" aria-invalid={fieldState.invalid} />
                <FieldDescription>Friendship is mutual: both players see each other as neighbours.</FieldDescription>
                {fieldState.invalid ? <FieldError errors={[fieldState.error]} /> : null}
              </Field>
            )}
          />
          {errors.root ? <FieldError errors={[errors.root]} /> : null}
          <Button type="submit" variant="outline" disabled={isSubmitting}>
            Add friend
          </Button>
        </FieldGroup>
      </form>
    </div>
  )
}
