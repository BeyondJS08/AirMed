"use client"

import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth-store"

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const router = useRouter()

  if (isAuthenticated) {
    router.push("/")
    return null
  }

  return (
    <div className="flex min-h-svh items-center justify-center p-4">
      <div className="w-full max-w-sm">{children}</div>
    </div>
  )
}
