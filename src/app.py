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

if __name__=="__main__":
    app.run(host='0.0.0.0',port=9009,debug=True)