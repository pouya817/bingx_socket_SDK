import json
import time
import requests
import websocket
import gzip
import io
import hmac
from hashlib import sha256
import threading

class WebSocketClient:
    def __init__(self, subscribe_url, channel_name):
        self.subscribe_url = subscribe_url
        self.channel_name = channel_name
        self.ws = None
        self.websocket_thread = None

    def on_message(self, ws, message):
        compressed_data = gzip.GzipFile(fileobj=io.BytesIO(message), mode='rb')
        decompressed_data = compressed_data.read()
        utf8_data = decompressed_data.decode('utf-8')
        if utf8_data == 'Ping': # this is very important , if you receive 'Ping' you need to send 'Pong'
           ws.send('Pong')
        else:
            print(utf8_data)  #this is the message you need

    def on_error(self, ws, error):
        print(f"WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print('The connection is closed!')

    def on_open(self, ws):
        print('WebSocket connected')
        subStr = json.dumps(self.channel_name)
        ws.send(subStr)
        print('Subscribed to :', subStr)

    def start(self):
        self.ws = websocket.WebSocketApp(
            self.subscribe_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        self.ws.on_open = self.on_open
        self.websocket_thread = threading.Thread(target=self.ws.run_forever)
        self.websocket_thread.start()

    def stop(self):
        if self.ws:
            self.ws.close()
        if self.websocket_thread:
            self.websocket_thread.join()

class WebSocketManager:
    def __init__(self, subscribe_url, channel_name):
        self.client = WebSocketClient(
            subscribe_url=subscribe_url,
            channel_name=channel_name
        )
        self.client.start()

    def close_connection(self):
        self.client.stop()


class BingxWS:
    def __init__(self, subscribe_url:str, channel:str):
        self.url = subscribe_url
        self.channel = channel
        self.ws = None


    @classmethod
    def create_user(cls,APIKEY, SECRETKEY):
        BASE_BINGX_URLS = 'https://open-api.bingx.com'
        APIKEY = APIKEY
        SECRETKEY = SECRETKEY

        def get_listen_key(api_key, secret_key):
            bingx = BingxEndpoints(api_key=api_key, secret_key=secret_key)
            response = bingx.get_listen_keys()
            return response

        class BingxEndpoints(object):

            def __init__(self, api_key: str, secret_key: str):
                self.api_key: str = api_key
                self.secret_key: str = secret_key

            def get_listen_keys(self):
                # BASE_BINGX_URLS = 'https://open-api.bingx.com'
                path = '/openApi/user/auth/userDataStream'
                method = "POST"
                return self._request(method=method, path=path, query_params={})

            def _request(self, method: str, path: str, query_params: dict) -> dict:
                parse_query_params = self.parse_query_params(query_params)
                bingx_sign = self.get_sign(self.secret_key, parse_query_params)
                url = f'{BASE_BINGX_URLS}{path}?{parse_query_params}&signature={bingx_sign}'
                headers = {'X-BX-APIKEY': self.api_key}
                response = requests.request(method, url, headers=headers, data={})
                return response.json()

            @staticmethod
            def parse_query_params(params_map: dict) -> str:
                sorted_keys = sorted(params_map)
                params_str = '&'.join(['%s=%s' % (x, params_map[x]) for x in sorted_keys])
                return params_str + '&timestamp=' + str(int(time.time() * 1000))

            @staticmethod
            def get_sign(api_secret: str, payload) -> str:
                return hmac.new(api_secret.encode('utf-8'), payload.encode('utf-8'), digestmod=sha256).hexdigest()

        return get_listen_key(api_key=APIKEY, secret_key=SECRETKEY)


