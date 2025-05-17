from django.db import models

# Create your models here.
class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    email = models.EmailField(max_length=50, unique=True)
    identification = models.CharField(max_length=10, unique=True)
    otp = models.IntegerField(null=True, blank=True)  # NULL se traduce como null=True, blank=True para permitir valores opcionales
    password = models.CharField(max_length=1000)
    name = models.CharField(max_length=50, null=True, blank=False)
    insurance_type = models.IntegerField(null=True, blank=True)
    document_type = models.IntegerField()
    date_expiration = models.DateField() # Fecha de nacimiento
    role = models.IntegerField(null=True, blank=True)
    notification_insurance = models.IntegerField(default=1)
    notification_others = models.IntegerField(default=1)
    color = models.IntegerField(default=0)
    gender = models.CharField(max_length=20, default="M")
    age = models.IntegerField(default=0) # Edad, calculado con la fecha de nacimiento
    failed_login_attempts = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    identification_parent = models.CharField(max_length=10, unique=True, null=True, blank=True)

    class Meta:
        db_table = 't_user'
        unique_together = ('email', 'identification')

class Comments(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(null=True, blank=False, max_length=50)
    identification = models.CharField(max_length=10, unique=False)
    phone = models.IntegerField(null=True, blank=False, unique=False)
    ask = models.CharField(max_length=1000, null=True, blank=False)
    contacted = models.IntegerField(default=0)

    class Meta:
        db_table = 't_comments'
        unique_together = ('identification', 'phone')

class AskChatgpt(models.Model):
    id = models.BigAutoField(primary_key=True)
    identification = models.CharField(max_length=255, null=True, blank=True)
    question = models.TextField()
    response = models.TextField()
    date = models.DateTimeField()

    class Meta:
        db_table = 't_ask_chatgpt'

class FeedBack(models.Model):
    id = models.BigAutoField(primary_key=True)
    identification = models.CharField(max_length=10, null=True)
    ranking = models.IntegerField()
    observation = models.TextField()
    date = models.DateField()

    class Meta:
        db_table = 't_feedback'

class FrequentQuestions(models.Model):
    id = models.BigAutoField(primary_key=True)
    question = models.TextField()
    answer = models.TextField()
    active = models.IntegerField()

    class Meta:
        db_table = 't_frequent_questions'

class Notifications(models.Model):
    id = models.BigAutoField(primary_key=True)
    identification = models.CharField(max_length=10)
    seenAt = models.IntegerField(null=True)
    message = models.TextField()
    notification_type = models.IntegerField() #1= insurance

class InsuranceHistory(models.Model):
    id = models.BigAutoField(primary_key=True)
    identification = models.CharField(max_length=10)
    name_insurance = models.CharField(max_length=100)
    value = models.IntegerField(default=0)

    class Meta:
        db_table = 't_insurance_history'


# una listado de documentos
#nombre del documento
#id ddel doc
# valor 0 y 1 


#crear # actualizar
# nombre de seguro
# identificación
# estado estado

 # eliminar
 # id
