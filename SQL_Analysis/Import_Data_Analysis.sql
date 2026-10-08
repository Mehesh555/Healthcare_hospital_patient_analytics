USE healthcare_analytics;

TRUNCATE TABLE healthcare_staging;

SELECT COUNT(*) AS Total_Rows
FROM healthcare_staging;

-- local_infile is a MySQL setting that controls whether MySQL is allowed to load data from a file stored on your computer.
SHOW VARIABLES LIKE 'local_infile';

SET GLOBAL local_infile = 1;

-- MySql only allow specific folder
SHOW VARIABLES LIKE 'secure_file_priv';

SELECT @@secure_file_priv;

-- Import all 25,000 rows

LOAD DATA INFILE 'C:/ProgramData/MySQL/MySQL Server 8.0/Uploads/healthcare_hospital_patient_analytics.csv'
INTO TABLE healthcare_staging
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    Patient_ID,
    Visit_ID,
    Visit_Date,
    Age,
    Gender,
    City,
    Department,
    Doctor,
    Diagnosis,
    Admission_Type,
    Admission_Date,
    Discharge_Date,
    Length_of_Stay_Days,
    Waiting_Time_Min,
    Treatment_Cost_INR,
    Insurance_Type,
    Insurance_Coverage_INR,
    Patient_Payment_INR,
    Patient_Satisfaction,
    Readmission,
    Followup_Required,
    Outcome
);

SELECT COUNT(*) AS Total_Rows
FROM healthcare_staging;

SELECT *
FROM healthcare_staging
LIMIT 10;

-- Populate departments
INSERT INTO departments (Department_Name)
SELECT DISTINCT Department
FROM healthcare_staging;

SELECT *
FROM departments;

-- Populate doctors
INSERT INTO doctors (Doctor_Name, Department)
SELECT DISTINCT Doctor, Department
FROM healthcare_staging;

SELECT *
FROM doctors;

-- Populate patients
INSERT INTO patients
(
    Patient_ID,
    Age,
    Gender,
    City
)
SELECT DISTINCT
    Patient_ID,
    Age,
    Gender,
    City
FROM healthcare_staging;

-- Populate visits
INSERT INTO visits
(
    Visit_ID,
    Patient_ID,
    Doctor_ID,
    Department_ID,
    Visit_Date,
    Diagnosis,
    Admission_Type,
    Waiting_Time_Min,
    Patient_Satisfaction,
    Readmission,
    Followup_Required,
    Outcome
)
SELECT
    s.Visit_ID,
    s.Patient_ID,
    d.Doctor_ID,
    dep.Department_ID,
    s.Visit_Date,
    s.Diagnosis,
    s.Admission_Type,
    s.Waiting_Time_Min,
    s.Patient_Satisfaction,
    s.Readmission,
    s.Followup_Required,
    s.Outcome
FROM healthcare_staging s
JOIN doctors d
    ON s.Doctor = d.Doctor_Name
   AND s.Department = d.Department
JOIN departments dep
    ON s.Department = dep.Department_Name;
    
-- Populate admissions
INSERT INTO admissions
(
    Visit_ID,
    Admission_Date,
    Discharge_Date,
    Length_of_Stay_Days
)
SELECT
    Visit_ID,
    Admission_Date,
    Discharge_Date,
    Length_of_Stay_Days
FROM healthcare_staging;

-- Populate payments
INSERT INTO payments
(
    Visit_ID,
    Treatment_Cost_INR,
    Insurance_Type,
    Insurance_Coverage_INR,
    Patient_Payment_INR
)
SELECT
    Visit_ID,
    Treatment_Cost_INR,
    Insurance_Type,
    Insurance_Coverage_INR,
    Patient_Payment_INR
FROM healthcare_staging;

-- Validate your database
SELECT COUNT(*) FROM patients;

SELECT COUNT(*) FROM doctors;

SELECT COUNT(*) FROM departments;

SELECT COUNT(*) FROM visits;

SELECT COUNT(*) FROM admissions;

SELECT COUNT(*) FROM payments;

-- Start SQL analysis
-- Now your project becomes a SQL + Tableau analytics project.

-- Query 1 — Total patients
SELECT COUNT(*) AS Total_Visits
FROM visits;

-- Query 2 — Total visits
SELECT COUNT(*) AS Total_Visits
FROM visits;

-- Query 3 — Patients by department
SELECT
    d.Department_Name,
    COUNT(*) AS Total_Visits
FROM visits v
JOIN departments d
    ON v.Department_ID = d.Department_ID
GROUP BY d.Department_Name
ORDER BY Total_Visits DESC;

-- Query 4 — Average waiting time
SELECT
    d.Department_Name,
    AVG(v.Waiting_Time_Min) AS Avg_Waiting_Time
FROM visits v
JOIN departments d
    ON v.Department_ID = d.Department_ID
GROUP BY d.Department_Name
ORDER BY Avg_Waiting_Time DESC;

-- Query 5 — Revenue by department
SELECT
    d.Department_Name,
    SUM(p.Treatment_Cost_INR) AS Total_Revenue
FROM payments p
JOIN visits v
    ON p.Visit_ID = v.Visit_ID
JOIN departments d
    ON v.Department_ID = d.Department_ID
GROUP BY d.Department_Name
ORDER BY Total_Revenue DESC;

-- Query 6 — Admission type
SELECT
    Admission_Type,
    COUNT(*) AS Total_Admissions
FROM visits
GROUP BY Admission_Type
ORDER BY Total_Admissions DESC;

-- Query 7 — Diagnosis analysis
SELECT
    Diagnosis,
    COUNT(*) AS Cases
FROM visits
GROUP BY Diagnosis
ORDER BY Cases DESC;

-- Query 8 — Average satisfaction
SELECT
    d.Department_Name,
    ROUND(AVG(v.Patient_Satisfaction), 2) AS Avg_Satisfaction
FROM visits v
JOIN departments d
    ON v.Department_ID = d.Department_ID
GROUP BY d.Department_Name
ORDER BY Avg_Satisfaction DESC;

-- Query 9 — Readmission rate
SELECT
    d.Department_Name,
    COUNT(CASE WHEN v.Readmission = 'Yes' THEN 1 END) AS Readmissions,
    COUNT(*) AS Total_Visits,
    ROUND(
        COUNT(CASE WHEN v.Readmission = 'Yes' THEN 1 END)
        * 100.0 / COUNT(*),
        2
    ) AS Readmission_Rate
FROM visits v
JOIN departments d
    ON v.Department_ID = d.Department_ID
GROUP BY d.Department_Name;

-- Query 10 — CTE
WITH department_stats AS
(
    SELECT
        Department_ID,
        AVG(Waiting_Time_Min) AS Avg_Waiting
    FROM visits
    GROUP BY Department_ID
)
SELECT
    d.Department_Name,
    ROUND(ds.Avg_Waiting, 2) AS Avg_Waiting
FROM department_stats ds
JOIN departments d
    ON ds.Department_ID = d.Department_ID
ORDER BY Avg_Waiting DESC;

-- Window function
WITH revenue_data AS
(
    SELECT
        d.Department_Name,
        SUM(p.Treatment_Cost_INR) AS Revenue
    FROM payments p
    JOIN visits v
        ON p.Visit_ID = v.Visit_ID
    JOIN departments d
        ON v.Department_ID = d.Department_ID
    GROUP BY d.Department_Name
)

SELECT
    Department_Name,
    Revenue,
    RANK() OVER (ORDER BY Revenue DESC) AS Revenue_Rank
FROM revenue_data;