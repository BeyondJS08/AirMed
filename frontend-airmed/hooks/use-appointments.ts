import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import * as appointmentsService from "@/services/appointments"

export function useAppointments(params?: {
  status?: string
  date_from?: string
  date_to?: string
}) {
  return useQuery({
    queryKey: ["appointments", params],
    queryFn: () => appointmentsService.listAppointments(params),
  })
}

export function useAppointment(id: number) {
  return useQuery({
    queryKey: ["appointments", id],
    queryFn: () => appointmentsService.getAppointment(id),
    enabled: !!id,
  })
}

export function useCancelAppointment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => appointmentsService.cancelAppointment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] })
    },
  })
}

export function useUpdateAppointment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number
      data: { status?: string; notes?: string | null }
    }) => appointmentsService.updateAppointment(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] })
    },
  })
}
