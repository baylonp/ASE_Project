import requests, os

from flask import Flask, request, make_response, jsonify
from requests.exceptions import ConnectionError, HTTPError
from werkzeug.exceptions import NotFound

ALLOWED_MATH_OPS = ['add', 'sub', 'mul', 'div', 'mod', 'random', 'reduce', 'last', 'crash']
ALLOWED_STR_OPS = ['lower', 'upper', 'concat', 'last', 'crash']

#CHANGE URLS TO MATCH THE NAMES AND PORTS OF THE SERVICES IN THE DOCKER-COMPOSE FILE
STRING_URL = 'http://string:5000'
CALC1_URL = 'http://calc1:5000'
CALC2_URL = 'http://calc2:5000'
DB_MANAGER_URL = 'http://db-manager:5000'


ids = {} #CAREFUL, THIS IS NOT FOR MULTIUSER AND MULTITHREADING, JUST FOR DEMO PURPOSES

app = Flask(__name__, instance_relative_config=True)

def create_app():
    return app

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, NotFound) and e.code == 404:
        return make_response('Not found\n', 404)
    os._exit(0)

@app.route('/calc/<op>')
def math(op):
    a = request.args.get('a')
    b = request.args.get('b')
    if op not in ALLOWED_MATH_OPS:
        return make_response('Invalid operation\n', 404)
    try:
        C_URL=getCalcURL()
        if({op} == 'crash'):
            URL = C_URL + f'/crash'
        else:
            URL = C_URL + f'/{op}?a={a}&b={b}'
        x = requests.get(URL)
        x.raise_for_status()
        res = x.json()
        return res
    except (ConnectionError):
        try:
            C_URL=getCalcURL()
            if({op} == 'crash'):
                URL = C_URL + f'/crash'
            else:
                URL = C_URL + f'/{op}?a={a}&b={b}'
            x = requests.get(URL)
            x.raise_for_status()
            res = x.json()
        except ConnectionError:
            return make_response('Calc service is down\n', 404)
        except HTTPError:
            return make_response('Invalid input\n', 400)

        return res


def getCalcURL():
    id = ids.get('id')
    if id is None:
        id = 0
    id = id + 1
    ids.update({'id':id})
    if id %2 == 0:
        return CALC1_URL
    else:
        return CALC2_URL

@app.route('/str/<op>')
def string(op):
    a = request.args.get('a', type=str)
    b = request.args.get('b', type=str)
    if op not in ALLOWED_STR_OPS:
        return make_response('Invalid operation\n', 404)
    
    if op == 'lower' or op == 'upper':
        json_response = string_request(STRING_URL + f'/{op}?a={a}')
    elif op == 'crash':
        json_response = string_request(STRING_URL + f'/crash')
    else:
        json_response = string_request(STRING_URL + f'/{op}?a={a}&b={b}')
    return json_response

def string_request(URL_API):
    x = requests.get(URL_API)
    x.raise_for_status()
    return x.json()
