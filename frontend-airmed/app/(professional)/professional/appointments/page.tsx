"use client"

import { useState } from "react"
import { useAppointments, useUpdateAppointment } from "@/hooks/use-appointments"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { StatusBadge, formatDate } from "@/components/status-badge"
import { toast } from "sonner"

function TableSkeleton() {
  return (
    <div className="space-y-3 p-6">
      {[1, 2, 3].map((i) => (
        <div key={i} className="flex items-center gap-4">
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-8 w-32" />
        </div>
      ))}
    </div>
  )
}

export default function ProfessionalAppointmentsPage() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>()
  const { data: appointments, isLoading } = useAppointments(
    statusFilter ? { status: statusFilter } : undefined
  )
  const updateMutation = useUpdateAppointment()

  const filters = ["", "scheduled", "confirmed", "completed", "cancelled"]

  async function handleStatus(id: number, status: string) {
    const label = status.charAt(0).toUpperCase() + status.slice(1)
    toast.promise(updateMutation.mutateAsync({ id, data: { status } }), {
      loading: `Updating appointment...`,
      success: `Appointment ${label.toLowerCase()}`,
      error: `Failed to ${label.toLowerCase()} appointment`,
    })
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Appointments</h1>
          <p className="text-sm text-muted-foreground">
            Manage your appointments
          </p>
        </div>
        <div className="flex gap-2">
          {filters.map((f) => (
            <Button
              key={f}
              variant={statusFilter === f ? "default" : "outline"}
              size="sm"
              onClick={() => setStatusFilter(f || undefined)}
            >
              {f || "All"}
            </Button>
          ))}
        </div>
      </div>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <TableSkeleton />
          ) : !appointments?.length ? (
            <div className="p-6 text-sm text-muted-foreground">
              No appointments found.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date & Time</TableHead>
                  <TableHead>Patient</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {appointments.map((appt) => (
                  <TableRow key={appt.id}>
                    <TableCell className="font-medium">
                      {formatDate(appt.start_time)}
                    </TableCell>
                    <TableCell>#{appt.patient_id}</TableCell>
                    <TableCell>
                      {appt.is_virtual
                        ? "Virtual"
                        : appt.location || "In-person"}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={appt.status} />
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-2">
                        {appt.status === "scheduled" && (
                          <>
                            <Button
                              size="sm"
                              onClick={() => handleStatus(appt.id, "confirmed")}
                            >
                              Confirm
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => handleStatus(appt.id, "cancelled")}
                            >
                              Cancel
                            </Button>
                          </>
                        )}
                        {appt.status === "confirmed" && (
                          <>
                            <Button
                              size="sm"
                              onClick={() => handleStatus(appt.id, "completed")}
                            >
                              Complete
                            </Button>
                            <Button
                              size="sm"
                              variant="destructive"
                              onClick={() => handleStatus(appt.id, "cancelled")}
                            >
                              Cancel
                            </Button>
                          </>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
