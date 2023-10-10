import bcrypt

# Generate a salt
salt = bcrypt.gensalt()

# Write the salt to a file
with open('report.txt', 'w') as f:
    f.write(salt.decode('utf-8'))
