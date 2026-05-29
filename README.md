User Journey Funnel Analysis
An end-to-end data analytics project analysing e-commerce user drop-off across a 4-stage conversion funnel — identifying where users are lost and why, using Python, SQL, and an interactive Plotly Dash dashboard.

📊 Project Overview
This project analyses the behaviour of 15,000 e-commerce users across a 4-stage funnel:
Visit → Signup → Cart → Purchase
The goal was to identify where and why users drop off, segment behaviour by device, city, and traffic source, and surface prioritised recommendations to improve conversion rates.

🔑 Key Findings
Mobile converts 40% below desktop despite accounting for 55% of total traffic — the single biggest revenue leakage point
Significant drop-off identified between the Cart and Purchase stages across all devices
Chi-square significance testing confirmed device type as a statistically significant driver of conversion differences
Automated recommendations engine surfaced the top 3 prioritised business fixes based on live data


🛠️ Tech Stack
ToolUsagePython (pandas, NumPy)Data cleaning, transformation, analytics engineSQLSegmented conversion queries by device, city, traffic sourcePlotly DashInteractive dashboard with live recommendationsSciPyChi-square A/B significance testing

📁 Project Structure

├── sql/              # SQL queries for funnel segmentation

├── dashboard/        # Plotly Dash app and layout

├── utils/            # Helper functions and analytics engine

└── .gitignore

🚀 How to Run
bash# Clone the repo
git clone https://github.com/dhruvdedhia/User-Journey-Funnel-Analysis.git
cd User-Journey-Funnel-Analysis

# Install dependencies
pip install -r requirements.txt

# Run the dashboard
python dashboard/app.py

💡 Business Impact

Identified mobile UX as the primary conversion bottleneck — actionable insight for product and engineering teams
Automated recommendations engine removes manual analysis, enabling faster decision-making
Statistical validation ensures findings are reliable, not coincidental


👤 Author
Dhruv Dedhia — Data Analyst | MSc Data Science, University of Surrey
