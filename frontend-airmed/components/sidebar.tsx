"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { useAuthStore } from "@/stores/auth-store"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const patientLinks = [
  { href: "/appointments", label: "My Appointments" },
  { href: "/appointments/book", label: "Book Appointment" },
]

const professionalLinks = [
  { href: "/professional", label: "Overview" },
  { href: "/professional/appointments", label: "Appointments" },
  { href: "/professional/availability", label: "Availability" },
  { href: "/professional/services", label: "Services" },
]

export function Sidebar({ role }: { role: "patient" | "professional" }) {
  const pathname = usePathname()
  const logout = useAuthStore((s) => s.logout)
  const user = useAuthStore((s) => s.user)
  const links = role === "patient" ? patientLinks : professionalLinks

  return (
    <aside className="flex w-64 flex-col border-r bg-muted/30">
      <div className="flex h-14 items-center border-b px-4">
        <Link href="/" className="text-lg font-semibold">
          AirMed
        </Link>
      </div>

      <nav className="flex-1 space-y-1 p-3">
        {links.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={cn(
              "flex items-center rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              pathname === link.href
                ? "bg-primary/10 text-primary"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            )}
          >
            {link.label}
          </Link>
        ))}
      </nav>

      <div className="border-t p-3">
        <div className="mb-2 px-3 text-xs text-muted-foreground">
          {user?.full_name || user?.email}
        </div>
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          onClick={() => {
            logout()
            window.location.href = "/login"
          }}
        >
          Sign out
        </Button>
      </div>
    </aside>
  )
}
