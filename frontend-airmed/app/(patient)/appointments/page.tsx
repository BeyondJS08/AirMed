import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function AppointmentsPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">My Appointments</h1>
        <p className="text-sm text-muted-foreground">
          View and manage your appointments
        </p>
      </div>
      <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
        <p>No appointments yet.</p>
        <Button asChild className="mt-4">
          <Link href="/appointments/book">Book an appointment</Link>
        </Button>
      </div>
    </div>
  )
}
