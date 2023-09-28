import requests

headers = {
    "Authorization": "BASIC bW1jY2FiZUBpcmlzaGRvZ2Zvb2RzLmNvbTpNZWxpc3NhNDEq",
    "content-type": "application/json",
    "Origin": "https://www.musgravemarketplace.ie",
    "Referer": "https://www.musgravemarketplace.ie/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

r = requests.get("https://www-api.musgravemarketplace.ie/INTERSHOP/rest/WFS/musgrave-MWPIRL-Site/-;loc=en_IE;cur=EUR/customers/-", headers=headers)

auth_token = r.headers.get("authentication-token")
