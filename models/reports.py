from models.db import get_db_connection


def allPatientTable():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
           SELECT * FROM cec_registration
    """)
    patients = cursor.fetchall()

    cursor.close()
    conn.close()

    return patients


def allTransferPatient():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
           SELECT * FROM cec_transfer
    """)
    patients = cursor.fetchall()

    cursor.close()
    conn.close()

    return patients


def getCECRegistrationCount():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
            SELECT COUNT(*) AS NumberOfPatient
            FROM cec_registration
    """)
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result["NumberOfPatient"]


def getTransferreeCount():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
           SELECT COUNT(*) AS NumberOfPatient
            FROM cec_transfer
    """)
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return result["NumberOfPatient"]


def getEkassEpressTransmittal():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM transmittal
    """)
    result = cursor.fetchall()

    cursor.close()
    conn.close()

    return result
