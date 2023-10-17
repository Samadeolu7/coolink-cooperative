import csv

def write_credentials_to_file(employee_id, email, password):
    with open(f"credentials/{employee_id}_credentials.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Username", "Password"])
        writer.writerow([f"{employee_id} or {email}", password])

    return file
