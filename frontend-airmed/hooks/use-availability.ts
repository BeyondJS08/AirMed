import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import * as availabilityService from "@/services/availability"

export function useAvailabilities() {
  return useQuery({
    queryKey: ["availabilities"],
    queryFn: () => availabilityService.listAvailabilities(),
  })
}

export function useCreateAvailability() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: {
      day_of_week: number
      start_time: string
      end_time: string
      is_active?: boolean
    }) => availabilityService.createAvailability(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["availabilities"] })
    },
  })
}

export function useUpdateAvailability() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: number
      data: {
        day_of_week?: number
        start_time?: string
        end_time?: string
        is_active?: boolean
      }
    }) => availabilityService.updateAvailability(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["availabilities"] })
    },
  })
}

export function useDeleteAvailability() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => availabilityService.deleteAvailability(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["availabilities"] })
    },
  })
}
