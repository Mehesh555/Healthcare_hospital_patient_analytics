from flask import Flask, request, redirect, url_for, render_template_string, flash
import mysql.connector
from mysql.connector import Error
from datetime import datetime


# ============================================================
# FLASK APPLICATION
# ============================================================

app = Flask(__name__)

# Used for Flask flash messages
app.secret_key = "careflow_hospital_secret_key"


# ============================================================
# MYSQL DATABASE CONFIGURATION
# ============================================================

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "5551",
    "database": "healthcare_analytics"
}


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():

    try:

        connection = mysql.connector.connect(
            host=DB_CONFIG["host"],
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"]
        )

        return connection

    except Error as e:

        print("MySQL connection error:", e)

        return None


# ============================================================
# CREATE TABLE IF IT DOES NOT EXIST
# ============================================================

def create_table():

    connection = get_connection()

    if connection is None:
        return

    cursor = connection.cursor()

    query = """
    CREATE TABLE IF NOT EXISTS hospital_web_records (

        Record_ID INT AUTO_INCREMENT PRIMARY KEY,

        Patient_ID VARCHAR(50) NOT NULL,

        Patient_Name VARCHAR(100) NOT NULL,

        Age INT NOT NULL,

        Gender VARCHAR(20) NOT NULL,

        City VARCHAR(100),

        Department VARCHAR(100),

        Diagnosis VARCHAR(150),

        Admission_Type VARCHAR(50),

        Visit_Date DATE,

        Waiting_Time_Min INT,

        Length_of_Stay_Days INT,

        Patient_Satisfaction DECIMAL(3,2),

        Treatment_Cost_INR DECIMAL(12,2),

        Insurance_Type VARCHAR(100),

        Insurance_Coverage_INR DECIMAL(12,2),

        Patient_Payment_INR DECIMAL(12,2),

        Readmission_Flag VARCHAR(10),

        Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )
    """

    try:

        cursor.execute(query)

        connection.commit()

        print("hospital_web_records table checked successfully.")

    except Error as e:

        print("Table creation error:", e)

    finally:

        cursor.close()
        connection.close()


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():

    connection = get_connection()

    total_records = 0
    today_records = 0
    recent_records = []
    db_status = False

    if connection:

        db_status = True

        cursor = connection.cursor(dictionary=True)

        try:

            # Total website records
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM hospital_web_records
            """)

            result = cursor.fetchone()

            total_records = result["total"]


            # Records added today
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM hospital_web_records
                WHERE DATE(Created_At) = CURDATE()
            """)

            result = cursor.fetchone()

            today_records = result["total"]


            # Recent records
            cursor.execute("""
                SELECT
                    Record_ID,
                    Patient_ID,
                    Patient_Name,
                    Age,
                    Gender,
                    City,
                    Department,
                    Diagnosis,
                    Admission_Type,
                    Visit_Date,
                    Treatment_Cost_INR,
                    Patient_Satisfaction,
                    Created_At
                FROM hospital_web_records
                ORDER BY Record_ID DESC
                LIMIT 10
            """)

            recent_records = cursor.fetchall()

        except Error as e:

            print("Database error:", e)

        finally:

            cursor.close()
            connection.close()


    return render_template_string(
        HTML_TEMPLATE,
        total_records=total_records,
        today_records=today_records,
        recent_records=recent_records,
        db_status=db_status
    )


# ============================================================
# ADD PATIENT
# ============================================================

@app.route("/add_patient", methods=["POST"])
def add_patient():

    # --------------------------------------------------------
    # GET FORM DATA
    # --------------------------------------------------------

    patient_id = request.form.get("patient_id", "").strip()
    patient_name = request.form.get("patient_name", "").strip()
    age = request.form.get("age", "").strip()
    gender = request.form.get("gender", "").strip()

    city = request.form.get("city", "").strip()
    department = request.form.get("department", "").strip()
    diagnosis = request.form.get("diagnosis", "").strip()

    admission_type = request.form.get("admission_type", "").strip()

    visit_date = request.form.get("visit_date", "").strip()

    waiting_time = request.form.get("waiting_time", "").strip()
    length_of_stay = request.form.get("length_of_stay", "").strip()

    satisfaction = request.form.get("satisfaction", "").strip()

    treatment_cost = request.form.get("treatment_cost", "").strip()

    insurance_type = request.form.get("insurance_type", "").strip()

    insurance_coverage = request.form.get(
        "insurance_coverage", ""
    ).strip()

    patient_payment = request.form.get(
        "patient_payment", ""
    ).strip()

    readmission = request.form.get("readmission", "").strip()


    # --------------------------------------------------------
    # BASIC VALIDATION
    # --------------------------------------------------------

    if not patient_id:
        flash("Patient ID is required.", "error")
        return redirect(url_for("index"))

    if not patient_name:
        flash("Patient name is required.", "error")
        return redirect(url_for("index"))

    if not age:
        flash("Age is required.", "error")
        return redirect(url_for("index"))

    if not gender:
        flash("Gender is required.", "error")
        return redirect(url_for("index"))


    # --------------------------------------------------------
    # CONVERT NUMERIC VALUES
    # --------------------------------------------------------

    try:

        age = int(age)

        waiting_time = int(waiting_time or 0)

        length_of_stay = int(length_of_stay or 0)

        satisfaction = float(satisfaction or 0)

        treatment_cost = float(treatment_cost or 0)

        insurance_coverage = float(
            insurance_coverage or 0
        )

        patient_payment = float(
            patient_payment or 0
        )

    except ValueError:

        flash(
            "Please enter valid numeric values.",
            "error"
        )

        return redirect(url_for("index"))


    # --------------------------------------------------------
    # MYSQL CONNECTION
    # --------------------------------------------------------

    connection = get_connection()

    if connection is None:

        flash(
            "Unable to connect to MySQL.",
            "error"
        )

        return redirect(url_for("index"))


    cursor = connection.cursor()


    # --------------------------------------------------------
    # CHECK DUPLICATE PATIENT ID
    # --------------------------------------------------------

    try:

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM hospital_web_records
            WHERE Patient_ID = %s
            """,
            (patient_id,)
        )

        duplicate = cursor.fetchone()[0]

        if duplicate > 0:

            flash(
                f"Patient ID {patient_id} already exists.",
                "error"
            )

            cursor.close()
            connection.close()

            return redirect(url_for("index"))


        # ----------------------------------------------------
        # INSERT NEW PATIENT
        # ----------------------------------------------------

        query = """
        INSERT INTO hospital_web_records
        (
            Patient_ID,
            Patient_Name,
            Age,
            Gender,
            City,
            Department,
            Diagnosis,
            Admission_Type,
            Visit_Date,
            Waiting_Time_Min,
            Length_of_Stay_Days,
            Patient_Satisfaction,
            Treatment_Cost_INR,
            Insurance_Type,
            Insurance_Coverage_INR,
            Patient_Payment_INR,
            Readmission_Flag
        )

        VALUES
        (
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s
        )
        """


        values = (

            patient_id,
            patient_name,
            age,
            gender,
            city,
            department,
            diagnosis,
            admission_type,
            visit_date if visit_date else None,
            waiting_time,
            length_of_stay,
            satisfaction,
            treatment_cost,
            insurance_type,
            insurance_coverage,
            patient_payment,
            readmission
        )


        cursor.execute(query, values)

        connection.commit()


        # ----------------------------------------------------
        # SUCCESS MESSAGE
        # ----------------------------------------------------

        flash(
            f"Patient {patient_id} added successfully to MySQL.",
            "success"
        )


    except Error as e:

        connection.rollback()

        print("Insert error:", e)

        flash(
            f"Database error: {e}",
            "error"
        )


    finally:

        cursor.close()
        connection.close()


    return redirect(url_for("index"))


# ============================================================
# SEARCH PATIENT
# ============================================================

@app.route("/search")
def search():

    patient_id = request.args.get(
        "patient_id",
        ""
    ).strip()

    connection = get_connection()

    records = []

    if connection:

        cursor = connection.cursor(
            dictionary=True
        )

        try:

            cursor.execute(
                """
                SELECT *
                FROM hospital_web_records
                WHERE Patient_ID LIKE %s
                ORDER BY Record_ID DESC
                """,
                (f"%{patient_id}%",)
            )

            records = cursor.fetchall()

        except Error as e:

            print("Search error:", e)

        finally:

            cursor.close()
            connection.close()


    return render_template_string(
        SEARCH_TEMPLATE,
        records=records,
        patient_id=patient_id
    )


# ============================================================
# HTML TEMPLATE
# ============================================================

HTML_TEMPLATE = """

<!DOCTYPE html>

<html lang="en">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>CareFlow Hospital</title>


<style>

/* =========================================================
   GLOBAL
   ========================================================= */

* {
    box-sizing: border-box;
}

body {

    margin: 0;

    font-family:
        "Segoe UI",
        Arial,
        sans-serif;

    background:
        linear-gradient(
            135deg,
            #eef7ff,
            #f8fbff
        );

    color: #12365a;

}


/* =========================================================
   HEADER
   ========================================================= */

.header {

    background:
        linear-gradient(
            110deg,
            #0b3157,
            #087c9c,
            #13a8b5
        );

    color: white;

    padding: 22px 6%;

    display: flex;

    justify-content: space-between;

    align-items: center;

    box-shadow:
        0 5px 20px
        rgba(0,0,0,0.15);

}


.logo-area {

    display: flex;

    align-items: center;

    gap: 18px;

}


.logo {

    width: 58px;

    height: 58px;

    border-radius: 16px;

    background:
        rgba(255,255,255,0.15);

    display: flex;

    align-items: center;

    justify-content: center;

    font-size: 30px;

}


.logo-text h1 {

    margin: 0;

    font-size: 28px;

}


.logo-text p {

    margin: 5px 0 0;

    opacity: 0.9;

}


.status {

    background:
        rgba(255,255,255,0.12);

    border:
        1px solid
        rgba(255,255,255,0.3);

    padding: 12px 20px;

    border-radius: 30px;

}


.status-dot {

    display: inline-block;

    width: 10px;

    height: 10px;

    background: #42e695;

    border-radius: 50%;

    margin-right: 8px;

}


/* =========================================================
   MAIN
   ========================================================= */

.container {

    width: 90%;

    max-width: 1500px;

    margin: 40px auto;

}


.page-title h2 {

    font-size: 36px;

    margin-bottom: 8px;

}


.page-title p {

    color: #65809b;

    font-size: 17px;

}


/* =========================================================
   ALERT
   ========================================================= */

.alert {

    padding: 16px 22px;

    border-radius: 14px;

    margin: 25px 0;

    font-weight: 600;

}


.alert.success {

    background: #e7fff4;

    border: 1px solid #a7efd0;

    color: #08734d;

}


.alert.error {

    background: #fff0f0;

    border: 1px solid #ffc0c0;

    color: #b42318;

}


/* =========================================================
   KPI CARDS
   ========================================================= */

.kpi-container {

    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 20px;

    margin: 25px 0;

}


.kpi {

    background: white;

    border: 1px solid #dce8f3;

    border-radius: 20px;

    padding: 25px;

    box-shadow:
        0 8px 25px
        rgba(20,80,130,0.08);

}


.kpi-icon {

    font-size: 30px;

}


.kpi h3 {

    font-size: 30px;

    margin: 10px 0 3px;

}


.kpi p {

    margin: 0;

    color: #7188a0;

}


/* =========================================================
   FORM CARD
   ========================================================= */

.form-card {

    background: white;

    border-radius: 24px;

    box-shadow:
        0 12px 40px
        rgba(25,75,110,0.10);

    border: 1px solid #dce8f3;

    overflow: hidden;

}


.form-header {

    padding: 28px 32px;

    border-bottom:
        1px solid #e0eaf3;

    display: flex;

    justify-content: space-between;

    align-items: center;

}


.form-header h2 {

    margin: 0;

}


.badge {

    background: #e8f5ff;

    color: #0873a6;

    padding: 10px 18px;

    border-radius: 25px;

    font-weight: 700;

}


/* =========================================================
   SECTION
   ========================================================= */

.section {

    padding: 28px 32px;

}


.section-title {

    display: flex;

    align-items: center;

    gap: 12px;

    margin-bottom: 25px;

    font-size: 19px;

    font-weight: 700;

}


.number {

    width: 36px;

    height: 36px;

    border-radius: 10px;

    background: #0c4778;

    color: white;

    display: flex;

    align-items: center;

    justify-content: center;

}


/* =========================================================
   FORM GRID
   ========================================================= */

.form-grid {

    display: grid;

    grid-template-columns:
        repeat(3, 1fr);

    gap: 20px;

}


.field {

    display: flex;

    flex-direction: column;

}


.field label {

    font-weight: 700;

    margin-bottom: 8px;

    color: #173c60;

}


.field label span {

    color: #e23b3b;

}


input,
select {

    width: 100%;

    padding: 14px 15px;

    border:
        1px solid #cbdbea;

    border-radius: 10px;

    background: #fbfdff;

    font-size: 15px;

    color: #163d60;

    outline: none;

    transition: 0.2s;

}


input:focus,
select:focus {

    border-color: #08a4bd;

    box-shadow:
        0 0 0 4px
        rgba(8,164,189,0.10);

}


/* =========================================================
   BUTTONS
   ========================================================= */

.buttons {

    padding: 25px 32px;

    background: #f7fbff;

    border-top:
        1px solid #e1ebf3;

    display: flex;

    gap: 15px;

}


.btn {

    border: none;

    padding: 15px 30px;

    border-radius: 10px;

    font-size: 16px;

    font-weight: 700;

    cursor: pointer;

}


.btn-primary {

    color: white;

    background:
        linear-gradient(
            100deg,
            #0b4d83,
            #079bb4
        );

}


.btn-secondary {

    color: #31516d;

    background: #e8f0f7;

}


/* =========================================================
   RECENT RECORDS
   ========================================================= */

.records {

    margin-top: 35px;

    background: white;

    border-radius: 20px;

    padding: 25px;

    border: 1px solid #dce8f3;

    overflow-x: auto;

}


.records h2 {

    margin-top: 0;

}


table {

    width: 100%;

    border-collapse: collapse;

    min-width: 1100px;

}


th {

    background: #0d416c;

    color: white;

    padding: 13px;

    text-align: left;

}


td {

    padding: 13px;

    border-bottom:
        1px solid #e8eef4;

}


tr:hover {

    background: #f3faff;

}


/* =========================================================
   SEARCH
   ========================================================= */

.search-box {

    margin-top: 30px;

    background: white;

    padding: 20px;

    border-radius: 18px;

    border: 1px solid #dce8f3;

}


.search-form {

    display: flex;

    gap: 10px;

}


.search-form input {

    max-width: 400px;

}


/* =========================================================
   RESPONSIVE
   ========================================================= */

@media(max-width: 1000px) {

    .form-grid {

        grid-template-columns:
            repeat(2, 1fr);

    }

    .kpi-container {

        grid-template-columns:
            1fr;

    }

}


@media(max-width: 650px) {

    .header {

        flex-direction: column;

        gap: 20px;

        align-items: flex-start;

    }

    .form-grid {

        grid-template-columns:
            1fr;

    }

    .container {

        width: 94%;

    }

}

</style>

</head>


<body>


<!-- ======================================================
     HEADER
     ====================================================== -->

<header class="header">

    <div class="logo-area">

        <div class="logo">
            🏥
        </div>

        <div class="logo-text">

            <h1>
                CareFlow Hospital
            </h1>

            <p>
                Patient Management & Analytics System
            </p>

        </div>

    </div>


    <div class="status">

        <span class="status-dot"></span>

        {% if db_status %}
            MySQL Database Connected
        {% else %}
            MySQL Disconnected
        {% endif %}

    </div>

</header>



<!-- ======================================================
     MAIN
     ====================================================== -->

<main class="container">


    <div class="page-title">

        <h2>
            New Patient Registration
        </h2>

        <p>
            Enter patient visit information and
            store it directly in the hospital
            analytics database.
        </p>

    </div>



    <!-- ==================================================
         FLASH MESSAGES
         ================================================== -->

    {% with messages = get_flashed_messages(
        with_categories=true
    ) %}

        {% if messages %}

            {% for category, message in messages %}

                <div class="alert {{ category }}">

                    {% if category == "success" %}
                        ✓
                    {% else %}
                        ⚠
                    {% endif %}

                    {{ message }}

                </div>

            {% endfor %}

        {% endif %}

    {% endwith %}



    <!-- ==================================================
         KPI
         ================================================== -->

    <div class="kpi-container">


        <div class="kpi">

            <div class="kpi-icon">
                👥
            </div>

            <h3>
                {{ total_records }}
            </h3>

            <p>
                Website Records in MySQL
            </p>

        </div>


        <div class="kpi">

            <div class="kpi-icon">
                📅
            </div>

            <h3>
                {{ today_records }}
            </h3>

            <p>
                Records Added Today
            </p>

        </div>


        <div class="kpi">

            <div class="kpi-icon">
                📊
            </div>

            <h3>
                Tableau
            </h3>

            <p>
                Ready for dashboard refresh
            </p>

        </div>


    </div>



    <!-- ==================================================
         FORM
         ================================================== -->

    <div class="form-card">


        <div class="form-header">

            <div>

                <h2>
                    Patient & Visit Information
                </h2>

                <p>
                    Complete the fields below to create
                    a new hospital record.
                </p>

            </div>


            <div class="badge">

                18 Data Fields

            </div>

        </div>



        <form
            method="POST"
            action="/add_patient"
        >


            <!-- ==========================================
                 PATIENT INFORMATION
                 ========================================== -->

            <div class="section">

                <div class="section-title">

                    <div class="number">
                        01
                    </div>

                    Patient Identification

                </div>


                <div class="form-grid">


                    <div class="field">

                        <label>
                            Patient ID <span>*</span>
                        </label>

                        <input
                            type="text"
                            name="patient_id"
                            placeholder="e.g. P025001"
                            required
                        >

                    </div>


                    <div class="field">

                        <label>
                            Patient Name <span>*</span>
                        </label>

                        <input
                            type="text"
                            name="patient_name"
                            placeholder="e.g. Rahul Kumar"
                            required
                        >

                    </div>


                    <div class="field">

                        <label>
                            Age <span>*</span>
                        </label>

                        <input
                            type="number"
                            name="age"
                            min="0"
                            max="120"
                            placeholder="e.g. 35"
                            required
                        >

                    </div>


                    <div class="field">

                        <label>
                            Gender <span>*</span>
                        </label>

                        <select
                            name="gender"
                            required
                        >

                            <option value="">
                                Select gender
                            </option>

                            <option value="Male">
                                Male
                            </option>

                            <option value="Female">
                                Female
                            </option>

                            <option value="Other">
                                Other
                            </option>

                        </select>

                    </div>


                    <div class="field">

                        <label>
                            City
                        </label>

                        <input
                            type="text"
                            name="city"
                            placeholder="e.g. Chennai"
                        >

                    </div>


                    <div class="field">

                        <label>
                            Department
                        </label>

                        <select
                            name="department"
                        >

                            <option value="">
                                Select department
                            </option>

                            <option>
                                Cardiology
                            </option>

                            <option>
                                Neurology
                            </option>

                            <option>
                                Oncology
                            </option>

                            <option>
                                Gastroenterology
                            </option>

                            <option>
                                General Medicine
                            </option>

                            <option>
                                Emergency
                            </option>

                            <option>
                                Dermatology
                            </option>

                            <option>
                                ENT
                            </option>

                            <option>
                                Orthopedics
                            </option>

                            <option>
                                Pediatrics
                            </option>

                        </select>

                    </div>


                </div>

            </div>



            <!-- ==========================================
                 MEDICAL INFORMATION
                 ========================================== -->

            <div class="section">

                <div class="section-title">

                    <div class="number">
                        02
                    </div>

                    Medical & Visit Information

                </div>


                <div class="form-grid">


                    <div class="field">

                        <label>
                            Diagnosis
                        </label>

                        <select
                            name="diagnosis"
                        >

                            <option value="">
                                Select diagnosis
                            </option>

                            <option>
                                Hypertension
                            </option>

                            <option>
                                Diabetes
                            </option>

                            <option>
                                Migraine
                            </option>

                            <option>
                                Asthma
                            </option>

                            <option>
                                Arthritis
                            </option>

                            <option>
                                Gastritis
                            </option>

                            <option>
                                Skin Infection
                            </option>

                            <option>
                                Thyroid Disorder
                            </option>

                            <option>
                                Heart Disease
                            </option>

                            <option>
                                Other
                            </option>

                        </select>

                    </div>


                    <div class="field">

                        <label>
                            Admission Type
                        </label>

                        <select
                            name="admission_type"
                        >

                            <option value="">
                                Select admission type
                            </option>

                            <option>
                                Emergency
                            </option>

                            <option>
                                Urgent
                            </option>

                            <option>
                                Elective
                            </option>

                        </select>

                    </div>


                    <div class="field">

                        <label>
                            Visit Date
                        </label>

                        <input
                            type="date"
                            name="visit_date"
                        >

                    </div>


                    <div class="field">

                        <label>
                            Waiting Time (Minutes)
                        </label>

                        <input
                            type="number"
                            name="waiting_time"
                            min="0"
                            placeholder="e.g. 35"
                        >

                    </div>


                    <div class="field">

                        <label>
                            Length of Stay (Days)
                        </label>

                        <input
                            type="number"
                            name="length_of_stay"
                            min="0"
                            placeholder="e.g. 4"
                        >

                    </div>


                    <div class="field">

                        <label>
                            Patient Satisfaction (1-5)
                        </label>

                        <input
                            type="number"
                            name="satisfaction"
                            min="1"
                            max="5"
                            step="0.01"
                            placeholder="e.g. 4.5"
                        >

                    </div>


                </div>

            </div>



            <!-- ==========================================
                 FINANCIAL INFORMATION
                 ========================================== -->

            <div class="section">

                <div class="section-title">

                    <div class="number">
                        03
                    </div>

                    Financial & Insurance Information

                </div>


                <div class="form-grid">


                    <div class="field">

                        <label>
                            Treatment Cost (INR)
                        </label>

                        <input
                            type="number"
                            name="treatment_cost"
                            min="0"
                            step="0.01"
                            placeholder="e.g. 50000"
                        >

                    </div>


                    <div class="field">

                        <label>
                            Insurance Type
                        </label>

                        <select
                            name="insurance_type"
                        >

                            <option value="">
                                Select insurance
                            </option>

                            <option>
                                Private
                            </option>

                            <option>
                                Government
                            </option>

                            <option>
                                Corporate
                            </option>

                            <option>
                                None
                            </option>

                        </select>

                    </div>


                    <div class="field">

                        <label>
                            Insurance Coverage (INR)
                        </label>

                        <input
                            type="number"
                            name="insurance_coverage"
                            min="0"
                            step="0.01"
                            placeholder="e.g. 40000"
                        >

                    </div>


                    <div class="field">

                        <label>
                            Patient Payment (INR)
                        </label>

                        <input
                            type="number"
                            name="patient_payment"
                            min="0"
                            step="0.01"
                            placeholder="e.g. 10000"
                        >

                    </div>


                    <div class="field">

                        <label>
                            Readmission
                        </label>

                        <select
                            name="readmission"
                        >

                            <option value="No">
                                No
                            </option>

                            <option value="Yes">
                                Yes
                            </option>

                        </select>

                    </div>


                </div>

            </div>



            <!-- ==========================================
                 BUTTONS
                 ========================================== -->

            <div class="buttons">

                <button
                    type="submit"
                    class="btn btn-primary"
                >

                    ✓ Save Patient Record

                </button>


                <button
                    type="reset"
                    class="btn btn-secondary"
                >

                    Clear Form

                </button>

            </div>


        </form>

    </div>



    <!-- ==================================================
         SEARCH
         ================================================== -->

    <div class="search-box">

        <h2>
            Search Patient
        </h2>

        <form
            class="search-form"
            method="GET"
            action="/search"
        >

            <input
                type="text"
                name="patient_id"
                placeholder="Enter Patient ID e.g. P025001"
            >

            <button
                type="submit"
                class="btn btn-primary"
            >

                Search

            </button>

        </form>

    </div>



    <!-- ==================================================
         RECENT RECORDS
         ================================================== -->

    <div class="records">

        <h2>
            Recently Added Patients
        </h2>


        {% if recent_records %}

        <table>

            <thead>

                <tr>

                    <th>Record ID</th>

                    <th>Patient ID</th>

                    <th>Name</th>

                    <th>Age</th>

                    <th>Gender</th>

                    <th>City</th>

                    <th>Department</th>

                    <th>Diagnosis</th>

                    <th>Visit Date</th>

                    <th>Cost</th>

                    <th>Satisfaction</th>

                </tr>

            </thead>


            <tbody>

            {% for row in recent_records %}

                <tr>

                    <td>
                        {{ row.Record_ID }}
                    </td>

                    <td>
                        <strong>
                            {{ row.Patient_ID }}
                        </strong>
                    </td>

                    <td>
                        {{ row.Patient_Name }}
                    </td>

                    <td>
                        {{ row.Age }}
                    </td>

                    <td>
                        {{ row.Gender }}
                    </td>

                    <td>
                        {{ row.City }}
                    </td>

                    <td>
                        {{ row.Department }}
                    </td>

                    <td>
                        {{ row.Diagnosis }}
                    </td>

                    <td>
                        {{ row.Visit_Date }}
                    </td>

                    <td>
                        ₹{{ "{:,.2f}".format(
                            row.Treatment_Cost_INR or 0
                        ) }}
                    </td>

                    <td>
                        ⭐ {{ row.Patient_Satisfaction }}
                    </td>

                </tr>

            {% endfor %}

            </tbody>

        </table>

        {% else %}

            <p>
                No website records found yet.
            </p>

        {% endif %}


    </div>


</main>


</body>

</html>

"""


# ============================================================
# SEARCH PAGE TEMPLATE
# ============================================================

SEARCH_TEMPLATE = """

<!DOCTYPE html>

<html>

<head>

<title>Patient Search</title>

<style>

body {

    font-family: Arial;

    background: #f1f7fc;

    padding: 30px;

    color: #173d60;

}

.container {

    max-width: 1400px;

    margin: auto;

    background: white;

    padding: 30px;

    border-radius: 20px;

}

h1 {

    color: #0b4778;

}

table {

    width: 100%;

    border-collapse: collapse;

    margin-top: 20px;

}

th {

    background: #0b4778;

    color: white;

    padding: 12px;

}

td {

    padding: 12px;

    border-bottom: 1px solid #ddd;

}

a {

    display: inline-block;

    margin-top: 20px;

    padding: 12px 20px;

    background: #0b4778;

    color: white;

    text-decoration: none;

    border-radius: 8px;

}

</style>

</head>


<body>

<div class="container">

<h1>
    Patient Search Results
</h1>

<p>
    Search: <strong>{{ patient_id }}</strong>
</p>


{% if records %}

<table>

<tr>

<th>Record ID</th>
<th>Patient ID</th>
<th>Name</th>
<th>Age</th>
<th>Gender</th>
<th>City</th>
<th>Department</th>
<th>Diagnosis</th>
<th>Visit Date</th>
<th>Cost</th>

</tr>


{% for row in records %}

<tr>

<td>
{{ row.Record_ID }}
</td>

<td>
{{ row.Patient_ID }}
</td>

<td>
{{ row.Patient_Name }}
</td>

<td>
{{ row.Age }}
</td>

<td>
{{ row.Gender }}
</td>

<td>
{{ row.City }}
</td>

<td>
{{ row.Department }}
</td>

<td>
{{ row.Diagnosis }}
</td>

<td>
{{ row.Visit_Date }}
</td>

<td>
₹{{ "{:,.2f}".format(
    row.Treatment_Cost_INR or 0
) }}
</td>

</tr>

{% endfor %}

</table>

{% else %}

<h3>
No patient found.
</h3>

{% endif %}


<a href="/">
    ← Back to Registration
</a>

</div>

</body>

</html>

"""


# ============================================================
# APPLICATION START
# ============================================================

if __name__ == "__main__":

    print("")
    print("==========================================")
    print("       CAREFLOW HOSPITAL SYSTEM")
    print("==========================================")
    print("")

    create_table()

    print("Starting Flask application...")
    print("Open: http://127.0.0.1:5000")
    print("")

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )