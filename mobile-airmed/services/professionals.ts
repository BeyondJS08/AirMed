import { api } from "../api/client";
import { User } from "../types";

export async function listProfessionals(): Promise<User[]> {
  return api<User[]>("/users/professionals");
}
