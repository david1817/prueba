from datetime import datetime, timedelta
import random
import bcrypt

def generate_password(password: str) -> str:
    # Genera una sal
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed_password.decode('utf-8')

def valid_role(value):
    match value:
        case 1:
            return "ROLE_ADMIN"
        case 2:
            return "ROLE_USER"
        case _:
            return ""
        
def generate_random_birth_date():
    min_age = 17
    max_age = 60
    today = datetime.today()
    max_birth_date = today - timedelta(days=min_age * 365)
    min_birth_date = today - timedelta(days=max_age * 365)
    random_birth_date = min_birth_date + (max_birth_date - min_birth_date) * random.random()
    return random_birth_date.date()

def calculate_age(birth_date):
    today = datetime.today().date()
    age = today.year - birth_date.year
    
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
        
    return age

def generate_random_gender():
    return random.choice(['M', 'F'])