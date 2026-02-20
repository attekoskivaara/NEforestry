import random
from openpyxl import load_workbook, Workbook

input_file = "recipients_test.xlsx"
output_file = "recipients_test2.xlsx"

def generate_password():
    return str(random.randint(10000, 99999))

# Lue input
wb_input = load_workbook(input_file)
ws_input = wb_input.active

# Selvitä sarakkeet
headers = {}
for col in range(1, ws_input.max_column + 1):
    value = ws_input.cell(row=1, column=col).value
    if value:
        headers[value.strip().lower()] = col

if "email" not in headers:
    raise ValueError("Input file must contain 'email' column")

# Luo output
wb_output = Workbook()
ws_output = wb_output.active
ws_output.title = "Recipients"

ws_output.append(["email", "first_name", "username", "password"])

for row in range(2, ws_input.max_row + 1):

    email = ws_input.cell(row=row, column=headers["email"]).value
    if not email:
        continue

    # Ota name sellaisenaan jos löytyy
    name = ""
    if "first_name" in headers:
        name_value = ws_input.cell(row=row, column=headers["first_name"]).value
        if name_value:
            name = name_value  # ei splitata, ei muokata

    password = generate_password()
    username = email

    ws_output.append([email, name, username, password])

wb_output.save(output_file)

print("recipients.xlsx created successfully!")