"use client"

import { useState } from "react"
import {
  useServices,
  useCreateService,
  useDeleteService,
} from "@/hooks/use-services"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function ServicesPage() {
  const { data: services, isLoading } = useServices()
  const createMutation = useCreateService()
  const deleteMutation = useDeleteService()

  const [name, setName] = useState("")
  const [duration, setDuration] = useState("30")
  const [price, setPrice] = useState("")
  const [description, setDescription] = useState("")
  const [error, setError] = useState("")

  async function handleAdd() {
    setError("")
    if (!name.trim()) {
      setError("Service name is required")
      return
    }
    const durationNum = parseInt(duration)
    if (isNaN(durationNum) || durationNum < 5) {
      setError("Duration must be at least 5 minutes")
      return
    }
    try {
      await createMutation.mutateAsync({
        name: name.trim(),
        description: description.trim() || null,
        duration_minutes: durationNum,
        price: price ? parseFloat(price) : null,
      })
      setName("")
      setDuration("30")
      setPrice("")
      setDescription("")
    } catch {
      setError("Failed to create service")
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Services</h1>
        <p className="text-sm text-muted-foreground">
          Manage the services you offer
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Add Service</CardTitle>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </div>
          )}
          <div className="grid gap-3 sm:grid-cols-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                placeholder="General checkup"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="duration">Duration (min)</Label>
              <Input
                id="duration"
                type="number"
                min={5}
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="price">Price ($)</Label>
              <Input
                id="price"
                type="number"
                min={0}
                step="0.01"
                placeholder="Optional"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="desc">Description</Label>
              <Input
                id="desc"
                placeholder="Optional"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
          </div>
          <Button
            onClick={handleAdd}
            disabled={createMutation.isPending}
            className="mt-3"
          >
            Add Service
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 text-sm text-muted-foreground">Loading...</div>
          ) : !services?.length ? (
            <div className="p-6 text-sm text-muted-foreground">
              No services added yet. Add one above.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Duration</TableHead>
                  <TableHead>Price</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {services.map((svc) => (
                  <TableRow key={svc.id}>
                    <TableCell className="font-medium">{svc.name}</TableCell>
                    <TableCell>{svc.duration_minutes} min</TableCell>
                    <TableCell>
                      {svc.price != null ? `$${svc.price.toFixed(2)}` : "—"}
                    </TableCell>
                    <TableCell className="text-muted-foreground">
                      {svc.description || "—"}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => deleteMutation.mutate(svc.id)}
                        disabled={deleteMutation.isPending}
                      >
                        Remove
                      </Button>
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
