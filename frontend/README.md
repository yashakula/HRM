# HRM Frontend

This is the frontend application for the Human Resource Management (HRM) system, built with [Next.js](https://nextjs.org) and containerized with Docker.

## Features

- **Authentication System**: Session-based authentication with role-based access control
- **Employee Management**: Create and search employee profiles
- **Role-Based Navigation**: Different access levels for HR Admin, Supervisor, and Employee roles
- **Responsive Design**: Built with Tailwind CSS for mobile-friendly interface

## Testing & Demo

### Docker Deployment (Recommended)

The complete application runs in Docker containers. From the project root:

```bash
# Build and start all services
docker-compose up -d

# Initialize seed data
curl -X POST http://localhost:8000/admin/seed-data
```

**Application URLs:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Demo Accounts

The application comes with pre-configured demo accounts for testing:

| Role | Username | Password | Capabilities |
|------|----------|----------|-------------|
| **HR Admin** | `hr_admin` | `admin123` | Full access - create employees, manage all records |
| **Supervisor** | `supervisor1` | `super123` | Manage team - view employees, approve leave requests |
| **Employee** | `employee1` | `emp123` | Self-service - view directory, manage personal info |

### User Stories Implemented

- **US-01: Create Employee Profile** - HR Admin can create new employee records
- **US-02: Search Employee Records** - All users can search and view employee directory

## Development Setup

For local development without Docker:

```bash
# Install dependencies
npm install

# Set environment variables
cp .env.example .env.local

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Technology Stack

- **Framework**: Next.js 15 with App Router
- **Styling**: Tailwind CSS + Shadcn/ui components
- **State Management**: Zustand for auth state
- **Data Fetching**: TanStack Query (React Query)
- **Form Handling**: React Hook Form + Zod validation
- **Authentication**: Session-based with HTTP-only cookies
- **Container**: Docker with multi-stage builds

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── login/             # Authentication page
│   ├── employees/         # Employee management
│   └── layout.tsx         # Root layout with navigation
├── components/            # Reusable UI components
├── lib/                   # Utilities and configurations
│   ├── api.ts            # API client
│   └── types.ts          # TypeScript definitions
└── store/                # State management
    └── authStore.ts      # Authentication store
```

## Build & Deployment

```bash
# Build for production
npm run build

# Build Docker image
docker build -t hrm-frontend .

# Run container
docker run -p 3000:3000 hrm-frontend
```
