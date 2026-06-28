"use client"

import { useAppointments, useCancelAppointment } from "@/hooks/use-appointments"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { StatusBadge, formatDate } from "@/components/status-badge"
import Link from "next/link"

export default function AppointmentsPage() {
  const { data: appointments, isLoading } = useAppointments()
  const cancelMutation = useCancelAppointment()

  const upcoming = (appointments || []).filter(
    (a) => a.status === "scheduled" || a.status === "confirmed"
  )
  const past = (appointments || []).filter(
    (a) => a.status === "completed" || a.status === "cancelled"
  )

  async function handleCancel(id: number) {
    if (confirm("Cancel this appointment?")) {
      try {
        await cancelMutation.mutateAsync(id)
      } catch {}
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">My Appointments</h1>
          <p className="text-sm text-muted-foreground">
            View and manage your appointments
          </p>
        </div>
        <Button asChild>
          <Link href="/appointments/book">Book an appointment</Link>
        </Button>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading...</p>
      ) : !appointments?.length ? (
        <Card>
          <CardContent className="p-8 text-center text-muted-foreground">
            <p>No appointments yet.</p>
          </CardContent>
        </Card>
      ) : (
        <>
          <section>
            <h2 className="mb-3 text-lg font-medium">Upcoming</h2>
            {upcoming.length === 0 ? (
              <p className="text-sm text-muted-foreground">No upcoming appointments.</p>
            ) : (
              <div className="grid gap-3">
                {upcoming.map((appt) => (
                  <Card key={appt.id}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">{formatDate(appt.start_time)}</CardTitle>
                        <StatusBadge status={appt.status} />
                      </div>
                    </CardHeader>
                    <CardContent className="text-sm text-muted-foreground">
                      <p>{appt.is_virtual ? "Virtual" : appt.location || "In-person"}</p>
                      <p className="mt-1">
                        {new Date(appt.start_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                        {" – "}
                        {new Date(appt.end_time).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </p>
                      {appt.status !== "cancelled" && (
                        <Button
                          size="sm"
                          variant="destructive"
                          className="mt-2"
                          onClick={() => handleCancel(appt.id)}
                        >
                          Cancel
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </section>

          <section>
            <h2 className="mb-3 text-lg font-medium">Past</h2>
            {past.length === 0 ? (
              <p className="text-sm text-muted-foreground">No past appointments.</p>
            ) : (
              <div className="grid gap-3">
                {past.map((appt) => (
                  <Card key={appt.id}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">{formatDate(appt.start_time)}</CardTitle>
                        <StatusBadge status={appt.status} />
                      </div>
                    </CardHeader>
                    <CardContent className="text-sm text-muted-foreground">
                      <p>{appt.is_virtual ? "Virtual" : appt.location || "In-person"}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </div>
  )
}
