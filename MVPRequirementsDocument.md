# MVP Requirements Document

**Project:** Human Resource Management Software MVP  
**Version:** 1.0  
**Date:** [YYYY-MM-DD]  
**Author:** [Name]

---

## 1. Introduction
This document defines the Minimum Viable Product (MVP) for the Human Resource Management (HRM) software, focusing on core HR functionalities that deliver immediate value.

## 2. Scope
The MVP includes three primary modules:

1. **Employee Management (CRUD)**
2. **Leave Request & Approval**
3. **Attendance Logging**

All other features—payroll, performance management, analytics, integrations—will be implemented in future releases.

## 3. Core Features

### 3.1 Employee Management (CRUD)
- **Create:** New employee records, including personal and job details.
- **Read:** Search and view existing employee profiles.
- **Update:** Edit employee information with version control.
- **Delete/Deactivate:** Soft delete or deactivate profiles.
- **Assignment Management:**
  - HR Admin defines assignments (job roles, projects) and assigns them to employees.
  - Employees can have multiple assignments but only one primary assignment.
  - Each assignment is linked to one or more supervisors who oversee related leave and attendance.

### 3.2 Leave Request & Approval
- Employees submit leave requests with dates and reasons; requests route to supervisors of all assignments held by the employee.
- Supervisors view pending requests in their dashboard.
- Supervisors and HR Admin approve or reject requests; leave is finalized only after approval from all relevant supervisors.
- Automated notifications inform employees of status changes.

### 3.3 Attendance Logging
- Employees check in and check out per assignment.
- The system records timestamps and calculates total hours worked.
- Supervisors and HR Admin can view and export attendance reports.

## 4. User Stories

### 4.1 HR Admin

| ID    | User Story                                                                                                       | Acceptance Criteria                                                                                               |
|-------|-------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| US-01 | As an HR Admin, I want to create a new employee profile so that I can maintain accurate personnel records.        | Form captures name, ID, department, and role. Success confirmation is displayed.                                   |
| US-02 | As an HR Admin, I want to search and view employee records so that I can quickly find staff details.              | Search by name or employee ID. List displays name, department, and status.                                        |
| US-03 | As an HR Admin, I want to update employee information so that records remain current.                            | Editable fields match profile details. Changes are saved correctly.                                               |
| US-04 | As an HR Admin, I want to deactivate an employee so that inactive staff are excluded from active lists.          | Profile is flagged as “Inactive” and excluded from default active searches.                                        |
| US-11 | As an HR Admin, I want to approve or reject leave requests so that leave is managed effectively.                  | Dashboard shows pending requests. Approval or rejection updates status and sends notifications to the employee.   |
| US-13 | As an HR Admin, I want to define assignments so that I can categorize job roles and projects.                    | Assignment form captures name, description, and default settings. Saved successfully.                              |
| US-14 | As an HR Admin, I want to assign assignments and designate supervisors so that reporting lines are clear.        | Assignment is linked to the employee with supervisor relationships stored.                                        |
| US-15 | As an HR Admin, I want to set a primary assignment for employees so that their main role is clear.               | Ability to mark one assignment as primary. Primary flag is stored correctly.                                      |

### 4.2 Supervisor

| ID    | User Story                                                                                                       | Acceptance Criteria                                                                                               |
|-------|-------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| US-10 | As a Supervisor, I want to view employees under my assignments so that I can manage their leave and attendance.   | Dashboard filters tasks by assignments. Lists supervisee names and pending tasks.                                 |
| US-06 | As a Supervisor, I want to approve or reject leave requests for my supervisees so that leave is managed properly. | Dashboard shows only my supervisees’ requests. Status updates and notifications function correctly.               |
| US-12 | As a Supervisor, I want to view attendance records for my supervisees so that I can monitor their working hours. | Attendance table is filtered to my supervisees, showing dates and total hours.                                   |

### 4.3 Employee

| ID    | User Story                                                                                                       | Acceptance Criteria                                                                                               |
|-------|-------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------|
| US-05 | As an Employee, I want to submit a leave request so that I can schedule time off.                                 | Request captures assignment context, dates, and reason. Confirmation message is displayed.                        |
| US-07 | As an Employee, I want to track the status of my leave requests so that I know when my time off is approved.     | Leave history displays each request with its current status.                                                      |
| US-08 | As an Employee, I want to log my attendance so that my working hours are recorded accurately.                     | Check-in and check-out buttons record timestamps correctly.                                                       |

## 5. Acceptance Criteria
- Responsive and accessible forms and dashboards.
- Validation for required fields and correct date formats.
- Role-based views for HR Admin, Supervisors, and Employees.
- Notifications for key actions: submission, approval, rejection.

## 6. Next Steps
1. Develop wireframes and UI prototypes.
2. Conduct a technical spike to validate schema and authentication.
3. Break down user stories into actionable tasks and plan sprint iterations.

---

*End of MVP Requirements Document*

