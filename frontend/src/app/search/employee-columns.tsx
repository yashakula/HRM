"use client"

import { ColumnDef } from "@tanstack/react-table"
import { ArrowUpDown, MoreHorizontal } from "lucide-react"
import { Employee } from "@/lib/types"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"

export const employeeColumns: ColumnDef<Employee>[] = [
  {
    accessorKey: "person.full_name",
    header: ({ column }) => {
      return (
        <Button
          variant="ghost"
          onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
        >
          Name
          <ArrowUpDown className="ml-2 h-4 w-4" />
        </Button>
      )
    },
    cell: ({ row }) => {
      const employee = row.original
      return (
        <div>
          <div className="font-medium">{employee.person.full_name}</div>
          {employee.person.date_of_birth && (
            <div className="text-sm text-muted-foreground">
              DOB: {new Date(employee.person.date_of_birth).toLocaleDateString()}
            </div>
          )}
        </div>
      )
    },
  },
  {
    accessorKey: "employee_id",
    header: ({ column }) => {
      return (
        <div className="flex justify-center">
          <Button
            variant="ghost"
            onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
          >
            Employee ID
            <ArrowUpDown className="ml-2 h-4 w-4" />
          </Button>
        </div>
      )
    },
    cell: ({ row }) => {
      return <div className="text-center">{row.getValue("employee_id")}</div>
    },
  },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      const status = row.getValue("status") as string
      return (
        <Badge
          variant={status === "Active" ? "default" : "destructive"}
        >
          {status}
        </Badge>
      )
    },
  },
  {
    accessorKey: "work_email",
    header: "Work Email",
    cell: ({ row }) => {
      return row.getValue("work_email") || "-"
    },
  },
  {
    accessorKey: "effective_start_date",
    header: "Start Date",
    cell: ({ row }) => {
      const date = row.getValue("effective_start_date") as string
      return date ? new Date(date).toLocaleDateString() : "-"
    },
  },
  {
    id: "actions",
    cell: ({ row }) => {
      const employee = row.original

      return (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="h-8 w-8 p-0">
              <span className="sr-only">Open menu</span>
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Actions</DropdownMenuLabel>
            <DropdownMenuItem
              onClick={() => window.location.href = `/employees/${employee.employee_id}/edit`}
            >
              View Details
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )
    },
  },
]
