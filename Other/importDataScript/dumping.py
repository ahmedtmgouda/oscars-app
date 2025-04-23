import csv
import mysql.connector

# 1. Connect to your MySQL database
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Madvillainy1971",
    database="theOscars"
)
cursor = connection.cursor()

# 2. CSV file path
csv_file_path = "/Users/ahmedgouda/Desktop/DatabaseM2/csvFilesClean/FinalAcademyNomination_clean.csv"

# 3. Create the INSERT statement
insert_stmt = """
    INSERT INTO AcademyNomination (
        personFirstName, personLastName, personBirthDate,
        movieTitle, movieReleaseDate,
        category, iteration, grantedOrNot
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""

row_count = 0
failed_rows = []

with open(csv_file_path, mode="r", encoding="utf-8-sig") as f:
    reader = csv.reader(f, delimiter=",", quotechar='"')

    # 4. Skip the header row
    next(reader, None)

    for row in reader:
        # row = [
        #   personFirstName, personLastName, personBirthDate,
        #   movieTitle, movieReleaseDate,
        #   category, iteration, grantedOrNot
        # ]
        
        personFirstName = row[0]
        personLastName = row[1]
        personBirthDate = row[2].strip()
        movieTitle = row[3]
        movieReleaseDate = row[4].strip()
        category = row[5]
        
        # iteration is an integer
        iteration_str = row[6].strip()
        iteration = int(iteration_str) if iteration_str else None

        # grantedOrNot is "True" or "False"
        granted_str = row[7].strip().lower()
        grantedOrNot = (granted_str == "true")

        data_tuple = (
            personFirstName,
            personLastName,
            personBirthDate,
            movieTitle,
            movieReleaseDate,
            category,
            iteration,
            grantedOrNot
        )

        try:
            cursor.execute(insert_stmt, data_tuple)
            connection.commit()
            row_count += 1
        except mysql.connector.Error as err:
            connection.rollback()
            failed_rows.append((data_tuple, str(err)))

# 5. Clean up
cursor.close()
connection.close()

# 6. Print summary
print(f"Successfully inserted {row_count} rows into AcademyNomination.")
if failed_rows:
    print("The following rows could not be inserted:")
    for i, (bad_row, error_msg) in enumerate(failed_rows, start=1):
        print(f"\nFailed row #{i}: {bad_row}")
        print(f"Error message: {error_msg}")
