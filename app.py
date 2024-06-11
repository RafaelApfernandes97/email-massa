from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import threading
import time
import os
from flask_paginate import Pagination, get_page_args

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
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
    try:
        df = pd.read_csv(file_path)
        if 'email' not in df.columns:
            raise KeyError('A coluna "email" não foi encontrada no arquivo CSV.')
        return df['email'].tolist()
    except Exception as e:
        flash(str(e), 'danger')
        return []

def send_email(to_address, subject, html_content):
    from_address = 'your_email@example.com'
    password = 'your_password'
    smtp_server = 'smtp.example.com'
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
    for i, recipient in enumerate(email_list):
        if send_email(recipient, subject, html_content):
            progress['sent'] += 1
        else:
            progress['failed'] += 1
        time.sleep(5)  # Pausa de 5 segundos entre o envio de cada e-mail
        if (i + 1) % 50 == 0:  # Pausa de 5 minutos a cada 50 e-mails
            time.sleep(300)

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

    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page', per_page=10)
    total = len(email_list)
    pagination_emails = email_list[offset:offset + per_page]
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')

    return render_template('index.html', emails=pagination_emails, page=page, per_page=per_page, pagination=pagination, progress=progress, subject=subject, html_content=html_content)

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
