import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(email_destination, token):
    # Configuración del servidor SMTP (aquí usamos Gmail como ejemplo)
    smtp_server = "smtp.gmail.com"
    smtp_port = 587  # Puerto para conexión TLS
    email_user = "P20241053@gmail.com"
    email_password = "swru jcfd ktpb jmwh"

    # Crear el mensaje
    message = MIMEMultipart()
    message["From"] = email_user
    message["To"] = email_destination
    message["Subject"] = "Recuperación de contraseña"

    body = "<!DOCTYPE html><html lang=\"es\"><head> <meta charset=\"UTF-8\"> <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"> <title>Recuperación de Contraseña</title> <style> body { font-family: Arial, sans-serif; background-color: #f4f4f7; margin: 0; padding: 0; color: #51545e; } .email-container { max-width: 600px; margin: 0 auto; padding: 20px; background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 3px rgba(0, 0, 0, 0.16), 0 2px 3px rgba(0, 0, 0, 0.23); } .email-header { text-align: center; padding-bottom: 20px; border-bottom: 1px solid #dcdcdc; } .email-header h1 { margin: 0; font-size: 24px; color: #333333; } .email-body { padding: 20px 0; text-align: center; } .email-body h2 { font-size: 22px; color: #333333; margin: 0 0 20px; } .email-body p { margin: 0 0 20px; font-size: 16px; line-height: 1.5; } .email-body .token { display: inline-block; padding: 10px 20px; font-size: 18px; background-color: #3869d4; color: #ffffff; border-radius: 5px; text-decoration: none; font-weight: bold; letter-spacing: 1.2px; } .email-footer { text-align: center; padding-top: 20px; border-top: 1px solid #dcdcdc; font-size: 14px; color: #999999; } .email-footer a { color: #3869d4; text-decoration: none; } </style></head><body> <div class=\"email-container\"> <div class=\"email-header\"> <h1>Recuperación de Contraseña</h1> </div> <div class=\"email-body\"> <h2>Hola</h2> <p>Hemos recibido una solicitud para restablecer tu contraseña. Usa el siguiente token para proceder:</p> <p class=\"token\">||token||</p> <p>Si no solicitaste este cambio, puedes ignorar este correo electrónico.</p> </div> <div class=\"email-footer\"> <p>Gracias por confiar en nosotros.</p> <p>Si tienes alguna duda, puedes <a href=\"mailto:support@example.com\">contactar a nuestro soporte</a>.</p> </div> </div></body></html>"
    body = body.replace("||token||", str(token))

    # Adjuntar el cuerpo del correo
    html_body = MIMEText(body, "html")
    message.attach(html_body)

    # Iniciar conexión con el servidor SMTP y enviar el correo
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Asegura la conexión
        server.login(email_user, email_password)
        texto = message.as_string()
        server.sendmail(email_user, email_destination, texto)
        server.quit()
        print("Correo enviado con éxito.")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
