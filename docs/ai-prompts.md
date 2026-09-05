# AI prompts

AI was used as an implementation, debugging and verification assistant. I remained responsible for deciding what to change, running the code, checking the deployed system, and accepting/rejecting suggestions.

## 1. Understanding the assignment and implementation order

### Prompt
> “i want to make sure the whole system is working and then deploy it”

### What I got
A verification-first approach: validate backend behaviour, then deploy the backend/database, then deploy the frontend and run an end-to-end check.

### What I corrected
I did not treat a passing local server as proof of a working deployment. I added a production API test and then tested the deployed browser application separately.

## 2. Repository and Git workflow

### Prompt
> “should i push the current code to github then you see everything from there i don't want to do manual testing”

### What I got
A recommendation to use the public repository as the source of truth and automate verification rather than manually exercising every endpoint.

### What I corrected
I kept the production deployment and repository separate from local secrets, and I only committed the files that were intended for deployment/documentation.

## 3. Automated API verification

### Prompt
> “i want to make sure the whole system is working and then deploy it”

### What I got
A production-oriented `test_api.py` that exercised authentication, classes, sessions, members, bookings, waitlist promotion, history, reports, recurring sessions and archive/restore.

### What I corrected
The first test run stopped because it assumed a room already existed:

`RuntimeError: No rooms exist; seed a room before continuing.`

I seeded the required reference data and reran the same verification. The final run completed with **27 passed, 0 failed**. Instructor-specific authorization checks were optional in that runner and were skipped because an instructor password was not supplied to the script.

## 4. Supabase and production database setup

### Prompt
> “how do i create supabase”

### What I got
Guidance for creating a hosted PostgreSQL database and moving the backend connection string into environment variables.

### What I corrected
The first connection attempt used a hostname that could not be resolved. I checked the Supabase connection details and replaced the invalid connection configuration with the working database URL before creating the tables.

## 5. Render deployment

### Prompt
> “let's do this then deploy further and finish this today”

### What I got
A staged deployment plan: database first, backend second, frontend third, then production verification.

### What I corrected
The backend's first production deployment timed out during port detection. Instead of changing application behaviour blindly, I verified the same Uvicorn command locally with an explicit port. The local server successfully listened on `0.0.0.0:10000`, after which the Render configuration was corrected and the backend deployment succeeded.

## 6. Frontend integration / CORS

### Prompt
> “swagger page appersa but stiill failed to fetch”

### What I got
A diagnosis path separating backend availability from browser-to-API communication: verify the frontend API base URL, check the browser Network/Console errors, and allow the deployed frontend origin in CORS.

### What I corrected
The frontend was configured to call the deployed API URL, and the backend CORS allow-list was updated to include `https://busy-class-booking.onrender.com`. The frontend was redeployed and the production login/dashboard flow then worked.

## 7. Documentation

### Prompt
> “this is the zip they provivded us which has require ments and what to submit now craete that documentation for our deployed project then we will submit”

### What I got
A documentation pass organized around the exact five files requested by the assignment: architecture, schema, plan, decisions and AI prompts, plus the submission checklist.

### What I corrected
The documentation was grounded in the actual repository structure and deployed behaviour rather than copying the assignment stubs unchanged. The final documents describe the deployed Render frontend/backend, Supabase PostgreSQL, the booking transaction design, and the production verification result.
