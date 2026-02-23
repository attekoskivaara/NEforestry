import csv
import random

input_file = "recipients_test.csv"
output_file = "recipients_test_230226_2.csv"

def generate_password():
    return str(random.randint(10000, 99999))

# Lue input CSV
with open(input_file, newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f, delimiter=';')  # <-- important!
    rows = list(reader)

# Luo output CSV
with open(output_file, "w", newline="", encoding="utf-8") as f:
    fieldnames = ["email", "first_name", "username", "password"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for row in rows:
        email = row.get("email")
        if not email:
            continue

        # Ota first_name sellaisenaan, jos löytyy
        name = row.get("first_name", "")

        password = generate_password()
        username = email  # sama kuin sähköposti

        writer.writerow({
            "email": email,
            "first_name": name,
            "username": username,
            "password": password
        })

print(f"{output_file} created successfully!")