from flask import Flask,  jsonify, request
import json

app = Flask(__name__)

fc=open("data/count.txt","r")
count=int(fc.read())
fc.close()

testUser={"name":'shj','age':"18",'event':'hackton'}
users={'2':testUser}
#save data with deleting
#json.dump(users,open("data/users.json","w"))

users=json.load(open("data/users.json"))






@app.route("/register",methods=['POST'])
def newUser():
    global count
    data=request.get_json(force=True)
    user={}
    user['name']=data['name']
    user['age']=data['age']
    user['event']=data['event']
    count+=1

    return "OK"










