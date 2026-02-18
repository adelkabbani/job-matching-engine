# HyperApply - Verification Guide

This guide will help you run the application and verify that the job matching, shortlisting, and document generation features are working correctly.

## 1. Start the Backend (API)

The backend handles all the logic, database connections, and AI processing.

1.  Open a **Terminal** (Command Prompt or PowerShell).
2.  Navigate to the backend directory:
    ```powershell
    cd "d:\website@Antigravity\jops auto apply\backend"
    ```
3.  Run the server:
    ```powershell
    python main.py
    ```
    *Alternatively, if you prefer:* `uvicorn main:app --reload`

**Success Indicator:**
You should see output indicating the server is running at `http://127.0.0.1:8000`.

---

## 2. Start the Frontend (Dashboard)

The frontend is the user interface where you interact with the system.

1.  Open a **New Terminal** window (keep the backend running in the first one).
2.  Navigate to the frontend directory:
    ```powershell
    cd "d:\website@Antigravity\jops auto apply\frontend"
    ```
3.  Run the development server:
    ```powershell
    npm run dev
    ```

**Success Indicator:**
You should see output saying `Ready in ...` and `Local: http://localhost:3000`.

---

## 3. Verify the Workflow (Step-by-Step)

Follow these steps to confirm everything is working as expected.

### Step A: Access the Dashboard
1.  Open your browser (Chrome/Edge).
2.  Go to: [http://localhost:3000/dashboard](http://localhost:3000/dashboard)
    *(Or use your local IP if testing from another device: `http://192.168.178.152:3000/dashboard`)*

### Step B: Add a Job
1.  Locate the **"Add Job by URL"** section at the top.
2.  Paste a job URL (e.g., a LinkedIn job or any URL for testing):
    `https://www.ycombinator.com/companies/growthbook/jobs/L98T12F-staff-software-engineer-growth`
3.  Click **"Add Job"**.
4.  **Check:** The job should appear in the list below after a few seconds.

### Step C: Shortlist the Job
1.  Find the job card you just added.
2.  Click the **Star icon** (Shortlist button) on the card.
3.  **Check:** The card background should turn greenish/yellow, and a **"Shortlisted"** badge should appear.
4.  **Check:** A new button **"CV & Cover Letter"** should appear on the card.

### Step D: Generate Documents
1.  Click the **"CV & Cover Letter"** button.
2.  **Tailor CV:** Click **"Tailor Now"**. Wait for the text to generate in the left box.
3.  **Draft Cover Letter:** Click **"Draft Pro"**. Wait for the text to generate in the right box.
4.  **Check:** You should see text in both boxes.

### Step E: Download
1.  Click **"Finalize & Save Docx"** at the bottom of the modal.
2.  Wait a moment.
3.  **Check:** A green **"Download Final"** button should appear.
4.  Click it to download your zip file containing the CV and Cover Letter.

---

## 4. Troubleshooting

*   **"Add Job" button is disabled:** Make sure you have pasted a URL into the input field.
*   **"CV & Cover Letter" button is missing:** Make sure you have clicked the **Star icon** to shortlist the job first.
*   **Network Errors:** Ensure both Backend (port 8000) and Frontend (port 3000) terminals are running and have not crashed.
