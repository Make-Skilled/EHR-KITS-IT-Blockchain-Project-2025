from flask import Flask,render_template,redirect,request,session
from web3 import Web3,HTTPProvider
import json
import bcrypt
from werkzeug.utils import secure_filename
import os
import hashlib
from datetime import datetime

UserManagementArtifactPath="../build/contracts/UserManagement.json"
EHRArtifactPath="../build/contracts/EHR.json"
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

# Configuration
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure base upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

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
                return redirect("/adminDashboard")
            else:
                return render_template('login.html',err='invalid admin details')
        elif role=="doctor":
            response=contract.functions.doctorLogin(email,password).call()
            if response==True:
                doc=contract.functions.viewDoctorByEmail(email).call()
                print(doc)
                session['docWallet']=doc[0]
                session['docId']=doc[1]
                session['docName']=doc[2]
                session['docEmail']=doc[4]
                session['docLicense']=doc[5]
                session['docSpecial']=doc[6]
                return redirect('/docDashboard')
            else:
                return render_template('login.html',err='doctor login failed')
        elif role=="patient":
            response=contract.functions.patientLogin(email,password).call()
            if response==True:
                pat=contract.functions.viewPatientByEmail(email).call()
                print(pat)
                session['patWallet']=pat[0]
                session['patId']=pat[1]
                session['patName']=pat[2]
                session['patEmail']=pat[4]
                session['patGender']=pat[5]
                session['patPhone']=pat[6]
                session['patAddress']=pat[7]
                session['patPhoto']=pat[8]
                return redirect('/patDashboard')
            else:
                return render_template('login.html',err='patient login failed')
    except Exception as e:
        print(e)
        return render_template('login.html',err=e)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/docDashboard')
def docDashboard():
    doc={}
    doc['name']=session['docName']
    doc['email']=session['docEmail']
    doc['wallet']=session['docWallet']
    doc['id']=session['docId']
    doc['license']=session['docLicense']
    doc['special']=session['docSpecial']
    ehrcontract,web3=connectWithContract(0,EHRArtifactPath)
    contract,web3=connectWithContract(0)
    appointments=ehrcontract.functions.getAllAppointmentIds().call()
    myAppointments=[]
    for appointment in appointments:
        appData=ehrcontract.functions.getAppointment(appointment).call()
        myApp={}
        if(appData[2]==session['docId'] and appData[-1]!='Completed'):
            myApp['appointmentId']=appData[0]
            myApp['patientName']= contract.functions.getPatientNameById(appData[2]).call()
            myApp['date']=appData[3].split('T')[0]
            myApp['time']=appData[3].split('T')[-1]
            myApp['status']=appData[4]
            myAppointments.append(myApp)
    print(myAppointments)
    return render_template('doctor-dashboard.html',doc=doc,appointments=myAppointments)

@app.route('/editDoctorAppointment/<int:appointment_id>', methods=['GET'])
def editDoctorAppointment(appointment_id):
    # Connect to the contract
    ehrcontract, web3 = connectWithContract(0, EHRArtifactPath)
    contract, web3 = connectWithContract(0)

    # Fetch appointment details
    appointment = ehrcontract.functions.getAppointment(appointment_id).call()

    # Fetch doctor and patient details
    doctor = contract.functions.getDoctorNameById(appointment[2]).call()
    patient = contract.functions.getPatientNameById(appointment[1]).call()
    print(doctor,patient)
    # Pass the data to the template
    return render_template('doctor-edit-appointment.html', appointment={
        "id": appointment[0],
        "datetime": appointment[3],
        "status": appointment[4],
    }, doctor=doctor, patient=patient)

@app.route('/updateDoctorAppointment', methods=['POST'])
def updateDoctorAppointment():
    # Get form data
    appointment_id = request.form.get('appointment_id')
    date = request.form.get('date')
    time = request.form.get('time')
    status = request.form.get('status')

    # Combine date and time into a single datetime string
    datetime_str = f"{date}T{time}"

    # Connect to the contract and update the appointment
    contract, web3 = connectWithContract(0, EHRArtifactPath)
    txn = contract.functions.updateAppointmentWithDate(int(appointment_id),status,datetime_str).transact()
    web3.eth.wait_for_transaction_receipt(txn)
    return redirect('/docDashboard')

@app.route('/docAssignedPatients')
def docAssignedPatients():
    ehrcontract,web3=connectWithContract(0,EHRArtifactPath)
    contract,web3=connectWithContract(0)
    appointments=ehrcontract.functions.getAllAppointmentIds().call()
    myAppointments=[]
    for appointment in appointments:
        appData=ehrcontract.functions.getAppointment(appointment).call()
        patientData=contract.functions.viewPatientById(appData[1]).call()
        print(patientData)
        myPatients={}
        if(appData[2]==session['docId']):
            myPatients['id']=patientData[1]
            myPatients['name']= patientData[2]
            myPatients['email']= patientData[4]
            myPatients['gender']=patientData[5]
            myPatients['address']=patientData[6]
            myAppointments.append(myPatients)
    print(myAppointments)
    return render_template('doctor-patients.html',users=myAppointments)

@app.route('/doctorViewPatient/<id>')
def doctorViewPatient(id):
    id=int(id)
    contract,web3=connectWithContract(0)
    patient=contract.functions.viewPatientById(id).call()
    ehrcontract,web3=connectWithContract(0,EHRArtifactPath)
    patientRecord=ehrcontract.functions.getPatientRecord(id).call()
    print(patient,patientRecord)
    data={}
    data['wallet']=patient[0]
    data['id']=patient[1]
    data['name']=patient[2]
    data['email']=patient[4]
    data['gender']=patient[5]
    data['phone']=patient[6]
    data['address']=patient[7]
    data['photo']=patient[8]
    data['record']=patientRecord[0]
    data['age']=patientRecord[1]
    data['date']=patientRecord[2]
    data['healthConditions']=patientRecord[3]
    data['medications']=patientRecord[4]
    data['doctorNotes']=patientRecord[5]
    try:
        medicalRecords=ehrcontract.functions.getMedicalRecords(id).call()
        print(medicalRecords)
        records_dict_list = []
        for record in medicalRecords:
            record_dict = {
                'recordId': record[0],
                'patientId': record[1],
                'filePath': 'static/uploads/'+ record[2],
                'date': record[3],
                'description': record[4]
            }
            records_dict_list.append(record_dict)
        return render_template('doctor-view-patient.html',user=data,records=records_dict_list)
    except:
        records_dict_list = []
        return render_template('doctor-view-patient.html',user=data,records=records_dict_list)

@app.route('/docAppointments')
def docAppointments():
    ehrcontract,web3=connectWithContract(0,EHRArtifactPath)
    contract,web3=connectWithContract(0)
    appointments=ehrcontract.functions.getAllAppointmentIds().call()
    myAppointments=[]
    for appointment in appointments:
        appData=ehrcontract.functions.getAppointment(appointment).call()
        myApp={}
        if(appData[2]==session['docId']):
            myApp['appointmentId']=appData[0]
            myApp['patientName']= contract.functions.getPatientNameById(appData[2]).call()
            myApp['date']=appData[3].split('T')[0]
            myApp['time']=appData[3].split('T')[-1]
            myApp['status']=appData[4]
            myAppointments.append(myApp)
    print(myAppointments)

    return render_template('doctor-appointments.html',appointments=myAppointments)

@app.route('/uploadRecordsByDoctor')
def uploadRecordsByDoctor():
    return render_template('doctor-records.html')

@app.route('/uploadRecordsByDoctorForm',methods=['POST'])
def uploadRecordsByDoctorForm():
    # Retrieve form data
    patientId = request.form['patientId']
    user_photo = request.files['file']
    date = request.form['date']
    description = request.form['description']

    # Create the upload folder if it doesn't exist
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    # Generate a unique filename for the uploaded file
    original_filename = secure_filename(user_photo.filename)
    file_extension = os.path.splitext(original_filename)[1]  # Extract the file extension
    unique_filename = f"{patientId}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}{file_extension}"
    user_photo_path = os.path.join(user_folder, unique_filename)

    # Save the file to the specified directory
    try:
        user_photo.save(user_photo_path)

        # Connect to the smart contract
        contract, web3 = connectWithContract(0, EHRArtifactPath)

        # Add the medical record to the contract
        tx_hash = contract.functions.addMedicalRecord(int(patientId), unique_filename,date,description).transact()
        web3.eth.wait_for_transaction_receipt(tx_hash)

        return render_template('doctor-records.html', res='Record Added Successfully')

    except Exception as e:
        # Handle errors and display a message to the user
        error_message = f"An error occurred: {str(e)}"
        return render_template('doctor-records.html', err=error_message)

@app.route('/patDashboard')
def patDashboard():
    pat={}
    pat['name']=session['patName']
    pat['email']=session['patEmail']
    pat['wallet']=session['patWallet']
    pat['id']=session['patId']
    pat['phone']=session['patPhone']
    pat['gender']=session['patGender']
    pat['address']=session['patAddress']
    pat['photo']=session['patPhoto']
    ehrcontract,web3=connectWithContract(0,EHRArtifactPath)
    contract,web3=connectWithContract(0)
    appointments=ehrcontract.functions.getAllAppointmentIds().call()
    myAppointments=[]
    for appointment in appointments:
        appData=ehrcontract.functions.getAppointment(appointment).call()
        myApp={}
        if(appData[1]==session['patId'] and appData[-1]!='Completed'):
            myApp['appointmentId']=appData[0]
            myApp['doctorName']= contract.functions.getDoctorNameById(appData[2]).call()
            myApp['date']=appData[3].split('T')[0]
            myApp['time']=appData[3].split('T')[-1]
            myApp['status']=appData[4]
            myAppointments.append(myApp)
    print(myAppointments)
    return render_template('patient-dashboard.html',pat=pat,appointments=myAppointments)

@app.route('/patProfile')
def patProfile():
    contract,web3=connectWithContract(0)
    pat=contract.functions.viewPatientByEmail(session['patEmail']).call()
    print(pat)
    session['patWallet']=pat[0]
    session['patId']=pat[1]
    session['patName']=pat[2]
    session['patEmail']=pat[4]
    session['patGender']=pat[5]
    session['patPhone']=pat[6]
    session['patAddress']=pat[7]
    session['patPhoto']=pat[8]
    pat={}
    pat['name']=session['patName']
    pat['email']=session['patEmail']
    pat['wallet']=session['patWallet']
    pat['id']=session['patId']
    pat['phone']=session['patPhone']
    pat['gender']=session['patGender']
    pat['address']=session['patAddress']
    pat['photo']=session['patPhoto']
    return render_template('patient-profile.html',pat=pat)

@app.route('/patEditProfile')
def patEditProfile():
    pat={}
    pat['name']=session['patName']
    pat['email']=session['patEmail']
    pat['wallet']=session['patWallet']
    pat['id']=session['patId']
    pat['phone']=session['patPhone']
    pat['gender']=session['patGender']
    pat['address']=session['patAddress']
    pat['photo']=session['patPhoto']
    print(pat)
    return render_template('patient-edit-profile.html',pat=pat)

@app.route('/patEditForm',methods=["POST"])
def patEditForm():
    fullname=request.form['fullname']
    email=request.form['email']
    wallet=request.form['wallet']
    phone=request.form['phone']
    address=request.form['address']
    gender=request.form['gender']
    print(fullname,email,wallet,phone,address,gender)
    contract,web3=connectWithContract(0)
    try:
        tx_hash=contract.functions.updatePatientByEmail(fullname,email,gender,phone,address).transact()
        web3.eth.waitForTransactionReceipt(tx_hash)
        return redirect('/patProfile')
    except Exception as e:
        print(e)
        return redirect('/patEditProfile')

@app.route('/uploadPatientPhoto',methods=['POST'])
def uploadPatientPhoto():
    user_photo = request.files['user_photo']

    # Create subdirectory path dynamically
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)  # Create folder if it doesn't exist

    # Secure and save files
    user_photo_filename = secure_filename(user_photo.filename)
    
    user_photo_path = os.path.join(user_folder, user_photo_filename)

    # Save files locally or to the specified directory
    user_photo.save(user_photo_path)

    contract,web3=connectWithContract(0)
    try:
        tx_hash=contract.functions.updatePatientPhoto(user_photo_path,session['patEmail']).transact()
        web3.eth.waitForTransactionReceipt(tx_hash)
    except Exception as e:
        print(e)
    return redirect('/patProfile')

@app.route('/patAppointments')
def patAppointments():
    pat={}
    pat['name']=session['patName']
    pat['photo']=session['patPhoto']

    ehrcontract,web3=connectWithContract(0,EHRArtifactPath)
    contract,web3=connectWithContract(0)
    appointments=ehrcontract.functions.getAllAppointmentIds().call()
    myAppointments=[]
    for appointment in appointments:
        appData=ehrcontract.functions.getAppointment(appointment).call()
        myApp={}
        if(appData[1]==session['patId']):
            myApp['appointmentId']=appData[0]
            myApp['doctorName']= contract.functions.getDoctorNameById(appData[2]).call()
            myApp['date']=appData[3].split('T')[0]
            myApp['time']=appData[3].split('T')[-1]
            myApp['status']=appData[4]
            myAppointments.append(myApp)
    print(myAppointments)
    return render_template('patient-appointments.html',pat=pat,appointments=myAppointments)

@app.route('/patRecords')
def patRecords():
    pat={}
    pat['name']=session['patName']
    pat['photo']=session['patPhoto']
    ehrcontract,web3=connectWithContract(0,EHRArtifactPath)
    try:
        medicalRecords=ehrcontract.functions.getMedicalRecords(session['patId']).call()
        records_dict_list = []
        for record in medicalRecords:
            if(record[1]==session['patId']):
                record_dict = {
                    'recordId': record[0],
                    'patientId': record[1],
                    'filePath': 'static/uploads/'+ record[2],
                    'date': record[3],
                    'description': record[4]
                }
                records_dict_list.append(record_dict)
        print(records_dict_list)
        return render_template('patient-medical-records.html',pat=pat,records=records_dict_list)
    except Exception as E:
        records_dict_list = []
        print(records_dict_list)
        print(E)
        return render_template('patient-medical-records.html',records=records_dict_list)

@app.route('/uploadRecordsByPatientForm',methods=['POST'])
def uploadRecordsByPatientForm():
    ehrcontract,web3=connectWithContract(0,EHRArtifactPath)
    contract,web3=connectWithContract(0)
    appointments=ehrcontract.functions.getAllAppointmentIds().call()
    myAppointments=[]
    for appointment in appointments:
        appData=ehrcontract.functions.getAppointment(appointment).call()
        myApp={}
        if(appData[1]==session['patId']):
            myApp['appointmentId']=appData[0]
            myApp['doctorName']= contract.functions.getDoctorNameById(appData[2]).call()
            myApp['date']=appData[3].split('T')[0]
            myApp['time']=appData[3].split('T')[-1]
            myApp['status']=appData[4]
            myAppointments.append(myApp)
    print(myAppointments)

    pat={}
    pat['name']=session['patName']
    pat['photo']=session['patPhoto']
    patientId = session['patId']
    user_photo = request.files['file']
    date = request.form['date']
    description = request.form['description']

    # Create the upload folder if it doesn't exist
    user_folder = os.path.join(app.config['UPLOAD_FOLDER'])
    if not os.path.exists(user_folder):
        os.makedirs(user_folder)

    # Generate a unique filename for the uploaded file
    original_filename = secure_filename(user_photo.filename)
    file_extension = os.path.splitext(original_filename)[1]  # Extract the file extension
    unique_filename = f"{patientId}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}{file_extension}"
    user_photo_path = os.path.join(user_folder, unique_filename)

    # Save the file to the specified directory
    try:
        user_photo.save(user_photo_path)

        # Connect to the smart contract
        contract, web3 = connectWithContract(0, EHRArtifactPath)

        # Add the medical record to the contract
        tx_hash = contract.functions.addMedicalRecord(int(patientId), unique_filename,date,description).transact()
        web3.eth.wait_for_transaction_receipt(tx_hash)

        return render_template('patient-appointments.html', pat=pat, res='Record Added Successfully',appointments=myAppointments)

    except Exception as e:
        # Handle errors and display a message to the user
        error_message = f"An error occurred: {str(e)}"
        return render_template('patient-appointments.html', pat=pat, err=error_message,appointments=myAppointments)

@app.route('/adminDashboard')
def adminDashboard():
    ehrcontract,web3=connectWithContract(0,EHRArtifactPath)
    appointmentsList=ehrcontract.functions.getAllAppointmentIds().call()
    contract,web3=connectWithContract(0)
    appointments = []
    for appointment_id in appointmentsList:
        appointment = ehrcontract.functions.getAppointment(appointment_id).call()
        date, time = appointment[3].split("T")
        appointments.append({
            "id": appointment[0],
            "patient_id": contract.functions.getPatientNameById(appointment[1]).call(),
            "doctor_id": contract.functions.getDoctorNameById(appointment[2]).call(),
            "date": date,
            "time": time,
            "status": appointment[4],
        })
    return render_template('admin-dashboard.html',appointments=appointments)

@app.route('/adminOverview')
def adminOverview():
    contract,web3=connectWithContract(0)
    ehrcontract,web3=connectWithContract(0,EHRArtifactPath)
    doctors=contract.functions.viewAllDoctors().call()
    patients=contract.functions.viewAllPatients().call()
    total_users=len(doctors)+len(patients)
    appointmentIds=ehrcontract.functions.getAllAppointmentIds().call()
    total_appointments=len(appointmentIds)
    appointmentsArray=[]
    total_pending_appointments=0
    for i in appointmentIds:
        appointment=ehrcontract.functions.getAppointment(i).call()
        if(appointment[-1]=='Pending'):
            total_pending_appointments+=1
        dummy_appointment=[]
        dummy_appointment.append(appointment[0])
        dummy_appointment.append(contract.functions.getPatientNameById(appointment[1]).call())
        dummy_appointment.append(contract.functions.getDoctorNameById(appointment[2]).call())
        dummy_appointment.append(appointment[3].split('T')[0])
        dummy_appointment.append(appointment[3].split('T')[1])
        dummy_appointment.append(appointment[4])
        appointmentsArray.append(dummy_appointment)
    recordsArray=ehrcontract.functions.getAllMedicalRecords().call()
    total_records=len(recordsArray)
    records=[]
    for record in recordsArray:
        dummyRecord=[]
        dummyRecord.append(record[0])
        dummyRecord.append(contract.functions.getPatientNameById(record[1]).call())
        dummyRecord.append(record[2])
        dummyRecord.append(record[3])
        dummyRecord.append(record[4])
        records.append(dummyRecord)
    print(records)
    return render_template('admin-overview.html',records=records,total_records=total_records,appointments=appointmentsArray,total_pending_appointments=total_pending_appointments,total_doctors=len(doctors),total_users=total_users,doctors=doctors,patients=patients,total_appointments=total_appointments)

@app.route('/adminUserManagement')
def adminUserManagement():
    contract,web3=connectWithContract(0,EHRArtifactPath)
    patient_ids = contract.functions.getAllPatientIds().call()
    patients = []
    for patient_id in patient_ids:
        patient = contract.functions.getPatientRecord(patient_id).call()
        patients.append({
            "id": patient_id,
            "filename": patient[0],
            "age": patient[1],
            "joined_date": patient[2],
            "health_conditions": patient[3],
            "medications": patient[4],
            "doctor_notes": patient[5],
        })
    return render_template('admin-user-management.html',patients=patients)

@app.route('/adminAppointmentManagement')
def adminAppointmentManagement():
    ehrcontract,web3=connectWithContract(0,EHRArtifactPath)
    appointmentsList=ehrcontract.functions.getAllAppointmentIds().call()
    contract,web3=connectWithContract(0)
    appointments = []
    for appointment_id in appointmentsList:
        appointment = ehrcontract.functions.getAppointment(appointment_id).call()
        date, time = appointment[3].split("T")
        appointments.append({
            "id": appointment[0],
            "patient_id": contract.functions.getPatientNameById(appointment[1]).call(),
            "doctor_id": contract.functions.getDoctorNameById(appointment[2]).call(),
            "date": date,
            "time": time,
            "status": appointment[4],
        })
    return render_template('admin-appointment-management.html',appointments=appointments)

@app.route('/editAppointment/<int:appointment_id>', methods=['GET'])
def editAppointment(appointment_id):
    # Connect to the contract
    ehrcontract, web3 = connectWithContract(0, EHRArtifactPath)
    contract, web3 = connectWithContract(0)

    # Fetch appointment details
    appointment = ehrcontract.functions.getAppointment(appointment_id).call()

    # Fetch doctor and patient details
    doctor = contract.functions.getDoctorNameById(appointment[2]).call()
    patient = contract.functions.getPatientNameById(appointment[1]).call()
    print(doctor,patient)
    # Pass the data to the template
    return render_template('admin-edit-appointment.html', appointment={
        "id": appointment[0],
        "datetime": appointment[3],
        "status": appointment[4],
    }, doctor=doctor, patient=patient)

@app.route('/updateAppointment', methods=['POST'])
def updateAppointment():
    # Get form data
    appointment_id = request.form.get('appointment_id')
    date = request.form.get('date')
    time = request.form.get('time')
    status = request.form.get('status')

    # Combine date and time into a single datetime string
    datetime_str = f"{date}T{time}"

    # Connect to the contract and update the appointment
    contract, web3 = connectWithContract(0, EHRArtifactPath)
    txn = contract.functions.updateAppointmentWithDate(int(appointment_id),status,datetime_str).transact()
    web3.eth.wait_for_transaction_receipt(txn)
    return redirect('/adminAppointmentManagement')

@app.route('/approveAppointment/<int:appointment_id>', methods=['POST'])
def approveAppointment(appointment_id):
    try:
        # Connect to the contract
        contract, web3 = connectWithContract(0, EHRArtifactPath)

        # Call the smart contract's cancellation function
        txn = contract.functions.updateAppointment(appointment_id, "Accepted").transact({"from": web3.eth.default_account})
        web3.eth.wait_for_transaction_receipt(txn)

        return {"success": True}, 200
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "error": str(e)}, 500
    
@app.route('/cancelAppointment/<int:appointment_id>', methods=['POST'])
def cancelAppointment(appointment_id):
    try:
        # Connect to the contract
        contract, web3 = connectWithContract(0, EHRArtifactPath)

        # Call the smart contract's cancellation function
        txn = contract.functions.updateAppointment(appointment_id, "Canceled").transact({"from": web3.eth.default_account})
        web3.eth.wait_for_transaction_receipt(txn)

        return {"success": True}, 200
    except Exception as e:
        print(f"Error: {e}")
        return {"success": False, "error": str(e)}, 500
    
@app.route('/adminMedicalRecords')
def adminMedicalRecords():
    contract,web3=connectWithContract(0)
    ehrcontract,web3=connectWithContract(0,EHRArtifactPath)
    try:
        medicalRecords=ehrcontract.functions.getAllMedicalRecords().call()
        records_dict_list = []
        for record in medicalRecords:
            record_dict = {
                'recordId': record[0],
                'patientId': record[1],
                'patientName': contract.functions.getPatientNameById(record[1]).call(),
                'filePath': 'static/uploads/'+ record[2],
                'date': record[3],
                'description': record[4]
            }
            records_dict_list.append(record_dict)
        print(records_dict_list)
    except:
        records_dict_list=[]

    return render_template('admin-medical-records.html',records=records_dict_list)

@app.route('/adminSystemSettings')
def adminSystemSettings():
    return render_template('admin-system-settings.html')

@app.route('/adminAddUser')
def adminAddUser():
    contract,web3=connectWithContract(0)
    patientList=contract.functions.viewAllPatients().call()
    formatted_patientList = [
        {
            "address": item[0],
            "id": item[1],
            "name": item[2],
            "password": item[3],
            "email": item[4],
            "gender": item[5],
            "phone": item[6],
            "address_details": item[7],
            "image_path": item[8],
            "status": item[9]
        }
        for item in patientList
    ]
    print(formatted_patientList)
    return render_template('admin-add-user.html',users=formatted_patientList)

@app.route('/adminAddUserForm',methods=['POST'])
def adminAddUserForm():
    contract,web3=connectWithContract(0)
    patientList=contract.functions.viewAllPatients().call()
    formatted_patientList = [
        {
            "address": item[0],
            "id": item[1],
            "name": item[2],
            "password": item[3],
            "email": item[4],
            "gender": item[5],
            "phone": item[6],
            "address_details": item[7],
            "image_path": item[8],
            "status": item[9]
        }
        for item in patientList
    ]
    if request.method == 'POST':
        # Retrieve form data
        patient_id = request.form.get('patient_id')
        name = request.form.get('name')
        email = request.form.get('email')
        gender = request.form.get('gender')
        phone = request.form.get('phone')
        address = request.form.get('address')
        status = request.form.get('status')
        age = request.form.get('age')
        joined_date = request.form.get('joined_date')
        health_conditions = request.form.get('health_conditions')
        medications = request.form.get('medications')
        doctor_notes = request.form.get('doctor_notes')

        # Process uploaded file
        uploaded_file = request.files.get('health_records')
        if uploaded_file:
            # Secure the filename and save it to the UPLOAD_FOLDER
            filename = os.path.join(app.config['UPLOAD_FOLDER'], uploaded_file.filename)
            uploaded_file.save(filename)
        else:
            if uploaded_file:
                return(render_template('admin-add-user.html',users=formatted_patientList,err='invalid files'))
        
        # (Optional) Save form data to a database here
        print(filename,patient_id,name,email,gender,phone,address,status,age,joined_date,health_conditions,medications,doctor_notes)
        
        contract,web3=connectWithContract(0,EHRArtifactPath)
        try:
            tx_hash=contract.functions.addPatientRecord(filename,int(patient_id),int(age),joined_date,health_conditions,medications,doctor_notes).transact()
            web3.eth.waitForTransactionReceipt(tx_hash)
            return render_template('admin-add-user.html',users=formatted_patientList,res='User Added successfully')
        except Exception as E:
            return render_template('admin-add-user.html',users=formatted_patientList,err=E)
        
@app.route("/delete_patient/<int:patient_id>", methods=["POST"])
def delete_patient(patient_id):
    contract,web3=connectWithContract(0,EHRArtifactPath)
    # Call the smart contract's deletePatientRecord function
    txn = contract.functions.deletePatientRecord(patient_id).transact()
    web3.eth.wait_for_transaction_receipt(txn)
    return redirect('/adminUserManagement')

@app.route("/edit_patient/<int:patient_id>", methods=["GET", "POST"])
def edit_patient(patient_id):
    if request.method == "POST":
        # Get updated data from the form
        updated_data = {
            "age": int(request.form["age"]),
            "joined_date": request.form["joined_date"],
            "health_conditions": request.form["health_conditions"],
            "medications": request.form["medications"],
            "doctor_notes": request.form["doctor_notes"],
        }

        contract,web3=connectWithContract(0,EHRArtifactPath)

        # Call the smart contract's editPatientRecord function
        txn = contract.functions.editPatientRecord(
            patient_id,
            updated_data["age"],
            updated_data["joined_date"],
            updated_data["health_conditions"],
            updated_data["medications"],
            updated_data["doctor_notes"],
        ).transact()

        web3.eth.wait_for_transaction_receipt(txn)

        return redirect('/adminUserManagement')

    contract,web3=connectWithContract(0,EHRArtifactPath)
    # Fetch existing patient data for the form
    patient = contract.functions.getPatientRecord(patient_id).call()
    print(patient)
    return render_template("admin-edit-patient.html", patient=patient)

@app.route('/adminAddAppointment')
def adminAddAppointment():
    contract,web3=connectWithContract(0)
    patientList=contract.functions.viewAllPatients().call()

    contract,web3=connectWithContract(0,EHRArtifactPath)

    formatted_patientList = [
        {
            "address": item[0],
            "id": item[1],
            "name": item[2],
            "password": item[3],
            "email": item[4],
            "gender": item[5],
            "phone": item[6],
            "address_details": item[7],
            "image_path": item[8],
            "status": item[9]
        }
        for item in patientList
    ]
    
    for i in formatted_patientList:
        patientRecord=contract.functions.getPatientRecord(i['id']).call()
        print(patientRecord)
        i['recordPath']=patientRecord[0]
        i['age']=patientRecord[1]
        i['date']=patientRecord[2]
        i['health_conditions']=patientRecord[3]
        i['medications']=patientRecord[4]
        i['doctor_notes']=patientRecord[5]
    
    print(formatted_patientList)    
    contract,web3=connectWithContract(0)
    doctorsList=contract.functions.viewAllDoctors().call()
    keys = ["address", "id", "name", "password", "email", "license", "specialization", "status"]

    # List of dictionaries (in case you have multiple entries in the list)
    formatted_data = [
        dict(zip(keys, record)) for record in doctorsList
    ]

    print(formatted_data)
    return render_template('admin-add-appointment.html',users=formatted_patientList,doctors=formatted_data)

@app.route('/adminAddAppointmentForm',methods=['POST'])
def adminAddAppointmentForm():
    patient_id=int(request.form['patient_id'])
    doctor_id=int(request.form['doctor_id'])
    appointment_date=request.form['appointment_date']
    print(patient_id,doctor_id,appointment_date)

    contract,web3=connectWithContract(0)
    patientList=contract.functions.viewAllPatients().call()

    contract,web3=connectWithContract(0,EHRArtifactPath)

    formatted_patientList = [
        {
            "address": item[0],
            "id": item[1],
            "name": item[2],
            "password": item[3],
            "email": item[4],
            "gender": item[5],
            "phone": item[6],
            "address_details": item[7],
            "image_path": item[8],
            "status": item[9]
        }
        for item in patientList
    ]
    
    for i in formatted_patientList:
        patientRecord=contract.functions.getPatientRecord(i['id']).call()
        print(patientRecord)
        i['recordPath']=patientRecord[0]
        i['age']=patientRecord[1]
        i['date']=patientRecord[2]
        i['health_conditions']=patientRecord[3]
        i['medications']=patientRecord[4]
        i['doctor_notes']=patientRecord[5]
    
    print(formatted_patientList)    
    contract,web3=connectWithContract(0)
    doctorsList=contract.functions.viewAllDoctors().call()
    keys = ["address", "id", "name", "password", "email", "license", "specialization", "status"]

    # List of dictionaries (in case you have multiple entries in the list)
    formatted_data = [
        dict(zip(keys, record)) for record in doctorsList
    ]
    try:
        contract,web3=connectWithContract(0,EHRArtifactPath)
        tx_hash=contract.functions.bookAppointment(patient_id,doctor_id,appointment_date).transact()
        web3.eth.waitForTransactionReceipt(tx_hash)
        return redirect('/adminAppointmentManagement')
    except Exception as E:
        return render_template('admin-add-appointment.html',users=formatted_patientList,doctors=formatted_data,err=E)

if __name__=="__main__":
    app.run(host='0.0.0.0',port=9009,debug=True)