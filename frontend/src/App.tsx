import type { FC } from "react"
import { Route, Routes } from "react-router-dom"

import { AppLayout } from "@/components/layout/AppLayout"
import { GuestOnly, RequireAdmin, RequireUser } from "@/components/layout/guards"
import { AdminUsersPage } from "@/pages/admin/AdminUsersPage"
import { FriendsPage } from "@/pages/FriendsPage"
import { GamePage } from "@/pages/GamePage"
import { LoginPage } from "@/pages/LoginPage"
import { NotFoundPage } from "@/pages/NotFoundPage"
import { RegisterPage } from "@/pages/RegisterPage"

export const App: FC = () => (
  <Routes>
    <Route element={<AppLayout />}>
      <Route index element={<GamePage />} />
      <Route element={<GuestOnly />}>
        <Route path="login" element={<LoginPage />} />
        <Route path="register" element={<RegisterPage />} />
      </Route>
      <Route element={<RequireUser />}>
        <Route path="friends" element={<FriendsPage />} />
      </Route>
      <Route element={<RequireAdmin />}>
        <Route path="admin" element={<AdminUsersPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Route>
  </Routes>
)
