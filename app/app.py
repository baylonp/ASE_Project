from flask import Flask, request, make_response, jsonify


import random 

app = Flask(__name__, instance_relative_config=True)





@app.route('/add')
def add():
    a = request.args.get('a', type=float)
    b = request.args.get('b', type=float)
    if a and b:
        return make_response(jsonify(s=a+b), 200) #HTTP 200 OK
    else:
        return make_response('Invalid input\n', 400) #HTTP 400 BAD REQUEST
    

#Endpoint /sub for subtraction which takes a and b as query paramete.

@app.route('/sub')
def sub():
    a = request.args.get('a', type=float)
    b = request.args.get('b', type=float)
    if a and b:
        return make_response(jsonify(s=a-b), 200) #HTTP 200 OK
    else:
        return make_response('Invalid input\n', 400) #HTTP 400 BAD REQUEST




#Endpoint /mul for multiplication which takes a and b as query parameters.
@app.route('/mul')
def mul():
    a = request.args.get('a', type=float)
    b = request.args.get('b', type=float)
    if a and b:
        return make_response(jsonify(s=a*b), 200) #HTTP 200 OK
    else:
        return make_response('Invalid input\n', 400) #HTTP 400 BAD REQUEST
    
    

#Endpoint /div for division which takes a and b as query parameters. Returns HTTP 400 BAD REQUEST also for division by zero.

@app.route('/div')
def div():
    a = request.args.get('a', type=float)
    b = request.args.get('b', type=float)
    if a and b:
        return make_response(jsonify(s=a/b), 200) #HTTP 200 OK
    else:
        return make_response('Invalid input\n', 400) #HTTP 400 BAD REQUEST
    

#Endpoint /mod for modulo which takes a and b as query parameters. Returns HTTP 400 BAD REQUEST also for division by zero.

@app.route('/mod')
def mod():
    a = request.args.get('a', type=float)
    b = request.args.get('b', type=float)
    if a and b:
        return make_response(jsonify(s=a%b), 200) #HTTP 200 OK
    else:
        return make_response('Invalid input\n', 400) #HTTP 400 BAD REQUEST





#Endpoint /random which takes a and b as query parameters and returns a random number between a and b included. Returns HTTP 400 BAD REQUEST if a is greater than b.

@app.route('/rand')
def rand():
    a = request.args.get('a', type=float)
    b = request.args.get('b', type=float)
    if a and b and (a < b):
        return make_response(jsonify(random.randint(int(a),int(b))), 200) #HTTP 200 OK
    else:
        return make_response('Invalid input\n', 400) #HTTP 400 BAD REQUEST
    


#Endpoint /upper. Return the given string CappTALIZED
@app.route('/upper')
def upper():
    a = request.args.get('a', type=str)
    #b = request.args.get('b', type=float)


    if a : #and b and (a < b):
        return make_response(jsonify(a.upper()), 200) #HTTP 200 OK
    else:
        return make_response('Invalid input\n', 400) #HTTP 400 BAD REQUEST
    

#Endpoint /concat. Return the given string CappTALIZED
@app.route('/concat')
def concat():
    a = request.args.get('a', type=str)
    b = request.args.get('b', type=str)


    if a and b : #and b and (a < b):
        return make_response(jsonify(a + b), 200) #HTTP 200 OK
    else:
        return make_response('Invalid input\n', 400) #HTTP 400 BAD REQUEST



#Endpoint /reduce. sort of online calculator
@app.route('/reduce')
def reduce():
    op = request.args.get('op', type=str)
    lst = request.args.get('lst', type=str)

    lst= eval(lst)

    #def switch(operator):

    if op == "sum":
        return make_response(jsonify(s = sum(lst)), 200) #HTTP 200 OK
'''
    if op and lst : #and b and (a < b):
        return make_response(jsonify(a + b), 200) #HTTP 200 OK
        
        else:
            return make_response('Invalid input\n', 400) #HTTP 400 BAD REQUEST

'''

if __name__ == '__main__':
    app.run(debug=True)
