import { useQuery } from "@tanstack/react-query"
import * as professionalsService from "@/services/professionals"

export function useProfessionals() {
  return useQuery({
    queryKey: ["professionals"],
    queryFn: () => professionalsService.listProfessionals(),
  })
}
