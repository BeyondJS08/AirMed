"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuthStore } from "@/stores/auth-store"
import { Sidebar } from "@/components/sidebar"

export default function ProfessionalLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const user = useAuthStore((s) => s.user)

  useEffect(() => {
    if (!isAuthenticated) {
      router.push("/login")
    } else if (user && !user.is_professional) {
      router.push("/appointments")
    }
  }, [isAuthenticated, user, router])

  if (!isAuthenticated || !user) return null

  return (
    <div className="flex min-h-svh">
      <Sidebar role="professional" />
      <main className="flex-1 p-6">{children}</main>
    </div>
  )
}
