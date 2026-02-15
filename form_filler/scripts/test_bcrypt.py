
import bcrypt

password = "K@nni:18"
stored_hash = "$2b$12$0M4AOK0VVBGQvaQildxWr.Pl9Mt2Nf28Q0NqMDltJwCpBrNEg8Nm."

print(f"Password: {password}")
print(f"Hash: {stored_hash}")

result = bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))

print(f"Match: {result}")
