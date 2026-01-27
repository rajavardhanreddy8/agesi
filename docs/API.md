# API Documentation

## Authentication (`/api/auth/*`)

### POST `/api/auth/register`
- **Body**: `{ email, password, outlook_password, full_name, ...profile_fields }`
- **Response**: `{ success: true, user_id: 1 }`

### POST `/api/auth/login`
- **Body**: `{ email, password }`
- **Response**: `{ success: true, token: "jwt...", user: {...} }`

### POST `/api/auth/verify-email`
- **Body**: `{ token: "..." }`

## Form Submission (`/api/submit-form`)
- **Headers**: `Authorization: Bearer <token>`
- **Content-Type**: `multipart/form-data`
- **Body**:
  - `pdf`: File
  - `data`: JSON string `{ form_url, leave_start_date, leave_end_date, reason }`

## Profile (`/api/profile`)
- **GET**: Get user profile.
- **PUT**: Update profile fields.

## Automation Status (`/api/task-status/<task_id>`)
- **GET**: Check status of running automation.
