from flask import Flask,render_template,redirect,request,session
from web3 import Web3,HTTPProvider
import json

UserManagementArtifactPath="../build/contracts/UserManagement.json"
blockchainServer="http://127.0.0.1:7545"

def connectWithContract(wallet,artifact=UserManagementArtifactPath):
    web3=Web3(HTTPProvider(blockchainServer)) # it is connecting with server
    print('Connected with Blockchain Server')

    if (wallet==0):
        web3.eth.defaultAccount=web3.eth.accounts[0]
    else:
        web3.eth.defaultAccount=wallet
    print('Wallet Selected')

    with open(artifact) as f:
        artifact_json=json.load(f)
        contract_abi=artifact_json['abi']
        contract_address=artifact_json['networks']['5777']['address']
    
    contract=web3.eth.contract(abi=contract_abi,address=contract_address)
    print('Contract Selected')
    return contract,web3

app=Flask(__name__)
app.secret_key="M@keskilled0"

@app.route('/')
def homePage():
    return render_template('index.html')

@app.route('/login')
def loginPage():
    return render_template('login.html')

@app.route('/signup')
def signupPage():
    return render_template('signup.html')

@app.route('/signupForm',methods=['POST'])
def signupForm():
    wallet=request.form['wallet']
    name=request.form['username']
    email=request.form['email']
    password=request.form['password']
    role=request.form['role']
    contract,web3=connectWithContract(0)
    try:
        if role=="doctor":
            license=request.form['license']
            specialization=request.form['specialization']
            tx_hash=contract.functions.addDoctor(wallet,name,password,email,license,specialization).transact()
            web3.eth.waitForTransactionReceipt(tx_hash)
        elif role=="patient":
            tx_hash=contract.functions.addPatient(wallet,name,password,email).transact()
            web3.eth.waitForTransactionReceipt(tx_hash)
        return render_template("signup.html",res="account successfully created")
    except Exception as e:
        print(e)
        return render_template("signup.html",err=e)

@app.route('/loginForm',methods=['POST'])
def loginForm():
    email=request.form['email']
    password=request.form['password']
    role=request.form['role']
    contract,web3=connectWithContract(0)
    try:
        if role=="admin":
            response=contract.functions.validateAdmin(email,password).call()
            if response==True:
                return render_template('login.html',res="admin login successful")
            else:
                return render_template('login.html',err='invalid admin details')
        elif role=="doctor":
            response=contract.functions.doctorLogin(email,password).call()
            if response==True:
                return render_template('login.html',res='doctor login successful')
            else:
                return render_template('login.html',err='doctor login failed')
        elif role=="patient":
            response=contract.functions.patientLogin(email,password).call()
            if response==True:
                return render_template('login.html',res='patient login successful')
            else:
                return render_template('login.html',err='patient login failed')
    except Exception as e:
        print(e)
        return render_template('login.html',err=e)


if __name__=="__main__":
    app.run(host='0.0.0.0',port=9009,debug=True)