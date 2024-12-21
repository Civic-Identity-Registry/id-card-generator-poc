from PIL import Image
import qrcode
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import base64
from io import BytesIO
import string

def generate_key_pair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()

    private_key_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode('utf-8')

    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')

    return private_key_pem, public_key_pem


def generate_login_key():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(16))


def create_id_card(name, dob, id_number, public_key, private_key, photo_path, sex):
    qr_public = qrcode.make(public_key)
    
    login_key = generate_login_key()
    
    buffered_public = BytesIO()
    qr_public.save(buffered_public, format="PNG")
    qr_public_b64 = base64.b64encode(buffered_public.getvalue()).decode()

    with open('template.html', 'r') as file:
        template_front = file.read()
    
    with open('template_back.html', 'r') as file:
        template_back = file.read()

    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    template_front = template_front.replace('{{name}}', name)
    template_front = template_front.replace('{{dob}}', dob)
    template_front = template_front.replace('{{id_number}}', id_number)
    template_front = template_front.replace('{{issue_date}}', current_time)
    template_front = template_front.replace('{{photo_path}}', photo_path)
    template_front = template_front.replace('{{sex}}', sex)
    
    template_front = template_front.replace('id="public-key-qr">', f'id="public-key-qr"><img src="data:image/png;base64,{qr_public_b64}" alt="Public Key QR">')
    template_front = template_front.replace('id="private-key-qr">', f'id="private-key-qr"><div class="login-key">{login_key}</div>')

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--window-size=1240,877')
    chrome_options.add_argument('--force-device-scale-factor=1')
    chrome_options.add_argument('--hide-scrollbars')

    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        temp_front = 'temp_card_front.html'
        with open(temp_front, 'w') as file:
            file.write(template_front)
        
        temp_back = 'temp_card_back.html'
        with open(temp_back, 'w') as file:
            file.write(template_back)

        driver.get(f'file:///{os.path.abspath(temp_front)}')
        driver.implicitly_wait(2)
        front_path = f"{id_number}_ID_Card.png"
        driver.save_screenshot(front_path)

        driver.get(f'file:///{os.path.abspath(temp_back)}')
        driver.implicitly_wait(2)
        back_path = f"{id_number}_ID_Card_back.png"
        driver.save_screenshot(back_path)
        
        os.remove(temp_front)
        os.remove(temp_back)
        
        return front_path, back_path
    finally:
        driver.quit()

name = "John Doe"
dob = "01/01/1990"
id_number = f"CIR-{random.randint(100000, 999999)}"
photo_path = "example.jpg"
private_key, public_key = generate_key_pair()
sex = "Example"

front_path, back_path = create_id_card(name, dob, id_number, public_key, private_key, photo_path, sex)
print(f"ID Card generated:\nFront: {front_path}\nBack: {back_path}")
