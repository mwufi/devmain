from jose import jwt

# The same SECRET_KEY used in the server
SECRET_KEY = "another_secret_key"
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiY2xpZW50X2lkIjoiMmM3NjhkZDUtOWY5Ny00Y2JhLTgyNWYtNzUyYzAzMzdlNWEzIiwiZXhwIjoxNzQ0MzMwNjI5fQ.BIRN2hnDkVRx1ECCr0vMahkjWiMyI8efQ8YyBPa_Kec"
decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
print(decoded)