import { zodResolver } from "@hookform/resolvers/zod"
import { CopyIcon } from "lucide-react"
import { useCallback, useEffect, useState } from "react"
import type { FC, ReactNode } from "react"
import { Controller, useForm } from "react-hook-form"
import { toast } from "sonner"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { Typography } from "@/components/ui/typography"
import { api } from "@/lib/api"
import type { FriendProfile, FriendsOverview } from "@/lib/api"
import { applyServerErrors } from "@/lib/forms"
import { usePending } from "@/lib/pending"

const addFriendSchema = z.object({
  playerId: z.string().regex(/^\d{1,16}$/, "Enter a player id (digits only)"),
})

type AddFriendFormValues = z.infer<typeof addFriendSchema>

const errorMessage = (error: unknown) => (error instanceof Error ? error.message : "Something went wrong")

type PersonRowProps = { person: FriendProfile; actions: ReactNode }

const PersonRow: FC<PersonRowProps> = ({ person, actions }) => (
  <div className="flex items-center justify-between gap-3">
    <div>
      <Typography.Small>{person.playerName || `Player ${person.id}`}</Typography.Small>
      <Typography.Muted>
        Level {person.level} · id {person.id}
      </Typography.Muted>
    </div>
    <div className="flex gap-2">{actions}</div>
  </div>
)

export const FriendsPage: FC = () => {
  const { refresh } = usePending()
  const [overview, setOverview] = useState<FriendsOverview | null>(null)
  const [removing, setRemoving] = useState<number | null>(null)
  const {
    control,
    handleSubmit,
    reset,
    setError,
    formState: { isSubmitting, errors },
  } = useForm<AddFriendFormValues>({
    resolver: zodResolver(addFriendSchema),
    defaultValues: { playerId: "" },
  })

  const load = useCallback(async () => {
    try {
      setOverview(await api.get<FriendsOverview>("/api/friends"))
    } catch (error) {
      toast.error(errorMessage(error))
    }
    void refresh()
  }, [refresh])

  useEffect(() => {
    void load()
  }, [load])

  const gemsMessage = (gems: number) => (gems > 0 ? ` You got ${gems} gems!` : "")

  const sendRequest = handleSubmit(async (values) => {
    try {
      const data = await api.post<{ accepted: boolean; gemsAwarded: number }>("/api/friends/requests", {
        playerId: Number(values.playerId),
      })
      toast.success(
        data.accepted ? `You are now friends!${gemsMessage(data.gemsAwarded)}` : "Friend request sent",
      )
      reset({ playerId: "" })
      await load()
    } catch (error) {
      const message = applyServerErrors(error, setError, ["playerId"])
      if (message) setError("root", { message })
    }
  })

  const answer = async (requestId: number, action: "accept" | "decline") => {
    try {
      const data = await api.post<{ gemsAwarded?: number }>(`/api/friends/requests/${requestId}/${action}`)
      toast.success(action === "accept" ? `Friend added.${gemsMessage(data.gemsAwarded ?? 0)}` : "Request declined")
    } catch (error) {
      toast.error(errorMessage(error))
    }
    await load()
  }

  const cancel = async (requestId: number) => {
    try {
      await api.delete(`/api/friends/requests/${requestId}`)
      toast.success("Request cancelled")
    } catch (error) {
      toast.error(errorMessage(error))
    }
    await load()
  }

  const removeFriend = async (friend: FriendProfile) => {
    try {
      await api.delete(`/api/friends/${friend.id}`)
      toast.success(`${friend.playerName || friend.id} is no longer your friend`)
    } catch (error) {
      toast.error(errorMessage(error))
    }
    setRemoving(null)
    await load()
  }

  const copyId = async () => {
    if (!overview) return
    try {
      await navigator.clipboard.writeText(String(overview.playerId))
      toast.success("Player id copied")
    } catch {
      toast.error("Could not copy. Select the number and copy it by hand.")
    }
  }

  if (!overview) {
    return (
      <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 p-4">
        <Skeleton className="h-28 w-full" />
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }

  const { rewardGems, rewardLimit, maxFriends } = overview.limits

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-4 p-4">
      <div>
        <Typography.H2>Friends</Typography.H2>
        <Typography.Muted>
          Friends are your neighbours in the game: you can visit them and help them.
        </Typography.Muted>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Your player id</CardTitle>
          <CardDescription>Share this number so other players can add you.</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-3">
          <Typography.Code className="text-lg">{overview.playerId}</Typography.Code>
          <Button variant="outline" size="sm" onClick={copyId}>
            <CopyIcon /> Copy
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Add a friend</CardTitle>
          <CardDescription>
            You both get {rewardGems} gems for each of your first {rewardLimit} friends.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={sendRequest} noValidate>
            <FieldGroup>
              <Controller
                name="playerId"
                control={control}
                render={({ field, fieldState }) => (
                  <Field data-invalid={fieldState.invalid}>
                    <FieldLabel htmlFor="friend-player-id">Player id</FieldLabel>
                    <Input
                      {...field}
                      id="friend-player-id"
                      inputMode="numeric"
                      placeholder="200000000"
                      aria-invalid={fieldState.invalid}
                    />
                    <FieldDescription>They have to accept your request.</FieldDescription>
                    {fieldState.invalid ? <FieldError errors={[fieldState.error]} /> : null}
                  </Field>
                )}
              />
              {errors.root ? <FieldError errors={[errors.root]} /> : null}
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Sending..." : "Send request"}
              </Button>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>

      {overview.incoming.length > 0 || overview.outgoing.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Requests</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {overview.incoming.map((request) => (
              <PersonRow
                key={request.requestId}
                person={request.from}
                actions={
                  <>
                    <Button size="sm" onClick={() => answer(request.requestId, "accept")}>
                      Accept
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => answer(request.requestId, "decline")}>
                      Decline
                    </Button>
                  </>
                }
              />
            ))}
            {overview.outgoing.map((request) => (
              <PersonRow
                key={request.requestId}
                person={request.to}
                actions={
                  <>
                    <Typography.Muted className="self-center">Waiting for an answer</Typography.Muted>
                    <Button size="sm" variant="outline" onClick={() => cancel(request.requestId)}>
                      Cancel
                    </Button>
                  </>
                }
              />
            ))}
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>
            Your friends ({overview.friends.length}/{maxFriends})
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {overview.friends.length === 0 ? <Typography.Muted>No friends yet.</Typography.Muted> : null}
          {overview.friends.map((friend) => (
            <PersonRow
              key={friend.id}
              person={friend}
              actions={
                removing === friend.id ? (
                  <>
                    <Button size="sm" variant="destructive" onClick={() => removeFriend(friend)}>
                      Confirm
                    </Button>
                    <Button size="sm" variant="outline" onClick={() => setRemoving(null)}>
                      Cancel
                    </Button>
                  </>
                ) : (
                  <Button size="sm" variant="outline" onClick={() => setRemoving(friend.id)}>
                    Remove
                  </Button>
                )
              }
            />
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
