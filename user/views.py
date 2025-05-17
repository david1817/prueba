import random
from functools import wraps
import os
from dotenv import load_dotenv
import PyPDF2
import bcrypt
import openai
from django.utils import timezone
from rest_framework import status, serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.utils import timezone
from datetime import timedelta
from user.dto import response_data_to_dict, ResponseData
from user.email_utils import send_email
from user.models import InsuranceHistory, User, Comments, AskChatgpt, FrequentQuestions, Notifications
from user.serializers import DeleteInsurance, ListInsurance, UserCreateSerializer, UserResponseSerializer, UserUpdateSerializer, UserLoginSerializer, \
    UserSendEmailRecovery, UserSendEmailTokenRecovery, UserRecoveryWithLogin, CommentsPhoneSerializer, \
    CommentsAskSerializer, FrequentQuestionsSerializer, FrequentQuestionsCreateUpdateSerializer, \
    FeedBackCreateSerializer, NotificationCreate, NotificationListNSerializer, NotificationDisablingSerializer, \
    NotificationDisablingUniqueSerializer, CommentsSaveSerializer, ChangeColorWebSerializer, CreateOrUpdateInsurance
from user.utility.utility_methods import generate_password, valid_role


def token_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION')

        if not token:
            return Response({'error': 'Token no proporcionado.'}, status=status.HTTP_401_UNAUTHORIZED)

        try:
            token = token.split()[1]  # Asume que el token es de tipo "Bearer <token>"
            access_token = AccessToken(token)  # Intenta validar el token
            # Aquí puedes acceder a los datos del token si es necesario
            # Puedes almacenar el user_id en request si lo necesitas en la vista
        except Exception:
            return Response({'error': 'Token no válido.'}, status=status.HTTP_401_UNAUTHORIZED)

        return view_func(request, *args, **kwargs)

    return _wrapped_view


# Create your views here.
@api_view(['POST'])
def login(request):
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        identification = serializer.validated_data['identification']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(identification=identification)

            # Verifica si la cuenta está actualmente bloqueada
            if user.account_locked_until and timezone.now() < user.account_locked_until:
                return Response({'error': 'Cuenta bloqueada por demasiados intentos fallidos. Intenta más tarde.'},
                                status=status.HTTP_403_FORBIDDEN)

            now = timezone.now()

            # Reinicia el contador si pasó más de 5 minutos desde el último fallo
            if user.last_failed_login and (now - user.last_failed_login > timedelta(minutes=5)):
                user.failed_login_attempts = 0

            hashed_password = user.password.encode('utf-8') if isinstance(user.password, str) else user.password
            if bcrypt.checkpw(password.encode('utf-8'), hashed_password):
                # Éxito: limpia los campos de fallos
                user.failed_login_attempts = 0
                user.account_locked_until = None
                user.last_failed_login = None
                user.save()

                refresh = RefreshToken.for_user(user)
                return Response({
                    'role': valid_role(user.role),
                    'identification': identification,
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'notificationInsurance': user.notification_insurance,
                    'notificationOthers': user.notification_others,
                    'color': user.color
                }, status=status.HTTP_200_OK)

            else:
                # Fallo: incrementa contador
                user.failed_login_attempts += 1
                user.last_failed_login = now

                # Si llega a 5 fallos dentro de 5 minutos → bloquear 1 hora
                if user.failed_login_attempts >= 5:
                    user.account_locked_until = now + timedelta(hours=1)
                    user.failed_login_attempts = 0  # Reinicia contador al bloquear

                user.save()
                return Response({'error': 'Usuario o Contraseña incorrecta'}, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({'error': 'Usuario no encontrado'}, status=status.HTTP_404_NOT_FOUND)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def create_user(request):
    serializer = UserCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()

        response_data = ResponseData(
            code=status.HTTP_201_CREATED,
            message='Usuario creado con éxito',
            data=serializer.data  # Puedes incluir cualquier otra información relevante aquí
        )

        return Response(response_data_to_dict(response_data), status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@token_required
def find_user(request):
    identification = request.data.get('identification')  # Extraer la identificación del request

    if not identification:
        return Response({'detail': 'Identification is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Buscar el usuario en la base de datos usando la identificación
        user = User.objects.get(identification=identification)

        # Serializar los campos seleccionados usando el serializer
        user_data = {
            'email': user.email,
            'identification': user.identification,
            'insurance_type': user.insurance_type,
            'document_type': user.document_type,
        }
        serializer = UserResponseSerializer(user_data)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@token_required
def update_user(request):
    identification = request.data.get('identification')

    try:
        user = User.objects.get(identification=identification)
    except User.DoesNotExist:
        return Response({
            "code": 404,
            "message": "Usuario no encontrado"
        }, status=404)

    serializer = UserUpdateSerializer(user, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response({
            "code": 200,
            "message": "Usuario actualizado con éxito",
            "data": serializer.data
        })
    else:
        return Response({
            "code": 400,
            "message": "Error al actualizar el usuario",
            "errors": serializer.errors
        }, status=400)


@api_view(['POST'])
def recovery_user(request):
    serializer = UserSendEmailRecovery(data=request.data)
    if serializer.is_valid():
        try:
            email = request.data.get('email')
            random_number = random.randint(100000, 999999)
            user = User.objects.get(email=email)
            user.otp = random_number
            user.save()
            send_email(email, random_number)

            return Response({
                "code": 200,
                "message": "Correo enviado correctamente",
            }, status=200)

        except User.DoesNotExist:
            Response({
                "code": 400,
                "message": "Usuario no encontrado",
            }, status=400)
    return Response({
        "code": 400,
        "message": "Error con los datos enviados",
    }, status=400)


@api_view(['POST'])
def recovery_token_user(request):
    serializer = UserSendEmailTokenRecovery(data=request.data)
    if serializer.is_valid():
        try:
            identification = request.data.get('identification')
            token = request.data.get('token')
            password = request.data.get('password')
            user = User.objects.get(identification=identification)
            if user.otp == token:
                user.password = generate_password(password)
                user.otp = None
                user.save()
            else:
                return Response({
                    "code": 400,
                    "message": "Token invalido",
                }, status=400)

            return Response({
                "code": 200,
                "message": "Contraseña actualiza correctamente",
            }, status=200)

        except User.DoesNotExist:
            Response({
                "code": 400,
                "message": "Usuario no encontrado",
            }, status=400)
    return Response({
        "code": 400,
        "message": "Error con los datos enviados",
    }, status=400)


@api_view(['POST'])
@token_required
def recovery_user_with_login(request):
    serializer = UserRecoveryWithLogin(data=request.data)

    # Si los datos no son válidos, devolver los errores
    if not serializer.is_valid():
        return Response({
            "code": 400,
            "message": "Error con los datos enviados",
            "errors": serializer.errors  # Mostrar los errores de validación
        }, status=400)

    try:
        current_password = request.data.get('currentPassword')
        identification = request.data.get('identification')
        new_password = request.data.get('newPassword')
        user = User.objects.get(identification=identification)

        hashed_password = user.password.encode('utf-8') if isinstance(user.password, str) else user.password

        # Verificar si la contraseña actual es correcta
        if bcrypt.checkpw(current_password.encode('utf-8'), hashed_password):
            password = generate_password(new_password)
            user.password = password
            user.save()

            return Response({
                "code": 200,
                "message": "Contraseña actualizada correctamente",
            }, status=200)
        else:
            return Response({
                "code": 400,
                "message": "Password incorrecto",
            }, status=400)

    except User.DoesNotExist:
        return Response({
            "code": 400,
            "message": "Usuario no encontrado",
        }, status=400)


class QuestionRequestSerializer(serializers.Serializer):
    question = serializers.CharField(max_length=1000)  # Ajusta el tamaño máximo según tus necesidades
    identification = serializers.CharField(allow_null=True, required=False)
    context = serializers.CharField(allow_null=True, required=False)

class QuestionResponseSerializer(serializers.Serializer):
    response = serializers.CharField()
    code = serializers.IntegerField()


# API chatgpt
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

@api_view(['POST'])
def ask(request):
    serializer = QuestionRequestSerializer(data=request.data)
    if serializer.is_valid():
        pdf_path = './user/context/Informacion_general.pdf'
        name_pdf = request.data['context']
        if name_pdf is not None:
            pdf_path = f'./user/context/{name_pdf}'
        
        data = extract_text_from_pdf(pdf_path)
        question = serializer.validated_data['question']
        # Mensajes iniciales para la conversación
        messages = [
            {"role": "system", "content": "Este es el contexto " + data},
            {"role": "user", "content": question}
        ]  # Ajusta el contexto según sea necesario
        try:
            # Llamada a la API de OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages
            )

            response_content = response.choices[0].message.content
            identification = serializer.validated_data.get('identification')
            print(identification)
            # Guarda la pregunta y la respuesta en el modelo AskChatgpt
            AskChatgpt.objects.create(
                identification=identification or None,
                question=question,
                response=response_content,
                date=timezone.now()  # Guarda la fecha actual
            )

            response_data = {
                'response': response_content,
                'code': status.HTTP_200_OK
            }
            response_serializer = QuestionResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'detail': 'Error al procesar la solicitud.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def extract_text_from_pdf(pdf_file):
    with open(pdf_file, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        text = ''

        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text += page.extract_text()
    return text


@api_view(['POST'])
@token_required
def comments_ask(request):
    serializer = CommentsPhoneSerializer(data=request.data)

    # Verifica si los datos son válidos
    if serializer.is_valid():
        # Llama a `create` para crear el comentario
        comment = serializer.save()
        
        # Prepara la respuesta
        response_data = ResponseData(
            code=status.HTTP_201_CREATED,
            message='Comentario creado exitosamente',
            data={'identification': comment.identification, 'ask': comment.ask}
        )
        return Response(response_data_to_dict(response_data), status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@token_required
def comments_phone(request):
    serializer = CommentsPhoneSerializer(data=request.data)

    # Verifica si los datos son válidos
    if serializer.is_valid():
        # Llama a `create` para crear el comentario
        comment = serializer.save()
        
        # Prepara la respuesta
        response_data = ResponseData(
            code=status.HTTP_201_CREATED,
            message='Comentario creado exitosamente',
            data={'identification': comment.identification, 'phone': comment.phone}
        )
        return Response(response_data_to_dict(response_data), status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def frequent_questions_list(request):
    # Obtener todas las preguntas frecuentes activas
    questions = FrequentQuestions.objects.all()

    # Serializar los datos
    serializer = FrequentQuestionsSerializer(questions, many=True)
    response_data = ResponseData(
        code=status.HTTP_200_OK,
        message="",
        data=serializer.data
    )

    return Response(response_data_to_dict(response_data), status=status.HTTP_200_OK)


@api_view(['POST'])
@token_required
def frequent_questions_create_update(request):
    # Verificamos si se envió un id
    question_id = request.data.get('id')

    # Si se proporciona un id, intentamos obtener la pregunta
    if question_id:
        try:
            # Buscar el registro existente
            question = FrequentQuestions.objects.get(id=question_id)
            # Crear un serializer para la actualización
            serializer = FrequentQuestionsCreateUpdateSerializer(question, data=request.data, partial=True)
        except FrequentQuestions.DoesNotExist:
            return Response({'error': 'Pregunta no encontrada.'}, status=status.HTTP_404_NOT_FOUND)
    else:
        # Crear un nuevo registro
        serializer = FrequentQuestionsCreateUpdateSerializer(data=request.data)

    # Validamos y guardamos
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED if not question_id else status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def feed_back_create(request):
    serializer = FeedBackCreateSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    # Cambiar la estructura de respuesta de error a un diccionario
    response_data = {
        'code': status.HTTP_400_BAD_REQUEST,
        'message': "Error en crear",
        'data': serializer.errors  # Cambiado a serializer.errors para devolver errores de validación
    }
    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@token_required
def notification_create(request):
    serializer = NotificationCreate(data=request.data)
    if serializer.is_valid():
        type_notification = request.data.get('type')
        if type_notification == 1:  # Tipo 1 Seguros, 2 = Otros
            insurance_type = request.data['insuranceType']
            users = User.objects.filter(insurance_type=insurance_type)
            users_list = list(users.values())

            for element in users_list:
                Notifications.objects.create(
                    message=request.data['message'],
                    identification=element['identification'],
                    notification_type=type_notification,
                    seenAt=0
                )
        elif type_notification == 2:
            Notifications.objects.create(
                message=request.data['message'],
                identification=request.data['identification'],
                notification_type=type_notification,
                seenAt=0
            )

        response_data = {
            'code': status.HTTP_200_OK,
            'message': "La notifación fue guardado",
            'data': None  # Cambiado a serializer.errors para devolver errores de validación
        }

        return Response(response_data, status=status.HTTP_200_OK)

    response_data = {
        'code': status.HTTP_400_BAD_REQUEST,
        'message': "Error en guardar la notificación",
        'data': serializer.errors  # Cambiado a serializer.errors para devolver errores de validación
    }
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@token_required
def notification_list(request):
    notifications = None
    serializer = NotificationListNSerializer(data=request.data)
    if serializer.is_valid():
        identification = request.data['identification']
        try:
            notification = Notifications.objects.filter(identification=identification)
            if notification is not None and notification.values() is not None:
                notifications = list(notification.values())
                for notification in notifications:
                    notification.pop('identification', None)  # Remover el campo 'identification'
        except Notifications.DoesNotExist:
            notifications = None  # Si no existen notificaciones, asignamos None o una lista vacía

        response_data = {
            'code': status.HTTP_200_OK,
            'message': None,
            'data': notifications  # Cambiado a serializer.errors para devolver errores de validación
        }
        return Response(response_data, status=status.HTTP_200_OK)

    response_data = {
        'code': status.HTTP_400_BAD_REQUEST,
        'message': "Error",
        'data': serializer.errors  # Cambiado a serializer.errors para devolver errores de validación
    }
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@token_required
def notification_disabling(request):
    serializer = NotificationDisablingSerializer(data=request.data)
    if serializer.is_valid():
        identification = serializer.validated_data['identification']
        notification_type = request.data['notificationType']
        value = request.data['value']
        try:
            user = User.objects.get(identification=identification)  # Cambiado a get()

            if notification_type == 1:
                user.notification_insurance = value
            elif notification_type == 2:
                user.notification_others = value

            user.save()

            response_data = {
                'code': status.HTTP_200_OK,
                'message': 'La notificación fue actualizada',
                'data': serializer.data  # Devolver datos del serializer
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            response_data = {
                'code': status.HTTP_400_BAD_REQUEST,
                'message': 'Usuario no encontrado',  # Corrección de typo
                'data': None
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)  # Cambiado a 400 en caso de error

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # Devuelve errores de validación


@api_view(['POST'])
@token_required
def notification_disabling_unique(request):
    serializer = NotificationDisablingUniqueSerializer(data=request.data)
    if serializer.is_valid():
        try:
            notification = Notifications.objects.get(id=request.data['idNotification'])
            notification.seenAt = 1
            notification.save()
            response_data = {
                'code': status.HTTP_200_OK,
                'message': 'La notificación fue actualizada',
                'data': serializer.data  # Devolver datos del serializer
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Notifications.DoesNotExist:
            response_data = {
                'code': status.HTTP_400_BAD_REQUEST,
                'message': 'Notificación no encontrada',  # Corrección de typo
                'data': None
            }
            return Response(response_data, status=status.HTTP_200_OK)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)  # Devuelve errores de validación


@api_view(['GET'])
@token_required
def comments_all(request):
    comments = Comments.objects.all()
    comments_list = list(comments.values())
    response_data = {
        'code': status.HTTP_200_OK,
        'message': None,
        'data': comments_list
    }

    return Response(response_data, status=status.HTTP_200_OK)


@api_view(['POST'])
@token_required
def comments_modify(request):
    serializer = CommentsSaveSerializer(data=request.data)
    if serializer.is_valid():
        comment_param = request.data['idComment']
        ask_param = request.data['ask']
        try:
            comment = Comments.objects.get(id=comment_param)
            comment.contacted = 1
            if ask_param is not None:
                comment.ask = ask_param
            comment.save()

            response_data = {
                'code': status.HTTP_200_OK,
                'message': 'Comentario actualizado',
                'data': None
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except Comments.DoesNotExist:
            response_data = {
                'code': status.HTTP_400_BAD_REQUEST,
                'message': 'Comentario no existe',
                'data': None
            }
            return Response(response_data, status=status.HTTP_200_OK)

    response_data = {
        'code': status.HTTP_400_BAD_REQUEST,
        'message': None,
        'data': serializer.errors
    }
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['POST'])
@token_required
def color_web(request):
    serializer = ChangeColorWebSerializer(data=request.data)
    if serializer.is_valid():
        identification = serializer.validated_data['identification']
        value = request.data['value']
        try:
            user = User.objects.get(identification=identification)
            user.color = value
            user.save()

            response_data = {
                'code': status.HTTP_200_OK,
                'message': 'El color de fondo fue actualizado',
                'data': serializer.data
            }
            return Response(response_data, status=status.HTTP_200_OK)

        except User.DoesNotExist:
            response_data = {
                'code': status.HTTP_400_BAD_REQUEST,
                'message': 'Usuario no encontrado',
                'data': None
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST) 

    response_data = {
        'code': status.HTTP_400_BAD_REQUEST,
        'message': None,
        'data': serializer.errors
    }
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['POST'])
@token_required
def insurance(request):
    serializer = CreateOrUpdateInsurance(data=request.data)
    if serializer.is_valid():
        id_param = request.data['idInsurance']
        identification_value = request.data['identification']
        name_insurance_param = request.data['nameInsurance']
        value_param = request.data['value']

        if id_param is None:
            insurance_history = InsuranceHistory.objects.create(
                identification=identification_value,
                name_insurance=name_insurance_param,
                value=value_param
            )
            message = 'Registro creado'
        else:
            insurance_history, created = InsuranceHistory.objects.update_or_create(
                id=id_param,
                defaults={
                    'identification': identification_value,
                    'name_insurance': name_insurance_param,
                    'value': value_param
                }
            )
            message = 'Registro actualizado' if not created else 'Registro creado'

        response_data = {
        'code': status.HTTP_200_OK,
        'message': message,
        'data': {
            'idInsurance': insurance_history.id,
            'identification': insurance_history.identification,
            'nameInsurance': insurance_history.name_insurance,
            'value': insurance_history.value,
            }
        }
        return Response(response_data, status=status.HTTP_200_OK)
        
    response_data = {
        'code': status.HTTP_400_BAD_REQUEST,
        'message': None,
        'data': serializer.errors
    }
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['POST'])
@token_required
def insurance_list(request):
    serializers = ListInsurance(data=request.data)
    if serializers.is_valid():
        insurance = InsuranceHistory.objects.filter(identification=request.data['identification'])
        insurance_list = list(insurance.values())
        response_data = {
            'code': status.HTTP_200_OK,
            'message': "Listado de seguros",
            'data': insurance_list
            }
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['POST'])
@token_required
def insurance_delete(request):
    serializers = DeleteInsurance(data=request.data)
    if serializers.is_valid():
        insurance = InsuranceHistory.objects.get(id=request.data['idInsurance'])
        insurance.delete()
        response_data = {
            'code': status.HTTP_200_OK,
            'message': "Pdf eliminado del usuario",
            'data': None
            }
    return Response(response_data, status=status.HTTP_200_OK)

@api_view(['GET'])
@token_required
def report(request):
    report_data = {
        "man": User.objects.filter(gender='M').count(),
        "women": User.objects.filter(gender='F').count(),
        "rangeAge1": User.objects.filter(age__gt=0, age__lt=17).count(),  # Cambia los valores según los datos reales
        "rangeAge2": User.objects.filter(age__gt=18, age__lt=29).count(),
        "rangeAge3": User.objects.filter(age__gt=30, age__lt=59).count(),
        "rangeAge4": User.objects.filter(age__gt=60).count(),
        "typeInsurance1": User.objects.filter(insurance_type=1).count(),
        "typeInsurance2": User.objects.filter(insurance_type=2).count(),
        "typeInsurance3": User.objects.filter(insurance_type=3).count(),
        "typeInsurance4": User.objects.filter(insurance_type=4).count(),
        "questionsRegistered": AskChatgpt.objects.filter(identification__isnull=False).count(),
        "questionsUnregistered": AskChatgpt.objects.filter(identification__isnull=True).count(),
        "userRegistered": User.objects.count()
    }

    response_data = {
        'code': status.HTTP_200_OK,
        'message': "Reporte generado",
        'data': report_data
    }
    return Response(response_data, status=status.HTTP_200_OK)