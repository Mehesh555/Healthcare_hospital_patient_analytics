CREATE DATABASE healthcare_analytics;

USE healthcare_analytics;

# Design the database
-- Create patients table
CREATE TABLE patients (
    Patient_ID VARCHAR(20) PRIMARY KEY,
    Age INT,
    Gender VARCHAR(20),
    City VARCHAR(50)
);

-- Create doctors table
CREATE TABLE doctors (
    Doctor_ID INT AUTO_INCREMENT PRIMARY KEY,
    Doctor_Name VARCHAR(100),
    Department VARCHAR(100)
);

-- Create departments table
CREATE TABLE departments (
    Department_ID INT AUTO_INCREMENT PRIMARY KEY,
    Department_Name VARCHAR(100)
);

-- Create visits table
CREATE TABLE visits (
    Visit_ID VARCHAR(20) PRIMARY KEY,
    Patient_ID VARCHAR(20),
    Doctor_ID INT,
    Department_ID INT,
    Visit_Date DATE,
    Diagnosis VARCHAR(100),
    Admission_Type VARCHAR(50),
    Waiting_Time_Min INT,
    Patient_Satisfaction DECIMAL(3,1),
    Readmission VARCHAR(10),
    Followup_Required VARCHAR(10),
    Outcome VARCHAR(100),

    FOREIGN KEY (Patient_ID)
        REFERENCES patients(Patient_ID),

    FOREIGN KEY (Doctor_ID)
        REFERENCES doctors(Doctor_ID),

    FOREIGN KEY (Department_ID)
        REFERENCES departments(Department_ID)
);

-- Create admissions table
CREATE TABLE admissions (
    Admission_ID INT AUTO_INCREMENT PRIMARY KEY,
    Visit_ID VARCHAR(20),
    Admission_Date DATE,
    Discharge_Date DATE,
    Length_of_Stay_Days INT,

    FOREIGN KEY (Visit_ID)
        REFERENCES visits(Visit_ID)
);

-- Create payments table
CREATE TABLE payments (
    Payment_ID INT AUTO_INCREMENT PRIMARY KEY,
    Visit_ID VARCHAR(20),
    Treatment_Cost_INR DECIMAL(12,2),
    Insurance_Type VARCHAR(50),
    Insurance_Coverage_INR DECIMAL(12,2),
    Patient_Payment_INR DECIMAL(12,2),

    FOREIGN KEY (Visit_ID)
        REFERENCES visits(Visit_ID)
);

-- Create healthcare_staging Table
CREATE TABLE healthcare_staging (
    Patient_ID VARCHAR(20),
    Visit_ID VARCHAR(20),
    Visit_Date DATE,
    Age INT,
    Gender VARCHAR(20),
    City VARCHAR(50),
    Department VARCHAR(100),
    Doctor VARCHAR(100),
    Diagnosis VARCHAR(100),
    Admission_Type VARCHAR(50),
    Admission_Date DATE,
    Discharge_Date DATE,
    Length_of_Stay_Days INT,
    Waiting_Time_Min INT,
    Treatment_Cost_INR DECIMAL(12,2),
    Insurance_Type VARCHAR(50),
    Insurance_Coverage_INR DECIMAL(12,2),
    Patient_Payment_INR DECIMAL(12,2),
    Patient_Satisfaction DECIMAL(3,1),
    Readmission VARCHAR(10),
    Followup_Required VARCHAR(10),
    Outcome VARCHAR(100)
);
