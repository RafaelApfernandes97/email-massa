from flask import Flask, render_template, request, redirect, url_for, jsonify
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import threading
import time
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

email_list = []
progress = {
    'total': 0,
    'sent': 0,
    'failed': 0
}

subject = ""
html_content = ""

def load_recipients(file_path):
    df = pd.read_csv(file_path)
    return df['email'].tolist()

def send_email(to_address, subject, html_content):
    from_address = 'suporte@mais.chat'
    password = 'myuniodjrosioghc'
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587

    msg = MIMEMultipart('alternative')
    msg['From'] = from_address
    msg['To'] = to_address
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_address, password)
        server.sendmail(from_address, to_address, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Falha ao enviar e-mail para {to_address}: {str(e)}")
        return False

def send_bulk_emails():
    global progress
    progress['total'] = len(email_list)
    progress['sent'] = 0
    progress['failed'] = 0
    for recipient in email_list:
        if send_email(recipient, subject, html_content):
            progress['sent'] += 1
        else:
            progress['failed'] += 1
        time.sleep(10)  # Pausa de 5 segundos entre o envio de cada e-mail

@app.route('/', methods=['GET', 'POST'])
def index():
    global email_list, subject, html_content
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(file_path)
                email_list = load_recipients(file_path)
                os.remove(file_path)
        subject = request.form.get('subject')
        html_content = request.form.get('html_content')
    return render_template('index.html', emails=email_list, progress=progress, subject=subject, html_content=html_content)

@app.route('/send_emails')
def send_emails():
    thread = threading.Thread(target=send_bulk_emails)
    thread.start()
    return redirect(url_for('index'))

@app.route('/progress')
def get_progress():
    return jsonify(progress)

if __name__ == "__main__":
    app.run(debug=True)
