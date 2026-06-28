"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useProfessionals } from "@/hooks/use-professionals"
import { useServices } from "@/hooks/use-services"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { getAvailableSlots } from "@/services/availability"
import { createAppointment } from "@/services/appointments"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import type { User, Slot } from "@/types"

type Step = "professional" | "service" | "slot" | "confirm"

export default function BookAppointmentPage() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const [step, setStep] = useState<Step>("professional")
  const [professional, setProfessional] = useState<User | null>(null)
  const [serviceId, setServiceId] = useState<number | null>(null)
  const [selectedDate, setSelectedDate] = useState("")
  const [selectedSlot, setSelectedSlot] = useState<Slot | null>(null)

  const { data: professionals, isLoading: loadingPros } = useProfessionals()
  const { data: services, isLoading: loadingServices } = useServices(professional?.id)

  const { data: slots, isLoading: loadingSlots } = useQuery({
    queryKey: ["available-slots", professional?.id, selectedDate, serviceId],
    queryFn: () => getAvailableSlots(professional!.id, selectedDate, serviceId ?? undefined),
    enabled: !!professional && !!selectedDate,
  })

  const bookMutation = useMutation({
    mutationFn: () =>
      createAppointment({
        professional_id: professional!.id,
        start_time: selectedSlot!.start_time,
        end_time: selectedSlot!.end_time,
        notes: null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] })
      router.push("/appointments")
    },
  })

  function reset() {
    setStep("professional")
    setProfessional(null)
    setServiceId(null)
    setSelectedDate("")
    setSelectedSlot(null)
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Book an Appointment</h1>
        <p className="text-sm text-muted-foreground">
          Find and book with a healthcare professional
        </p>
      </div>

      <div className="flex gap-2 text-sm text-muted-foreground">
        {["professional", "service", "slot", "confirm"].map((s, i) => (
          <span key={s} className={step === s ? "font-medium text-foreground" : ""}>
            {i + 1}. {s.charAt(0).toUpperCase() + s.slice(1)}
            {i < 3 && " → "}
          </span>
        ))}
      </div>

      {step === "professional" && (
        <section>
          <h2 className="mb-3 text-lg font-medium">Select a Professional</h2>
          {loadingPros ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : (
            <div className="grid gap-3">
              {(professionals || []).map((p) => (
                <Card
                  key={p.id}
                  className="cursor-pointer transition-colors hover:bg-muted/50"
                  onClick={() => {
                    setProfessional(p)
                    setStep("service")
                  }}
                >
                  <CardHeader>
                    <CardTitle className="text-base">{p.full_name || p.email}</CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm text-muted-foreground">
                    {p.email}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </section>
      )}

      {step === "service" && professional && (
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-medium">
              Select a Service — {professional.full_name || professional.email}
            </h2>
            <Button variant="ghost" size="sm" onClick={reset}>
              Change
            </Button>
          </div>
          {loadingServices ? (
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : !services?.length ? (
            <p className="text-sm text-muted-foreground">No services available.</p>
          ) : (
            <div className="grid gap-3">
              {services.map((s) => (
                <Card
                  key={s.id}
                  className="cursor-pointer transition-colors hover:bg-muted/50"
                  onClick={() => {
                    setServiceId(s.id)
                    setStep("slot")
                  }}
                >
                  <CardHeader>
                    <CardTitle className="text-base">{s.name}</CardTitle>
                  </CardHeader>
                  <CardContent className="text-sm text-muted-foreground">
                    <p>{s.duration_minutes} min{s.price != null ? ` — $${s.price}` : ""}</p>
                    {s.description && <p className="mt-1">{s.description}</p>}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </section>
      )}

      {step === "slot" && professional && (
        <section>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-medium">Pick a Date & Time</h2>
            <Button variant="ghost" size="sm" onClick={() => setStep("service")}>
              Back
            </Button>
          </div>
          <input
            type="date"
            className="mb-4 block rounded-md border px-3 py-2 text-sm"
            value={selectedDate}
            min={new Date().toISOString().slice(0, 10)}
            onChange={(e) => {
              setSelectedDate(e.target.value)
              setSelectedSlot(null)
            }}
          />
          {selectedDate && (
            <>
              {loadingSlots ? (
                <p className="text-sm text-muted-foreground">Loading available slots...</p>
              ) : !slots?.length ? (
                <p className="text-sm text-muted-foreground">No available slots for this date.</p>
              ) : (
                <div className="grid grid-cols-3 gap-2">
                  {slots.map((slot) => (
                    <Button
                      key={slot.start_time}
                      variant={
                        selectedSlot?.start_time === slot.start_time ? "default" : "outline"
                      }
                      onClick={() => {
                        setSelectedSlot(slot)
                        setStep("confirm")
                      }}
                    >
                      {new Date(slot.start_time).toLocaleTimeString([], {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </Button>
                  ))}
                </div>
              )}
            </>
          )}
        </section>
      )}

      {step === "confirm" && professional && selectedSlot && (
        <section>
          <h2 className="mb-3 text-lg font-medium">Confirm Appointment</h2>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Appointment Summary</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p><strong>Professional:</strong> {professional.full_name || professional.email}</p>
              <p><strong>Date:</strong> {new Date(selectedSlot.start_time).toLocaleDateString()}</p>
              <p>
                <strong>Time:</strong>{" "}
                {new Date(selectedSlot.start_time).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}{" "}
                –{" "}
                {new Date(selectedSlot.end_time).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </p>
              {serviceId && (
                <p>
                  <strong>Service:</strong>{" "}
                  {services?.find((s) => s.id === serviceId)?.name || `#${serviceId}`}
                </p>
              )}
            </CardContent>
          </Card>
          <div className="flex gap-3">
            <Button variant="outline" onClick={() => setStep("slot")}>
              Back
            </Button>
            <Button
              onClick={() => bookMutation.mutate()}
              disabled={bookMutation.isPending}
            >
              {bookMutation.isPending ? "Booking..." : "Confirm Booking"}
            </Button>
          </div>
        </section>
      )}
    </div>
  )
}
