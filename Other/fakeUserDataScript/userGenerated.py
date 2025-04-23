import csv
import random
from datetime import datetime, timedelta
from faker import Faker
import os

fake = Faker()

# The directory where we will save our CSV files
output_dir = "/Users/ahmedgouda/Desktop/userGeneratedDate"

# Ensure the directory exists (if it doesn't, this will create it)
os.makedirs(output_dir, exist_ok=True)

# -----------------------------
# 1) Generate 5 Users
# -----------------------------
num_users = 5

def random_gender():
    return random.choice(["Male", "Female"])

users_data = []
for _ in range(num_users):
    full_name = fake.name()
    username = (full_name.split()[0] + str(random.randint(10, 999))).lower()
    
    gender = random_gender()
    email = fake.email()
    
    # Age: random between 18 and 60
    age = random.randint(18, 60)
    
    # We'll approximate birth date by subtracting 'age' years from "now"
    today = datetime.now()
    birth_date = today.replace(year=today.year - age)
    # Random shift in days up to 365
    birth_date -= timedelta(days=random.randint(0, 365))
    birth_date_str = birth_date.strftime("%Y-%m-%d")
    
    country = fake.country()
    
    users_data.append({
        "username": username,
        "gender": gender,
        "email": email,
        "age": age,
        "birthDate": birth_date_str,
        "country": country
    })

# Build full path for Users.csv
users_csv_path = os.path.join(output_dir, "Users.csv")

# Write Users.csv
with open(users_csv_path, "w", newline='', encoding='utf-8') as f:
    fieldnames = ["username", "gender", "email", "age", "birthDate", "country"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in users_data:
        writer.writerow(row)

# -----------------------------
# 2) Generate 1 Nomination per User
# -----------------------------
possible_persons = [
    ("Charlie", "Chaplin", "1889-04-16"),
    ("Buster", "Keaton", "1895-10-04"),
    ("Meryl", "Streep", "1949-06-22"),
    ("Tom", "Hanks", "1956-07-09"),
    ("Audrey", "Hepburn", "1929-05-04")
]

possible_movies = [
    ("City Lights", "1931-03-07"),
    ("Modern Times", "1936-02-25"),
    ("The General", "1926-12-31"),
    ("Forrest Gump", "1994-06-23"),
    ("Roman Holiday", "1953-08-27")
]

possible_categories = ["Best Actor", "Best Actress", "Best Picture", "Best Director", "Best Cinematography"]

user_nominations = []

for user in users_data:
    person = random.choice(possible_persons)
    movie = random.choice(possible_movies)
    category = random.choice(possible_categories)
    iteration = random.randint(1, 96)
    granted = random.choice([True, False])
    
    user_nominations.append({
        "userUsername": user["username"],
        "personFirstName": person[0],
        "personLastName": person[1],
        "personBirthDate": person[2],
        "movieTitle": movie[0],
        "movieReleaseDate": movie[1],
        "category": category,
        "iteration": iteration,
        "grantedOrNot": granted
    })

# Build full path for UserNomination.csv
usernom_csv_path = os.path.join(output_dir, "UserNomination.csv")

# Write UserNomination.csv
with open(usernom_csv_path, "w", newline='', encoding='utf-8') as f:
    fieldnames = [
        "userUsername",
        "personFirstName",
        "personLastName",
        "personBirthDate",
        "movieTitle",
        "movieReleaseDate",
        "category",
        "iteration",
        "grantedOrNot"
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in user_nominations:
        writer.writerow(row)

print("Done! Created the following files:")
print(f" - {users_csv_path}")
print(f" - {usernom_csv_path}")
