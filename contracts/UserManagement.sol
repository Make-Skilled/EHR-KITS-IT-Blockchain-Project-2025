// SPDX-License-Identifier: MIT
pragma solidity >=0.4.22 <0.9.0;

contract UserManagement {
  address admin;
  string adminUsername = "admin@gmail.com";
  string adminPassword = "admin123";

  uint docId;
  uint patId;

  struct Doctor {
    address _doctorAddress; // Mandatory
    uint _doctorId;
    string _doctorName;
    string _doctorPassword;
    string _doctorEmail;
    string _doctorLicense;
    string _doctorSpecialisation;
    bool _exist;
  }

  struct Patient {
    address _patientAddress; // Mandatory
    uint _patientId;
    string _patientName;
    string _patientPassword;
    string _patientEmail;
    string _patientGender;
    string _patientPhone;
    string _patientHomeAddress;
    string _patientProfilePhoto;
    bool _exist;
  }

  // Mapping variables
  mapping(address => Doctor) _doctors;
  address[] _doctorwallets;

  mapping(address => Patient) _patients;
  address[] _patientwallets;

  constructor() {
    admin = msg.sender; // msg.sender is a global variable where it is holding the address of contract invoker
    docId = 0;
    patId = 0;
  }

  // ValidateAdmin will verify login details of admin passed by frontend
  function validateAdmin(string memory username, string memory password) public view returns (bool) {
    if (keccak256(bytes(username)) == keccak256(bytes(adminUsername))) {
      if (keccak256(bytes(password)) == keccak256(bytes(adminPassword))) {
        return true;
      } else {
        return false;
      }
    } else {
      return false;
    }
  }

  // It will create an account of doctor
  function addDoctor(address wallet, string memory name, string memory password, string memory email, string memory doclicense, string memory docspecial) public {
    require(!_doctors[wallet]._exist, "Account exist for this wallet");
    docId += 1;

    Doctor memory new_doctor = Doctor(wallet, docId, name, password, email, doclicense, docspecial, true);
    _doctors[wallet] = new_doctor;
    _doctorwallets.push(wallet);
  }

  // It will create an account of patient
  function addPatient(address wallet, string memory name, string memory password, string memory email) public {
    require(!_patients[wallet]._exist, "Account exist for this wallet");
    patId += 1;

    Patient memory new_patient = Patient(wallet, patId, name, password, email,"NA","NA","NA","NA",true);
    _patients[wallet] = new_patient;
    _patientwallets.push(wallet);
  }

  // It will return all the registered doctors
  function viewAllDoctors() public view returns (Doctor[] memory) {
    Doctor[] memory _doctorArray = new Doctor[](_doctorwallets.length);

    for (uint256 i = 0; i < _doctorwallets.length; i++) {
      _doctorArray[i] = _doctors[_doctorwallets[i]];
    }

    return _doctorArray;
  }

  // It will return all the registered patients
  function viewAllPatients() public view returns (Patient[] memory) {
    Patient[] memory _patientArray = new Patient[](_patientwallets.length);

    for (uint256 i = 0; i < _patientwallets.length; i++) {
      _patientArray[i] = _patients[_patientwallets[i]];
    }

    return _patientArray;
  }

  // It will return only one record of doctor based on wallet
  function viewDoctorByWallet(address wallet) public view returns (Doctor memory) {
    require(_doctors[wallet]._exist, "No account with that wallet"); // true
    return _doctors[wallet];
  }

  // It will return only one record of patient based on wallet
  function viewPatientByWallet(address wallet) public view returns (Patient memory) {
    require(_patients[wallet]._exist, "No account with that wallet"); // true
    return _patients[wallet];
  }

  // It will return only one record of doctor based on doctor id
  function viewDoctorById(uint docI) public view returns (Doctor memory) {
    require(docI > 0 && docI <= _doctorwallets.length, "Invalid doctor ID");
    return _doctors[_doctorwallets[docI - 1]];
  }

  // It will return only one record of patient based on patient id
  function viewPatientById(uint patI) public view returns (Patient memory) {
    require(patI > 0 && patI <= _patientwallets.length, "Invalid patient ID");
    return _patients[_patientwallets[patI - 1]];
  }

  // It will validate the login details of doctor
  function doctorLogin(string memory email, string memory password) public view returns (bool) {
    for (uint256 i = 0; i < _doctorwallets.length; i++) {
      Doctor memory doc = _doctors[_doctorwallets[i]];
      if (keccak256(bytes(doc._doctorEmail)) == keccak256(bytes(email)) && keccak256(bytes(doc._doctorPassword)) == keccak256(bytes(password))) {
        return true;
      }
    }
    return false;
  }

  // It will validate the login details of patient
  function patientLogin(string memory email, string memory password) public view returns (bool) {
    for (uint256 i = 0; i < _patientwallets.length; i++) {
      Patient memory pat = _patients[_patientwallets[i]];
      if (keccak256(bytes(pat._patientEmail)) == keccak256(bytes(email)) && keccak256(bytes(pat._patientPassword)) == keccak256(bytes(password))) {
        return true;
      }
    }
    return false;
  }

  function viewPatientByEmail(string memory email) public view returns (Patient memory) {
    for (uint i = 0; i < _patientwallets.length; i++) {
        Patient memory pat = _patients[_patientwallets[i]];
        if (keccak256(bytes(pat._patientEmail)) == keccak256(bytes(email))) {
            return pat;
        }
    }
    revert("Patient with the given email does not exist");
  }

  function updatePatientByEmail(string memory name,string memory email,string memory gender,string memory phone,string memory homeAddress) public {
    for (uint i = 0; i < _patientwallets.length; i++) {
        if (keccak256(bytes(_patients[_patientwallets[i]]._patientEmail)) == keccak256(bytes(email))) {
            _patients[_patientwallets[i]]._patientName = name;
            _patients[_patientwallets[i]]._patientGender = gender;
            _patients[_patientwallets[i]]._patientPhone = phone;
            _patients[_patientwallets[i]]._patientHomeAddress = homeAddress;
            return; // Exit the function after updating
        }
    }

    revert("Patient with the given email does not exist");
  }

  function updatePatientPhoto(string memory photo,string memory email) public {
    for (uint i = 0; i < _patientwallets.length; i++) {
        if (keccak256(bytes(_patients[_patientwallets[i]]._patientEmail)) == keccak256(bytes(email))) {
          _patients[_patientwallets[i]]._patientProfilePhoto=photo;
          return;
        }
    }
    revert("Patient with the given email does not exist");
  }

  function viewDoctorByEmail(string memory email) public view returns (Doctor memory){
    for(uint i=0; i<_doctorwallets.length;i++){
      Doctor memory doc = _doctors[_doctorwallets[i]];
      if (keccak256(bytes(doc._doctorEmail)) == keccak256(bytes(email))){
        return doc;
      }
    }
    revert("Doctor with the given email does not exist");
  }


  // It has to return admin wallet address, admin username
  function viewAdmin() public view returns (address, string memory) {
    // Read Operation only
    return (admin, adminUsername);
  }

  function getDoctorNameById(uint docI) public view returns (string memory) {
    Doctor memory doctor = viewDoctorById(docI);
    return doctor._doctorName;
  }

  // Retrieve patient name by ID
  function getPatientNameById(uint patI) public view returns (string memory) {
      Patient memory patient = viewPatientById(patI);
      return patient._patientName;
  }
}
