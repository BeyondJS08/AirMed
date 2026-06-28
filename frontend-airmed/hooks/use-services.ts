import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import type { ServiceCreate, ServiceUpdate } from "@/services/services"
import * as servicesService from "@/services/services"

export function useServices(professionalId?: number) {
  return useQuery({
    queryKey: ["services", professionalId],
    queryFn: () => servicesService.listServices(professionalId),
  })
}

export function useCreateService() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: ServiceCreate) => servicesService.createService(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["services"] })
    },
  })
}

export function useUpdateService() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ServiceUpdate }) =>
      servicesService.updateService(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["services"] })
    },
  })
}

export function useDeleteService() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => servicesService.deleteService(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["services"] })
    },
  })
}
