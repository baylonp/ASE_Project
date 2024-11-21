from flask import Flask, request, make_response, jsonify
import time, os, threading, redis

app = Flask(__name__)

r = redis.Redis(host='db', port=6379, decode_responses=True)

@app.route('/concat')
def concat():
    a = request.args.get('a', type=str)
    b = request.args.get('b', type=str)
    if a and b:
        res = a+b
        save_last("concat",(a,b),res)
        return make_response(jsonify(s=res), 200)
    else:
        return make_response('Invalid input\n', 400)

@app.route('/upper')
def upper():
    a = request.args.get('a', 0, type=str)
    res = a.upper()
    save_last("upper","("+a+")",res)
    return make_response(jsonify(s=res), 200)

@app.route('/lower')
def lower():
    a = request.args.get('a', 0, type=str)
    res = a.lower()
    save_last("lower","("+a+")",res)
    return make_response(jsonify(s=res), 200)

@app.route('/crash')
def crash():
    def close():
        time.sleep(1)
        os._exit(0)
    thread = threading.Thread(target=close)
    thread.start()
    ret = str(request.host) + " crashed"
    return make_response(jsonify(s=ret), 200)

def save_last(op,args,res):
    dict_to_send = {"op": op, "args": args, "res": res}
    timestamp = time.time()
    r.set(timestamp, str(dict_to_send))

if __name__ == '__main__':
    app.run(debug=True)