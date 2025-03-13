import time
import requests
import tls_client
import random
from console import Console
from datetime import datetime
from colorama import Fore, Style
import time
import requests
import tls_client
import random
import threading
from datetime import datetime
from colorama import Fore, Style
from queue import Queue

API_URL = "https://api.online-disposablemail.com/api/latest/code"
API_HOST = "http://127.0.0.1:5000"

def twocaptchasolver():
    max_attempts = 50
    for attempt in range(max_attempts):
        try:
            if attempt > 0: 
                print(f"Retrying in 3 seconds... (Attempt {attempt}/{max_attempts})")
                time.sleep(3)

            params = {"url": "https://streamlabs.com/slid/signup", "sitekey": "0x4AAAAAAACELUBpqiwktdQ9"}
            response = requests.get(f"{API_HOST}/turnstile", params=params, timeout=120)

            if response.status_code == 200:
                result = response.json()
                if result["status"] == "success": 
                    return result["result"]
                else: 
                    print(f"Turnstile-Solver failed: {result.get('error')}")
            else: 
                print(f"Error from Turnstile-Solver: HTTP {response.status_code}")
        except requests.RequestException as e: 
            print(f"Network error occurred: {str(e)}")
        except Exception as e: 
            print(f"An unexpected error occurred: {str(e)}")

    print("Max attempts reached. Could not solve captcha.")
    return None

def fetch_email_otp(order_id):
    while True:
        response = requests.get(f"{API_URL}?orderId={order_id}")
        data = response.json()

        if data.get("code") == 200:
            otp_code = data["data"].get("code")
            email_content = data["data"].get("content")

            if otp_code:
                return otp_code  

        time.sleep(5)  


def extract_order_id(url):
    if "orderId=" in url:
        return url.split("orderId=")[-1]
    return None

def load_emails():
    emails = []
    with open("gmail.txt", "r") as file:
        for line in file:
            parts = line.strip().split("----")
            if len(parts) == 2:
                email, order_id_url = parts
                order_id = extract_order_id(order_id_url)
                if order_id:
                    emails.append((email, order_id))
    return emails

def remove_processed_email(email):
    with open("gmail.txt", "r") as file:
        lines = file.readlines()

    with open("gmail.txt", "w") as file:
        for line in lines:
            if not line.startswith(email):
                file.write(line)

def creator(email, order_id, queue):

    ses = tls_client.Session(client_identifier="chrome_131", random_tls_extension_order=True)


    captcha_token = twocaptchasolver()
    if not captcha_token:
        return False

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "priority": "u=1, i",
        "referer": "https://streamlabs.com/slid/signup",
        "sec-ch-ua": '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"',
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
    }
    ses.get('https://streamlabs.com/api/v5/available-features', headers=headers)
    xsrf = ses.cookies.get('XSRF-TOKEN')

    if not xsrf:
        return False

    ses.headers.update({
        'accept': 'application/json, text/plain, */*',
        'cache-control': 'no-cache',
        'client-id': '419049641753968640',
        'content-type': 'application/json',
        'origin': 'https://streamlabs.com',
        'referer': 'https://streamlabs.com/',
        'x-xsrf-token': xsrf,
    })

    json_data = {
        'email': email,
        'username': '',
        'password': 'Jignewah382ry83#',
        'agree': True,
        'agreePromotional': False,
        'dob': '',
        'captcha_token': captcha_token,
        'locale': 'en-US',
    }

    response = ses.post('https://api-id.streamlabs.com/v1/auth/register', json=json_data)
    time_str = datetime.now().strftime("%H:%M:%S")
    if response.status_code == 200:
        print(f"{Fore.LIGHTBLACK_EX}[{Fore.WHITE}{time_str}{Fore.LIGHTBLACK_EX}] {Fore.WHITE}[{Fore.BLUE}/{Fore.WHITE}]{Style.RESET_ALL} {Fore.BLUE}Created Streamlabs Acc{Style.RESET_ALL} {Fore.BLUE}>{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}{email}{Style.RESET_ALL}")
        return True, xsrf, ses 
    else:
        print(f"❌ Failed to create account for {email}: {response.text}")
        return False, None, None

def verifier(xsrf, otp, email, ses):
    url = "https://api-id.streamlabs.com/v1/users/@me/email/verification/confirm"
    payload = {"code": otp, "email": email, "tfa_code": ""}
    ses.headers.update({"x-xsrf-token": xsrf})
    response = ses.post(url, json=payload)
    
    time_str = datetime.now().strftime("%H:%M:%S")  # Get current time
    
    if response.status_code == 204:
        with open("accs.txt", 'a') as f:
            f.write(f"{email}:Jignewah382ry83#\n")
        
        print(f"{Fore.LIGHTBLACK_EX}[{Fore.WHITE}{time_str}{Fore.LIGHTBLACK_EX}] {Fore.WHITE}[{Fore.GREEN}+{Fore.WHITE}]{Style.RESET_ALL} {Fore.GREEN}Verified{Style.RESET_ALL} {Fore.BLUE}-->{Style.RESET_ALL} {Fore.LIGHTBLACK_EX}{email}{Style.RESET_ALL}")
        return True
    else:
        print(f"{Fore.LIGHTBLACK_EX}[{Fore.WHITE}{time_str}{Fore.LIGHTBLACK_EX}] {Fore.RED}[❌]{Style.RESET_ALL} {Fore.RED}Verification failed{Style.RESET_ALL} {Fore.BLUE} > {Style.RESET_ALL} {Fore.LIGHTBLACK_EX}{email}{Style.RESET_ALL}: {response.text}")
        return False


def process_email(email, order_id, queue):
    success, xsrf, ses = creator(email, order_id, queue)
    if success:
        otp = fetch_email_otp(order_id)
        if otp and verifier(xsrf, otp, email, ses):
            remove_processed_email(email)
    else:
        with open("failed.txt", "a") as f:
            f.write(f"{email},{order_id}\n")

def worker(queue):
    while not queue.empty():
        email, order_id = queue.get()
        process_email(email, order_id, queue)
        queue.task_done()

def main():
    emails = load_emails()
    queue = Queue()
    for email, order_id in emails:
        queue.put((email, order_id))

    threads = []
    for _ in range(1):  # 3 Threads
        thread = threading.Thread(target=worker, args=(queue,))
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    main()
