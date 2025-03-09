import http.server
import socketserver
import threading
import time
import json
import urllib.parse  # For parsing query parameters
import prompt
from prompt import main, open_ai_call

PORT = 8080

class ThreadedHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Logging
        thread_id = threading.get_ident()
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"Thread {thread_id} handling request at {current_time}")

        # Parse query parameters
        query_string = urllib.parse.urlparse(self.path).query
        query_params = urllib.parse.parse_qs(query_string)
        #comment below out to test in prod
        #query_params = {'prompts': 'V6PNSC80LL.COM,B9U5R3RJMPP.COM,YM5R99EX5Q8.COM,MBSIGLGFQIH2.COM,GSJZNQCOHIKO.COM,VEG2671WMX88.COM,DLNOYYVQSOZHH.COM,BFZFLQEJOHXMQ.COM,AJFSZWOMNHDFCYY.COM,EXAGQLXTMOPSFT8.COM,FWOGZPAGLGOVLIMY.COM,JVRRMMKYEJDEYLCQ.COM,dell.com,LKLHJONIUDKKHCWO.COM,CADDBSGSCNYDZOH5F.COM,CEUNNFOHGWJYAUA9H.COM,NQZHTFHRMYMTVBQJE.COM,OVLREWGRHHVAJBOTX.COM,OTPWFJOKPOZOOMNK2O.COM,CNEISZDKHZEKQEUBUT.COM,EMUXMJDBTNWCQRFN0G.COM,OWASALWIGURWYVNNPV.COM,PMNYPARTDBVYHCZDJS.COM,04F645A5.COM,15AF64DD.INFO,2AF14345.INFO,2518F789.COM,CFAOBN.COM,QQQCLQFO.CC,HYEHGNR.NET,amazon.com,WWW.XN--ZALGO075952-SJGB60AIGHL2I8JC3B0A2A97FTBLL0CZA.COM,WWW.XN--ZALGO003446-SJGB60AIGHL2I8JC3B0A2A97FTBLL0CZA.COM,WWW.XN--ZALGO012841-SJGB60AIGHL2I8JC3B0A2A97FTBLL0CZA.COM,WWW.XN--ZALGO029243-SJGB60AIGHL2I8JC3B0A2A97FTBLL0CZA.COM,CLIENTALALAXP.MN,CLIENTALNOTHING.ME,USERALCLICLIENT.ME,AGENTCLIENTCLIENT.ME,JSCJSCAXPCLIALLOW.ME,JSCCLIENTAGENTDISA.ME,DISAALALLOWDISALLOW.ME,QUJFVNN.TO,CRWKBMX.TW,OLKQXMAEUIWYX.XXX,BPWENCSDVRJXJI.PRO,pop.imvhhht.ru,pop.hrfomio.ru,pop.jkkjymtb.com,espn.com,gmail.com,bose.com', 'whiteleafuc': 'WLUC1'}

        # Check if JSON data is provided in the query
        if 'prompts' in query_params:
            try:
                # Process the JSON data
                case, data = parse_data(query_params)

                #call prompt.py
                ai_response=call_prompt(case, data)
                print(f'(ai_response={ai_response}')

                # Send response
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"status": "success", "data": ai_response}
                self.wfile.write(json.dumps(response).encode())
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"status": "error", "message": "Invalid JSON data"}
                self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"status": "error", "message": "No JSON data provided"}
            self.wfile.write(json.dumps(response).encode())

def parse_data(json_data):

    # Split the 'prompts' string into a list
    values_list = json_data['prompts'].split(',')  # Split on commas

    # Get the 'whiteleafuc' string value
    prompt_key = json_data['whiteleafuc']

    print("List from 'prompts':", values_list)
    print("String from 'whiteleafuc':", prompt_key)
    return(prompt_key, values_list)

#call prompt.py   sdf 
def call_prompt(case, data):
    response=main(case, data)
    print(response)

    return response

#Threading functionality
class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    pass

#start server and stay running
def start_server():
    server = ThreadedHTTPServer(("0.0.0.0", PORT), ThreadedHTTPRequestHandler)
    print(f"Server started on port {PORT}")
    server.serve_forever()

#Call server start
if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server)
    server_thread.daemon = True
    server_thread.start()

# if Ctrl + C, stop server
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Server is shutting down...")