"use client"

import { ColumnDef } from "@tanstack/react-table"
import { ArrowUpDown } from "lucide-react"
import { Assignment } from "@/lib/types"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"

const getStatusBadge = (assignment: Assignment) => {
  const now = new Date()
  const startDate = assignment.effective_start_date ? new Date(assignment.effective_start_date) : null
  const endDate = assignment.effective_end_date ? new Date(assignment.effective_end_date) : null

  if (endDate && endDate < now) {
    return <Badge variant="destructive">Ended</Badge>
  } else if (startDate && startDate > now) {
    return <Badge variant="secondary">Future</Badge>
  } else {
    return <Badge variant="default">Active</Badge>
  }
}

const formatDate = (dateString?: string) => {
  if (!dateString) return "N/A"
  return new Date(dateString).toLocaleDateString()
}

export const assignmentColumns: ColumnDef<Assignment>[] = [
  {
    accessorKey: "employee.person.full_name",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Employee
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const assignment = row.original
      return (
        <div>
          <div className="font-medium">{assignment.employee.person.full_name}</div>
          <div className="text-sm text-muted-foreground">
            ID: {assignment.employee.employee_id}
          </div>
        </div>
      )
    },
  },
  {
    accessorKey: "assignment_type.description",
    header: "Role",
    cell: ({ row }) => {
      const assignment = row.original
      return (
        <div>
          <div className="font-medium">{assignment.assignment_type.description}</div>
          {assignment.description && (
            <div className="text-sm text-muted-foreground">
              {assignment.description}
            </div>
          )}
        </div>
      )
    },
  },
  {
    accessorKey: "assignment_type.department.name",
    header: "Department",
  },
  {
    id: "supervisors",
    header: "Supervisor(s)",
    cell: ({ row }) => {
      const assignment = row.original
      if (assignment.supervisors.length > 0) {
        return (
          <div className="flex flex-wrap gap-1">
            {assignment.supervisors.map((supervisor) => (
              <Badge key={supervisor.employee_id} variant="outline">
                {supervisor.person.full_name}
              </Badge>
            ))}
          </div>
        )
      }
      return <span className="text-muted-foreground">No supervisor</span>
    },
  },
  {
    accessorKey: "effective_start_date",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Start Date
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      return formatDate(row.getValue("effective_start_date"))
    },
  },
  {
    accessorKey: "effective_end_date",
    header: "End Date",
    cell: ({ row }) => {
      return formatDate(row.getValue("effective_end_date"))
    },
  },
  {
    id: "status",
    header: "Status",
    cell: ({ row }) => {
      return getStatusBadge(row.original)
    },
  },
]
