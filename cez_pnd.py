import urllib.request
import urllib.parse
import http.cookiejar
import logging
import json
import os
import re
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CezPndClient:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.base_url = "https://pnd.cezdistribuce.cz/cezpnd2/external"
        
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'cs-CZ,cs;q=0.9',
            'Origin': 'https://pnd.cezdistribuce.cz',
            'DNT': '1'
        }

    def login(self):
        login_url = "https://cas.cez.cz/cas/login"
        service_url = f"{self.base_url}/dashboard/view"
        params = {'service': service_url}
        full_login_url = f"{login_url}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(full_login_url, headers=self.headers)
            with self.opener.open(req) as res:
                html = res.read().decode('utf-8')

            match = re.search(r'name="execution"\s+value="([^"]+)"', html)
            if not match:
                logger.error("Chyba: Nepodařilo se najít 'execution' token.")
                return False
            
            execution = match.group(1)

            payload = {
                'username': self.email,
                'password': self.password,
                'execution': execution,
                '_eventId': 'submit',
                'geolocation': ''
            }
            
            data = urllib.parse.urlencode(payload).encode('utf-8')
            post_headers = self.headers.copy()
            post_headers['Content-Type'] = 'application/x-www-form-urlencoded'

            req_post = urllib.request.Request(full_login_url, data=data, headers=post_headers, method='POST')
            with self.opener.open(req_post) as res:
                res.read()

            req_final = urllib.request.Request(service_url, headers=self.headers)
            with self.opener.open(req_final) as res:
                res.read()

            cookies_dict = {cookie.name: cookie.value for cookie in self.cj if "cezdistribuce.cz" in cookie.domain}
            if "JSESSIONID" in cookies_dict:
                logger.info("Přihlášení úspěšné.")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Chyba při přihlašování: {e}")
            return False

    def get_data(self):
        # Dynamický výpočet data
        now = datetime.now()
        date_to = now.strftime("%d.%m.%Y 00:00")
        date_from = (now - timedelta(days=2)).strftime("%d.%m.%Y 00:00")
        
        logger.info(f"Stahuji data od {date_from} do {date_to}")
        
        url = f"{self.base_url}/data"
        payload = {
            "format": "chart",
            "idAssembly": -1027,
            "idDeviceSet": "79005",
            "intervalFrom": date_from,
            "intervalTo": date_to,
            "compareFrom": None,
            "opmId": None,
            "electrometerId": None
        }

        headers = self.headers.copy()
        headers.update({
            'Content-Type': 'application/json;charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': f"{self.base_url}/dashboard/view"
        })

        try:
            body = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(url, data=body, headers=headers, method='POST')
            with self.opener.open(req) as res:
                return json.loads(res.read().decode('utf-8'))
        except Exception as e:
            logger.error(f"Chyba při stahování dat: {e}")
            return None

if __name__ == "__main__":
    USER_EMAIL = "PND_USERNAME"
    USER_PASS = "PND_PASSWORD"

    client = CezPndClient(USER_EMAIL, USER_PASS)
    if client.login():
        result = client.get_data()
        if result:
#            script_dir = os.path.dirname(os.path.abspath(__file__))
#            file_path = os.path.join(script_dir, "data.json")
#            with open(file_path, "w", encoding="utf-8") as f:
#                json.dump(result, f, ensure_ascii=False, indent=4)
#            logger.info(f"Hotovo. Data uložena do {file_path}")
            print(json.dumps(result))
