import json
from dotenv import load_dotenv
import os

load_dotenv()

# Retrieve and deserialize the list from the environment variable
years_str = os.getenv("YEARS", "[]")
years = json.loads(years_str)

# Print the original list
print("Original List:", years)

# Append elements to the list
years.append(2021)
years.append(2022)

# Serialize and store the updated list back in the environment variable
os.environ["YEARS"] = json.dumps(years)

# Retrieve and deserialize the updated list from the environment variable
updated_years_str = os.getenv("YEARS", "[]")
updated_years = json.loads(updated_years_str)

# Print the updated list
print("Updated List:", updated_years)
