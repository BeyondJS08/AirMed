"use client"

import { useAppointments } from "@/hooks/use-appointments"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { StatusBadge } from "@/components/status-badge"

export default function ProfessionalOverviewPage() {
  const today = new Date().toISOString().split("T")[0]
  const { data: upcoming, isLoading: upcomingLoading } = useAppointments({
    date_from: today,
  })
  const { data: all, isLoading: allLoading } = useAppointments()

  if (upcomingLoading || allLoading) {
    return <div className="text-sm text-muted-foreground">Loading...</div>
  }

  const totalUpcoming = upcoming?.length ?? 0
  const totalScheduled =
    all?.filter((a) => a.status === "scheduled").length ?? 0
  const totalCompleted =
    all?.filter((a) => a.status === "completed").length ?? 0
  const totalCancelled =
    all?.filter((a) => a.status === "cancelled").length ?? 0
  const nextAppointment = upcoming?.[0]

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Overview</h1>
        <p className="text-sm text-muted-foreground">
          Welcome to your professional dashboard
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Upcoming
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{totalUpcoming}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Awaiting Confirmation
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{totalScheduled}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Completed
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{totalCompleted}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Cancelled
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-semibold">{totalCancelled}</p>
          </CardContent>
        </Card>
      </div>

      {nextAppointment && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Next Appointment</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">
              <span className="font-medium">
                {new Date(nextAppointment.start_time).toLocaleString()}
              </span>
              {" — "}
              {nextAppointment.is_virtual
                ? "Virtual"
                : nextAppointment.location || "In-person"}
            </p>
            <p className="text-sm text-muted-foreground">
              Status: <StatusBadge status={nextAppointment.status} />
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
