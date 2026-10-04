# RetailSense version 3 — complete website

## Easiest start (recommended)

1. Stop the old server: Ctrl+C in the old terminal.
2. Extract the ENTIRE new ZIP into a fresh folder.
3. Double-click **START_WINDOWS.bat**, next to the RetailSense folder.
4. Allow dependency installation to finish. Keep the terminal open.
5. Open http://127.0.0.1:5000. Press Ctrl+Shift+R if old styling appears.
6. Click Get started, create a local account, then load demo or import CSV.

Do not run the old `..\.venv` command from a new extraction. The launcher creates a correct environment inside the new project folder.

## Keep previous files

Keep your old project folder as a backup. V3 introduces account-specific databases; it does not automatically attach the old shared database to an account. Import your original transaction CSV again after signing up, or load the demo. Customer exports are summaries and cannot be imported as transaction data. No old files are deleted by this package.

## What's included

Home page → Signup / Login → Account workspace → Data import → Analytics → Customer profiles → ML training → Export → Logout.

- Responsive landing page with product preview, features, workflow, FAQs and working calls to action.
- Signup/login with hashed passwords, signed sessions and basic login throttling.
- Each account has its own database and model results.
- Dark/light analytics workspace, date/country filters, SVG revenue chart, business observations and customer drill-down.

This is a complete local portfolio website. It has not been publicly deployed. Email verification, password reset and production cloud infrastructure are not included.
