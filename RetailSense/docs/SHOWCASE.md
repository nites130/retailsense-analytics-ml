# Showcase checklist

## Before publishing

Run the app, understand each module, import real data if making real-data claims and save the actual evaluation results. Create 3 screenshots: Overview, Customers, Prediction lab. Record a 60–90 second walkthrough. Explicitly label any synthetic demo results. Do not claim that this project increased real revenue or achieved unmeasured outcomes. Acknowledge AI assistance if describing your development process and explain what you personally implemented, tested or changed.

## GitHub (when you are ready)

Suggested repository: `retailsense-analytics-ml`.

From the folder containing app.py:

```bash
git init
git add .
git status
git commit -m "Build RetailSense analytics and repeat-purchase prediction app"
git branch -M main
```

Review `git status` before committing: no .venv, database, customer CSV or credentials. Create an empty GitHub repository under your own account, then use its exact URL:

```bash
git remote add origin YOUR_REPOSITORY_URL
git push -u origin main
```

Replace YOUR_REPOSITORY_URL; don't paste it literally. No repository has been created or pushed for you. Add your screenshots to docs/screenshots and link them in README after capturing them.

## LinkedIn draft — personalise after testing

I’m sharing RetailSense, a full-stack retail analytics and customer purchase prediction portfolio project.

The app combines a sales dashboard, customer segmentation and a machine-learning workflow that estimates repeat purchases within 30 days of the dataset cutoff.

Stack: Python, Pandas, SQL/SQLite, Flask, scikit-learn, HTML, CSS and JavaScript.

My focus was understanding data cleaning, feature engineering and evaluation on later time periods, rather than relying on a random train/test split.

[State whether your screenshots use synthetic demo data or the UCI dataset.]
[Add one actual finding and one honest limitation after analysis.]

GitHub: [your repository link]

#DataAnalytics #DataScience #Python #MachineLearning #PortfolioProject

## Resume — use only after running and understanding the work

**RetailSense — Retail Analytics & Repeat-Purchase Prediction**
Python | SQL | Flask | Pandas | scikit-learn | JavaScript

- Developed a full-stack retail analytics application with CSV validation, SQLite persistence, interactive sales dashboards and customer segmentation.
- Compared Logistic Regression and Random Forest using temporal validation, with a later test window and baseline comparison for 30-day repeat-purchase prediction.
- Added searchable customer insights, prediction exports and automated integration tests.

Add measured dataset size and test metrics only after your own real-data run. Keep synthetic demo evaluation clearly labelled. Do not list Power BI, React, cloud deployment: those are not implemented here. Version 3 includes local signup/login and account-isolated SQLite workspaces.

## Explain it in an interview

1. Why is gross revenue different from profit and net revenue?
2. Which records were excluded, and how might that bias the result?
3. Why are features computed before a cutoff and labels after it?
4. What do precision, recall, F1 and the baseline tell you?
5. Why does customer inactivity not automatically mean churn?
6. What would you add before using the app with real business users?
