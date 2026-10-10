# 🎓 Student Exam Performance Dashboard

Interactive Streamlit dashboard analysing the exam results of **100,000 students** (44 columns) from the
[Student Exam Performance & Success Dataset](https://www.kaggle.com/datasets/mobeenfatimah/student-exam-performance-and-success-dataset).

## Pages
- **Overview**: KPIs (avg score, pass/fail rate, score change, study hours, attendance) and score distributions
- **Study Insights**: fail rate by study hours, attendance, sleep and exam anxiety, plus the effect of exam difficulty
- **Background**: income, school type, parent education, urban/rural, gender, internet access and tuition vs. outcomes
- **Risk and Support**: at-risk students (downloadable CSV) and recommendations

## Key findings
- Average exam score is about 62, and the fail rate is 22.6% (fail = score below 50)
- Previous score, study hours, attendance and exam difficulty are the strongest drivers of failure
- Family income, school type, parent education and urban/rural have only a small effect

## Run locally
    pip install -r requirements.txt
    streamlit run app.py

The file `student_exam_performance.csv` must be in the same folder as `app.py`.

## Author
Mina Nassim
