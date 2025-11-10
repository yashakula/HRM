'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMutation } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { EmployeeCreateRequest } from '@/lib/types';
import ProtectedRoute from '@/components/auth/ProtectedRoute';
import PermissionGuard from '@/components/auth/PermissionGuard';
import { SensitiveField, PermissionBasedSection } from '@/components/auth/ConditionalRender';
import {
  Field,
  FieldDescription,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from "@/components/ui/field"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { DatePicker } from "@/components/ui/date-picker"

export default function CreateEmployeePage() {
  return (
    <ProtectedRoute
      pageIdentifier="employees/create"
      requiredPermissions={['view', 'create']}
    >
      <PermissionGuard
        permission="employee.create"
        fallback={
          <div className="text-center py-12">
            <div className="text-6xl mb-4">🔒</div>
            <h3 className="text-lg font-medium mb-2">Access Denied</h3>
            <p className="text-muted-foreground">You don&apos;t have permission to create employees.</p>
          </div>
        }
      >
        <CreateEmployeeForm />
      </PermissionGuard>
    </ProtectedRoute>
  );
}

function CreateEmployeeForm() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [dateOfBirth, setDateOfBirth] = useState<Date | undefined>();
  const [startDate, setStartDate] = useState<Date | undefined>();
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [confirmEmail, setConfirmEmail] = useState('');
  const [ssn, setSSN] = useState('');
  const [confirmSSN, setConfirmSSN] = useState('');
  const [bankAccount, setBankAccount] = useState('');
  const [confirmBankAccount, setConfirmBankAccount] = useState('');
  const [workEmail, setWorkEmail] = useState('');
  const [department, setDepartment] = useState('');

  const createEmployeeMutation = useMutation({
    mutationFn: (data: EmployeeCreateRequest) => apiClient.createEmployee(data),
    onSuccess: () => {
      setIsSubmitting(false);
      router.push('/employees');
    },
    onError: (error) => {
      setIsSubmitting(false);
      console.error('Failed to create employee:', error);
    },
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    // Validation
    if (email !== confirmEmail) {
      alert('Emails do not match');
      setIsSubmitting(false);
      return;
    }

    if (ssn !== confirmSSN) {
      alert('SSN does not match');
      setIsSubmitting(false);
      return;
    }

    if (bankAccount !== confirmBankAccount) {
      alert('Bank account numbers do not match');
      setIsSubmitting(false);
      return;
    }

    // Transform form data to API format
    const employeeData: EmployeeCreateRequest = {
      person: {
        full_name: `${firstName} ${lastName}`.trim(),
        date_of_birth: dateOfBirth?.toISOString().split('T')[0],
      },
      work_email: workEmail || undefined,
      effective_start_date: startDate?.toISOString().split('T')[0],
    };

    // Add personal information if any field is filled
    const hasPersonalInfo = email || ssn || bankAccount;
    if (hasPersonalInfo) {
      employeeData.personal_information = {
        personal_email: email || undefined,
        ssn: ssn || undefined,
        bank_account: bankAccount || undefined,
      };
    }

    createEmployeeMutation.mutate(employeeData);
  };

  return (
    <div>
      <div className="w-full max-w-3xl mx-auto">
        <form onSubmit={onSubmit}>
          <FieldGroup>
            <FieldSet>
              <FieldLegend>Personal Information</FieldLegend>
              <FieldGroup className="grid grid-cols-2 gap-4">
                <Field>
                  <FieldLabel htmlFor="first-name">First Name</FieldLabel>
                  <Input
                    id="first-name"
                    placeholder="Enter First Name"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    required
                  />
                </Field>
                <Field>
                  <FieldLabel htmlFor="last-name">Last Name</FieldLabel>
                  <Input
                    id="last-name"
                    placeholder="Enter Last Name"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    required
                  />
                </Field>
                <Field>
                  <FieldLabel htmlFor="email">Email</FieldLabel>
                  <Input
                    id="email"
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                  />
                </Field>
                <Field>
                  <FieldLabel htmlFor="confirmEmail">Confirm Email</FieldLabel>
                  <Input
                    id="confirmEmail"
                    type="email"
                    placeholder="Confirm Email"
                    value={confirmEmail}
                    onChange={(e) => setConfirmEmail(e.target.value)}
                    required
                  />
                </Field>
                <Field>
                <DatePicker
                  label="Date of Birth"
                  id="date_of_birth"
                  placeholder="Select date of birth"
                  value={dateOfBirth}
                  onChange={setDateOfBirth}
                />
              </Field>
              </FieldGroup>
              
            </FieldSet>
            <PermissionBasedSection
              sectionType="hr_admin"
              title="Sensitive Information"
              description="Financial and identity information (HR Admin only)"
              fallback={
                <div className="border border-border rounded-md p-4">
                  <p className="text-sm">
                    Sensitive information fields are only visible to HR Administrators.
                  </p>
                </div>
              }
            >
              <FieldSet>
                {/* <FieldLegend>Sensitive Information</FieldLegend>
                <FieldDescription>Financial and identity information (HR Admin only)</FieldDescription> */}
                <FieldGroup className="grid grid-cols-2 gap-4">
                  <SensitiveField fieldType="ssn">
                    <Field>
                      <FieldLabel htmlFor="ssn">SSN</FieldLabel>
                      <Input
                        id="ssn"
                        placeholder="XXX-XX-XXXX"
                        value={ssn}
                        onChange={(e) => setSSN(e.target.value)}
                      />
                    </Field>
                  </SensitiveField>
                  <SensitiveField fieldType="ssn">
                    <Field>
                      <FieldLabel htmlFor="confirmSSN">Confirm SSN</FieldLabel>
                      <Input
                        id="confirmSSN"
                        placeholder="XXX-XX-XXXX"
                        value={confirmSSN}
                        onChange={(e) => setConfirmSSN(e.target.value)}
                      />
                    </Field>
                  </SensitiveField>
                  <SensitiveField fieldType="bank_account">
                    <Field>
                      <FieldLabel htmlFor="bankAcc">Bank Account Number</FieldLabel>
                      <Input
                        id="bankAcc"
                        placeholder="Account Number"
                        value={bankAccount}
                        onChange={(e) => setBankAccount(e.target.value)}
                      />
                    </Field>
                  </SensitiveField>
                  <SensitiveField fieldType="bank_account">
                    <Field>
                      <FieldLabel htmlFor="confirmBankAcc">Confirm Bank Account Number</FieldLabel>
                      <Input
                        id="confirmBankAcc"
                        placeholder="Account Number"
                        value={confirmBankAccount}
                        onChange={(e) => setConfirmBankAccount(e.target.value)}
                      />
                    </Field>
                  </SensitiveField>
                </FieldGroup>
              </FieldSet>
            </PermissionBasedSection>

            <FieldSet>
              <FieldLegend>Employment Information</FieldLegend>
              <FieldGroup className="grid grid-cols-2 gap-4">
              <Field>
                <FieldLabel htmlFor="workEmail">Work Email</FieldLabel>
                <Input
                  id="workEmail"
                  type="email"
                  placeholder="employee@company.com"
                  value={workEmail}
                  onChange={(e) => setWorkEmail(e.target.value)}
                  required
                />
              </Field>
              <Field>
                <FieldLabel>Department</FieldLabel>
                <Select value={department} onValueChange={setDepartment}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose department" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="engineering">Engineering</SelectItem>
                    <SelectItem value="design">Design</SelectItem>
                    <SelectItem value="marketing">Marketing</SelectItem>
                    <SelectItem value="sales">Sales</SelectItem>
                    <SelectItem value="support">Customer Support</SelectItem>
                    <SelectItem value="hr">Human Resources</SelectItem>
                    <SelectItem value="finance">Finance</SelectItem>
                    <SelectItem value="operations">Operations</SelectItem>
                  </SelectContent>
                </Select>
                <FieldDescription>
                  Select your department or area of work.
                </FieldDescription>
              </Field>
              <Field>
                <DatePicker
                  label="Start Date"
                  id="start_date"
                  placeholder="Select start date"
                  value={startDate}
                  onChange={setStartDate}
                />
              </Field>
            </FieldGroup>
            </FieldSet>

            {/* Error Display */}
            {createEmployeeMutation.error && (
              <div className="bg-destructive/10 border border-destructive/50 rounded-md p-4">
                <p className="text-destructive text-sm">
                  Error creating employee: {createEmployeeMutation.error instanceof Error
                    ? createEmployeeMutation.error.message
                    : 'Unknown error'}
                </p>
              </div>
            )}

            {/* Form Actions */}
            <div className="flex justify-end gap-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.push('/employees')}
              >
                Cancel
              </Button>

              <Button
                type="submit"
                disabled={isSubmitting}
              >
                {isSubmitting ? 'Creating...' : 'Create Employee'}
              </Button>
            </div>
          </FieldGroup>
        </form>
      </div>
    </div>
  );
}