import bcrypt
from rest_framework import serializers

from .models import User, Comments, FrequentQuestions, FeedBack, Notifications
from .utility.utility_methods import calculate_age, generate_password, generate_random_birth_date, generate_random_gender


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        read_only_fields = ('id',)


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'name', 'identification', 'password', 'document_type', 'date_expiration', 'identification_parent']

    def create(self, validated_data):
        # Generar un "salt" para el hashing
        salt = bcrypt.gensalt()
        # Extraer la contraseña del diccionario de datos validados
        date_param = generate_random_birth_date()
        password = validated_data.pop('password')
        validated_data['date_expiration'] = date_param
        validated_data['role'] = 2
        validated_data['insurance_type'] = 1
        validated_data['age'] = calculate_age(date_param)
        validated_data['gender'] = generate_random_gender()

        # Si 'identification_parent' viene como null, simplemente no se agrega al modelo
        identification_parent = validated_data.get('identification_parent', None)
        if identification_parent is not None:
            validated_data['identification_parent'] = identification_parent
        
        # Aplicar el hash a la contraseña
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        # Crear una nueva instancia del modelo User con los datos validados y la contraseña cifrada
        user = User.objects.create(password=hashed_password, **validated_data)
        user.password = ""
        return user

class UserResponseSerializer(serializers.Serializer):
    email = serializers.EmailField()
    identification = serializers.CharField()
    insurance_type = serializers.IntegerField()
    document_type = serializers.IntegerField()

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'identification', 'insurance_type', 'password']

    identification = serializers.CharField()
    insurance_type = serializers.IntegerField(required=False, allow_null=True)
    email = serializers.EmailField(required=False, allow_null=True)
    password = serializers.CharField(write_only=True, required=False, allow_null=True)

    def validate_email(self, value):
        user_id = self.instance.id if self.instance else None
        if User.objects.filter(email=value).exclude(id=user_id).exists():
            raise serializers.ValidationError("Este correo ya está en uso por otro usuario.")
        return value

    def update(self, instance, validated_data):
        # Actualiza solo si el campo está presente y no es None
        for field in ['email', 'insurance_type', 'password']:
            if field in validated_data and validated_data[field]:
                if field == 'password':
                    instance.password = generate_password(validated_data['password'])
                else:
                    setattr(instance, field, validated_data[field])

        instance.save()
        return instance

class UserLoginSerializer(serializers.Serializer):
    identification = serializers.CharField()
    password = serializers.CharField()

class UserSendEmailRecovery(serializers.Serializer):
    email = serializers.EmailField()

class UserRecoveryWithLogin(serializers.Serializer):
    identification = serializers.CharField(max_length=10, min_length=8)
    currentPassword = serializers.CharField(max_length=500, min_length=1)
    newPassword = serializers.CharField(max_length=500, min_length=1)

class UserSendEmailTokenRecovery(serializers.Serializer):
    identification = serializers.CharField()
    token = serializers.IntegerField()
    password = serializers.CharField()


class CommentsAskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comments
        fields = ['identification', 'ask']

    def create(self, validated_data):
        raise serializers.ValidationError("Este comentario ya existe, intenta usar 'update_or_create'.")

    def update_or_create(self, validated_data):
        if comment:
            comment.phone = validated_data['phone']
            comment.save()
            return comment

        comment = Comments.objects.create(**validated_data)
        return comment

class CommentsPhoneSerializer(serializers.Serializer):
    identification = serializers.CharField(max_length=10)
    phone = serializers.IntegerField(required=False)
    ask = serializers.CharField(max_length=100, required=False)

    def create(self, validated_data):
        # Crea el comentario sin restricciones de unicidad
        return Comments.objects.create(**validated_data)


class FrequentQuestionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = FrequentQuestions
        fields = ['id', 'question', 'active', 'answer']

class FrequentQuestionsCreateUpdateSerializer(serializers.ModelSerializer):
    question = serializers.CharField(required=True)
    active = serializers.IntegerField(required=True)
    answer = serializers.CharField(required=True)

    class Meta:
        model = FrequentQuestions
        fields = ['question', 'active', 'answer']

    def validate(self, data):
        # Si es una creación (la instancia no existe)
        if self.instance is None:
            if 'question' not in data or 'active' not in data:
                raise serializers.ValidationError("Los campos 'question' y 'active' son obligatorios al crear un registro.")
        return data

class FeedBackCreateSerializer(serializers.ModelSerializer):
    identification = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    ranking = serializers.IntegerField()
    observation = serializers.CharField
    date = serializers.DateTimeField()

    class Meta:
        model = FeedBack
        fields = ['identification', 'ranking', 'observation', 'date']


class NotificationCreate(serializers.Serializer):
    insuranceType = serializers.IntegerField(required=False)
    type = serializers.IntegerField() # Tipo 1 Seguros, 2 = Otros
    message = serializers.CharField(allow_null=True)
    identification = serializers.CharField(allow_null=True, required=False)


class NotificationListNSerializer(serializers.Serializer):
    identification = serializers.CharField(required=True)

class NotificationDisablingSerializer(serializers.Serializer):
    identification = serializers.CharField(required=True)
    value = serializers.IntegerField()
    notificationType = serializers.IntegerField(required=True)

class NotificationDisablingUniqueSerializer(serializers.Serializer):
    idNotification = serializers.IntegerField(required=True)

class CommentsSaveSerializer(serializers.Serializer):
    idComment = serializers.IntegerField(required=True)
    ask = serializers.CharField(required=False)

class ChangeColorWebSerializer(serializers.Serializer):
    identification = serializers.CharField(required=True)
    value = serializers.IntegerField(required=True)

class InsuranceHistory(serializers.Serializer):
    identification = serializers.CharField(required=True)
    name_insurance = serializers.CharField(max_length=100)
    value = serializers.IntegerField(required=True)

class CreateOrUpdateInsurance(serializers.Serializer):
    idInsurance = serializers.IntegerField(required=False, allow_null=True)
    identification = serializers.CharField(max_length=10)
    nameInsurance = serializers.CharField(max_length=100)
    value = serializers.IntegerField()

class ListInsurance(serializers.Serializer):
    identification = serializers.CharField(max_length=10)

class DeleteInsurance(serializers.Serializer):
    idInsurance = serializers.IntegerField()
    
