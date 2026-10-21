import { zodResolver } from "@hookform/resolvers/zod"
import type { FC } from "react"
import { Controller, useForm } from "react-hook-form"
import { useNavigate } from "react-router-dom"
import { z } from "zod"

import { Button } from "@/components/ui/button"
import { Field, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field"
import { Input } from "@/components/ui/input"
import { Link } from "@/components/ui/link"
import { Typography } from "@/components/ui/typography"
import { useAuth } from "@/lib/auth"
import { applyServerErrors } from "@/lib/forms"
import { AuthCard } from "@/pages/AuthCard"

const loginSchema = z.object({
  email: z.string().min(1, "Enter your email"),
  password: z.string().min(1, "Enter your password"),
})

type LoginFormValues = z.infer<typeof loginSchema>

export const LoginPage: FC = () => {
  const { login } = useAuth()
  const navigate = useNavigate()
  const {
    control,
    handleSubmit,
    setError,
    formState: { isSubmitting, errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  })

  const onSubmit = handleSubmit(async (values) => {
    try {
      await login(values.email, values.password)
      navigate("/")
    } catch (error) {
      const message = applyServerErrors(error, setError, ["email", "password"])
      if (message) setError("root", { message })
    }
  })

  return (
    <AuthCard
      title="Log in"
      description="Enter your account to play."
      footer={
        <Typography.Muted>
          New here? <Link href="/register">Create an account</Link>
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
                <FieldLabel htmlFor="login-email">Email</FieldLabel>
                <Input {...field} id="login-email" type="email" autoComplete="email" aria-invalid={fieldState.invalid} />
                {fieldState.invalid ? <FieldError errors={[fieldState.error]} /> : null}
              </Field>
            )}
          />
          <Controller
            name="password"
            control={control}
            render={({ field, fieldState }) => (
              <Field data-invalid={fieldState.invalid}>
                <FieldLabel htmlFor="login-password">Password</FieldLabel>
                <Input
                  {...field}
                  id="login-password"
                  type="password"
                  autoComplete="current-password"
                  aria-invalid={fieldState.invalid}
                />
                {fieldState.invalid ? <FieldError errors={[fieldState.error]} /> : null}
              </Field>
            )}
          />
          {errors.root ? <FieldError errors={[errors.root]} /> : null}
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Logging in..." : "Log in"}
          </Button>
        </FieldGroup>
      </form>
    </AuthCard>
  )
}
