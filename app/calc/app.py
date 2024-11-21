from flask import Flask, request, make_response, jsonify
import random, time, os, threading, redis


app = Flask(__name__)
r = redis.Redis(host='db', port=6379, decode_responses=True)

@app.route('/add')
def add():
    a = request.args.get('a', type=float)
    b = request.args.get('b', type=float)
    if a and b:
        save_last("add",(a,b),a+b)
        return make_response(jsonify(s=a+b), 200) #HTTP 200 OK
    else:
        return make_response('Invalid input\n', 400) #HTTP 400 BAD REQUEST

@app.route('/sub')
def sub():
    a = request.args.get('a', type=float)
    b = request.args.get('b', type=float)
    if a and b:
        save_last("sub",(a,b),a-b)
        return make_response(jsonify(s=a-b), 200)

@app.route('/mul')
def mul():
    a = request.args.get('a', type=float)
    b = request.args.get('b', type=float)
    if a and b:
        save_last("mul",(a,b),a*b)
        return make_response(jsonify(s=a*b), 200)
    else:
        return make_response('Invalid input\n', 400)

@app.route('/div')
def div():
    a = request.args.get('a', type=float)
    b = request.args.get('b', type=float)
    if a and b:
        if b == 0:
            return make_response('Division by zero\n', 400)
        save_last("div",(a,b),a/b)
        return make_response(jsonify(s=a/b), 200)
    else:
        return make_response('Invalid input\n', 400)

@app.route('/mod')
def mod():
    a = request.args.get('a', type=float)
    b = request.args.get('b', type=float)
    if a and b:
        if b == 0:
            return make_response('Division by zero\n', 400)
        save_last("mod",(a,b),a%b)
        return make_response(jsonify(s=a%b), 200)
    else:
        return make_response('Invalid input\n', 400)

@app.route('/random')
def rand():
    a = request.args.get('a', type=int)
    b = request.args.get('b', type=int)
    if a and b:
        if a > b:
            return make_response('Invalid input\n', 400)
        res = random.randint(a, b)
        save_last("random",(a,b),res)
        return make_response(jsonify(s=res), 200)
    else:
        return make_response('Invalid input\n', 400)

@app.route('/reduce')
def reduce():
    op = request.args.get('op', type=str)
    lst = request.args.get('lst', type=str)
    if op and lst:
        lst = eval(lst)
        if op == 'add':
            res = sum(lst)
            response =  make_response(jsonify(s=res), 200)
        elif op == 'sub':
            res = lst[0] - sum(lst[1:])
            response = make_response(jsonify(s=res), 200)
        elif op == 'mul':
            res = 1
            for i in lst:
                res *= i
            response = make_response(jsonify(s=res), 200)
        elif op == 'div':
            res = lst[0]
            for i in lst[1:]:
                if i == 0:
                    return make_response('Division by zero\n', 400)
                res /= i
            response = make_response(jsonify(s=res), 200)
        else:
            return make_response(f'Invalid operator: {op}', 400)
        save_last("reduce",(op,lst),res)
        return response
    else:
        return make_response('Invalid operator\n', 400)

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