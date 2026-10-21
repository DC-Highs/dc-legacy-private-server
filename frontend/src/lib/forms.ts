import type { FieldValues, Path, UseFormSetError } from "react-hook-form"

import { ApiError } from "@/lib/api"

/** Show the errors the API returned next to their fields; returns a message for anything else. */
export const applyServerErrors = <T extends FieldValues>(
  error: unknown,
  setError: UseFormSetError<T>,
  knownFields: readonly string[],
): string | null => {
  if (!(error instanceof ApiError)) return "Something went wrong. Try again."

  let handled = false
  for (const [field, message] of Object.entries(error.fields)) {
    if (knownFields.includes(field)) {
      setError(field as Path<T>, { message })
      handled = true
    }
  }
  return handled ? null : error.message
}
