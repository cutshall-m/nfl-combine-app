#Site link: https://nfl-combine.streamlit.app/

# 🏈 NFL Combine Performance & Impact on Draft Position

An interactive data application that explores how college athletes' NFL Combine drill performances impact their NFL Draft outcomes. Built with Python, MySQL, and Streamlit, this project models draft projections using linear regression weights and provides historical draft and combine query capabilities.

---

## 📌 Project Architecture

* **Frontend / UI**: Streamlit (Python)
* **Backend Database**: Cloud-hosted MySQL Database (Aiven.io)
* **Data Visualizations**: Streamlit Dataframes & Interactive Controls
* **Deployment**: Streamlit Community Cloud

---

## 🗄️ Database Schema & Structure

The database consists of relational entities designed to handle lookups, player profiles, athletic testing, and draft positioning:

* `player`: Central entity holding athlete information, school, and position details.
* `position`: Lookup table for position abbreviations and full descriptions.
* `conference`: Lookup table categorizing colleges and their respective conferences/tiers.
* `combine_result`: Stores performance metrics (40-yard dash, vertical jump, bench press, broad jump, 3-cone drill, 20-yard shuttle).
* `draft_result`: Tracks draft selection year, round, pick number, and drafting franchise.
* `attribute_coefficients`: Contains position-specific regression weights and intercepts used to calculate projected draft positions.

---

## 🚀 Features

1. **Draft Round Predictor**: 
   * Select an athletic position to retrieve regression weights and dynamically calculate estimated draft positioning based on user-inputted drill scores.
2. **Historical Draft Query**: 
   * Search draft results by year (2000–2026) to view player selections alongside their respective combine metrics.
3. **Athletic Outlier Identification**: 
   * Instantly query and isolate elite top-tier athletic drill performances against draft selection outcomes.

---

## 🛠️ Local Setup & Installation

### Prerequisites
* Python 3.9+
* A running MySQL database instance

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/nfl-combine-app.git](https://github.com/YOUR_USERNAME/nfl-combine-app.git)
cd nfl-combine-app
