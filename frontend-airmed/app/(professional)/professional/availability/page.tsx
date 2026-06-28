"use client"

import { useState } from "react"
import {
  useAvailabilities,
  useCreateAvailability,
  useDeleteAvailability,
} from "@/hooks/use-availability"
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const DAY_LABELS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
  "Sunday",
]

export default function AvailabilityPage() {
  const { data: availabilities, isLoading } = useAvailabilities()
  const createMutation = useCreateAvailability()
  const deleteMutation = useDeleteAvailability()

  const [dayOfWeek, setDayOfWeek] = useState("")
  const [startTime, setStartTime] = useState("09:00")
  const [endTime, setEndTime] = useState("17:00")
  const [error, setError] = useState("")

  async function handleAdd() {
    setError("")
    if (!dayOfWeek) {
      setError("Please select a day")
      return
    }
    if (startTime >= endTime) {
      setError("End time must be after start time")
      return
    }
    try {
      await createMutation.mutateAsync({
        day_of_week: parseInt(dayOfWeek),
        start_time: `${startTime}:00`,
        end_time: `${endTime}:00`,
      })
      setDayOfWeek("")
      setStartTime("09:00")
      setEndTime("17:00")
    } catch {
      setError("Failed to create availability")
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold">Availability</h1>
        <p className="text-sm text-muted-foreground">
          Manage your weekly availability windows
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Add Weekly Window</CardTitle>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive">
              {error}
            </div>
          )}
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="day">Day</Label>
              <Select value={dayOfWeek} onValueChange={setDayOfWeek}>
                <SelectTrigger id="day" className="w-40">
                  <SelectValue placeholder="Select day" />
                </SelectTrigger>
                <SelectContent>
                  {DAY_LABELS.map((label, i) => (
                    <SelectItem key={i} value={String(i)}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="start">Start</Label>
              <Input
                id="start"
                type="time"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                className="w-32"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="end">End</Label>
              <Input
                id="end"
                type="time"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                className="w-32"
              />
            </div>
            <Button onClick={handleAdd} disabled={createMutation.isPending}>
              Add Window
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="p-6 text-sm text-muted-foreground">Loading...</div>
          ) : !availabilities?.length ? (
            <div className="p-6 text-sm text-muted-foreground">
              No availability windows set. Add one above.
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Day</TableHead>
                  <TableHead>Start</TableHead>
                  <TableHead>End</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {availabilities.map((av) => (
                  <TableRow key={av.id}>
                    <TableCell className="font-medium">
                      {DAY_LABELS[av.day_of_week]}
                    </TableCell>
                    <TableCell>{av.start_time}</TableCell>
                    <TableCell>{av.end_time}</TableCell>
                    <TableCell>
                      {av.is_active ? (
                        <span className="text-xs font-medium text-green-600 dark:text-green-400">
                          Active
                        </span>
                      ) : (
                        <span className="text-xs font-medium text-muted-foreground">
                          Inactive
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => deleteMutation.mutate(av.id)}
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
