"use client"

import * as React from "react"
import { CalendarIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"

function formatDate(date: Date | undefined) {
  if (!date) {
    return ""
  }

  return date.toLocaleDateString("en-US", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  })
}

function isValidDate(date: Date | undefined) {
  if (!date) {
    return false
  }
  return !isNaN(date.getTime())
}

interface DatePickerProps {
  label?: string
  placeholder?: string
  value?: Date
  onChange?: (date: Date | undefined) => void
  id?: string
  className?: string
}

export function DatePicker({
  label = "Date",
  placeholder = "Select a date",
  value: externalValue,
  onChange,
  id = "date",
  className,
}: DatePickerProps) {
  const [open, setOpen] = React.useState(false)
  const [date, setDate] = React.useState<Date | undefined>(externalValue)
  const [month, setMonth] = React.useState<Date | undefined>(externalValue || new Date())
  const [value, setValue] = React.useState(formatDate(externalValue))

  // Update internal state when external value changes
  React.useEffect(() => {
    setDate(externalValue)
    setValue(formatDate(externalValue))
    if (externalValue) {
      setMonth(externalValue)
    }
  }, [externalValue])

  const handleDateChange = (newDate: Date | undefined) => {
    setDate(newDate)
    setValue(formatDate(newDate))
    if (newDate) {
      setMonth(newDate)
    }
    onChange?.(newDate)
  }

  return (
    <div className="flex flex-col gap-3">
      <Label htmlFor={id} className="px-1">
        {label}
      </Label>
      <div className="relative flex gap-2">
        <Input
          id={id}
          value={value}
          placeholder={placeholder}
          className="bg-background pr-10"
          onChange={(e) => {
            const inputDate = new Date(e.target.value)
            setValue(e.target.value)
            if (isValidDate(inputDate)) {
              handleDateChange(inputDate)
            }
          }}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") {
              e.preventDefault()
              setOpen(true)
            }
          }}
        />
        <Popover open={open} onOpenChange={setOpen}>
          <PopoverTrigger asChild>
            <Button
              id={`${id}-picker`}
              variant="ghost"
              className="absolute top-1/2 right-2 size-6 -translate-y-1/2"
            >
              <CalendarIcon className="size-3.5" />
              <span className="sr-only">Select date</span>
            </Button>
          </PopoverTrigger>
          <PopoverContent
            className="w-auto p-0"
            align="start"
          >
            <div className="p-3">
              <Calendar
                mode="single"
                selected={date}
                captionLayout="dropdown"
                month={month}
                onMonthChange={setMonth}
                onSelect={(selectedDate) => {
                  handleDateChange(selectedDate)
                  setOpen(false)
                }}
                className="scale-110"
              />
            </div>
          </PopoverContent>
        </Popover>
      </div>
    </div>
  )
}
