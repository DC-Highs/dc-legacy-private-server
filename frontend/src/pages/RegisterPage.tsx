import { zodResolver } from "@hookform/resolvers/zod"
import type { FC } from "react"
import { Controller, useForm } from "react-hook-form"
import { useNavigate } from "react-router-dom"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Link } from "@/components/ui/link"
import { Typography } from "@/components/ui/typography"
import { useAuth } from "@/lib/auth"
import { applyServerErrors } from "@/lib/forms"
import { AuthCard } from "@/pages/AuthCard"

const registerSchema = z
  .object({
    email: z.email("Enter a valid email"),
    password: z.string().min(8, "Use at least 8 characters").max(128, "Use at most 128 characters"),
    confirmPassword: z.string().min(1, "Repeat your password"),
  })
  .refine((values) => values.password === values.confirmPassword, {
    path: ["confirmPassword"],
    message: "Passwords do not match",
  })

type RegisterFormValues = z.infer<typeof registerSchema>

export const RegisterPage: FC = () => {
  const { register } = useAuth()
  const navigate = useNavigate()
  const {
    control,
    handleSubmit,
    setError,
    formState: { isSubmitting, errors },
  } = useForm<RegisterFormValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: "", password: "", confirmPassword: "" },
  })

  const onSubmit = handleSubmit(async (values) => {
    try {
      await register(values.email, values.password, values.confirmPassword)
      navigate("/")
    } catch (error) {
      const message = applyServerErrors(error, setError, ["email", "password", "confirmPassword"])
      if (message) setError("root", { message })
    }
  })

  return (
    <AuthCard
      title="Create your account"
      description="Just an email and a password. No confirmation code needed."
      footer={
        <Typography.Muted>
          Already have an account? <Link href="/login">Log in</Link>
        </Typography.Muted>
      }
    >
      <form onSubmit={onSubmit} noValidate>
        <FieldGroup>
          <Controller
            name="email"
            control={control}
            render={({ field, fieldState }) => (
              <Field data-invalid={fieldState.invalid}>
                <FieldLabel htmlFor="register-email">Email</FieldLabel>
                <Input {...field} id="register-email" type="email" autoComplete="email" aria-invalid={fieldState.invalid} />
                {fieldState.invalid ? <FieldError errors={[fieldState.error]} /> : null}
              </Field>
            )}
          />
          <Controller
            name="password"
            control={control}
            render={({ field, fieldState }) => (
              <Field data-invalid={fieldState.invalid}>
                <FieldLabel htmlFor="register-password">Password</FieldLabel>
                <Input
                  {...field}
                  id="register-password"
                  type="password"
                  autoComplete="new-password"
                  aria-invalid={fieldState.invalid}
                />
                <FieldDescription>At least 8 characters.</FieldDescription>
                {fieldState.invalid ? <FieldError errors={[fieldState.error]} /> : null}
              </Field>
            )}
          />
          <Controller
            name="confirmPassword"
            control={control}
            render={({ field, fieldState }) => (
              <Field data-invalid={fieldState.invalid}>
                <FieldLabel htmlFor="register-confirm">Confirm password</FieldLabel>
                <Input
                  {...field}
                  id="register-confirm"
                  type="password"
                  autoComplete="new-password"
                  aria-invalid={fieldState.invalid}
                />
                {fieldState.invalid ? <FieldError errors={[fieldState.error]} /> : null}
              </Field>
            )}
          />
          {errors.root ? <FieldError errors={[errors.root]} /> : null}
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Creating account..." : "Create account"}
          </Button>
        </FieldGroup>
      </form>
    </AuthCard>
  )
}
