// SPDX-License-Identifier: MIT
pragma solidity >=0.4.22 <0.9.0;

contract EHR {
    struct PatientRecord {
        string filename;          // File name of the uploaded health record
        uint patientId;           // Patient ID
        uint age;                 // Patient's age
        string joinedDate;        // Date the patient joined
        string healthConditions;  // Known health conditions
        string medications;       // Current medications
        string doctorNotes;       // Doctor's notes
    }

    struct AppointmentRecord {
        uint id;
        uint patientId;
        uint doctorId;
        string datetime;
        string status;
    }

    struct MedicalRecord {
        uint recordId;     // Unique ID for the record
        uint patientId;    // ID of the patient
        string filePath;   // Path to the medical record file
        string date;
        string description;
    }

    mapping(uint => MedicalRecord[]) public medicalRecords; // Mapping from patient ID to a list of medical records
    uint public recordCounter;                             // Counter for unique record IDs

    event MedicalRecordAdded(uint patientId, uint recordId, string filePath);

    uint appId;
    mapping(uint => PatientRecord) public patientRecords; // Mapping of patient ID to records
    uint[] public patientIds;                             // List of patient IDs (for iteration)
    address public admin;                                 // Contract admin

    event PatientRecordAdded(uint patientId);

    mapping(uint => AppointmentRecord) public appointments; // Mapping to store appointments by their ID
    uint[] public appointmentIds; // Array to keep track of all appointment IDs

    // Event to emit when an appointment is booked
    event AppointmentBooked(uint appointmentId, uint patientId, uint doctorId, string datetime);

    constructor() {
        admin = msg.sender; // Set the deployer as the admin
        appId=0;
        recordCounter = 0; // Initialize record counter
    }

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }

    function bookAppointment(uint patient, uint doctor, string memory date) public {
        require(patient > 0, "Invalid patient ID");
        require(doctor > 0, "Invalid doctor ID");
        require(bytes(date).length > 0, "Invalid date and time");

        // Increment the appointment ID counter
        appId += 1;

        // Create a new appointment record
        appointments[appId] = AppointmentRecord({
            id: appId,
            patientId: patient,
            doctorId: doctor,
            datetime: date,
            status: "pending"
        });

        // Add the appointment ID to the list
        appointmentIds.push(appId);

        // Emit the event
        emit AppointmentBooked(appId, patient, doctor, date);
    }

    function updateAppointment(uint appointmentId, string memory status) public {
        // Ensure the appointment exists
        require(appointments[appointmentId].id != 0, "Appointment not found");
        require(bytes(status).length > 0, "Invalid status");

        // Update the status of the appointment
        appointments[appointmentId].status = status;
    }

    function updateAppointmentWithDate(uint appointmentId, string memory status,string memory datetime) public {
        // Ensure the appointment exists
        require(appointments[appointmentId].id != 0, "Appointment not found");
        require(bytes(status).length > 0, "Invalid status");

        // Update the status of the appointment
        appointments[appointmentId].status = status;
        appointments[appointmentId].datetime = datetime;
    }

    function getAppointment(uint appointmentId) public view returns (
        uint, uint, uint, string memory, string memory
    ) {
        require(appointments[appointmentId].id != 0, "Appointment not found");

        AppointmentRecord memory appointment = appointments[appointmentId];
        return (
            appointment.id,
            appointment.patientId,
            appointment.doctorId,
            appointment.datetime,
            appointment.status
        );
    }

    // Function to get all appointment IDs
    function getAllAppointmentIds() public view returns (uint[] memory) {
        return appointmentIds;
    }

    // Add a new patient record
    function addPatientRecord(
        string memory filename,
        uint patientId,
        uint age,
        string memory joinedDate,
        string memory healthConditions,
        string memory medications,
        string memory doctorNotes
    ) public onlyAdmin {
        require(patientRecords[patientId].patientId == 0, "Patient record already exists"); // Ensure unique patient ID

        PatientRecord memory newRecord = PatientRecord(
            filename,
            patientId,
            age,
            joinedDate,
            healthConditions,
            medications,
            doctorNotes
        );

        patientRecords[patientId] = newRecord;
        patientIds.push(patientId);

        emit PatientRecordAdded(patientId);
    }

    // Retrieve a patient's record by ID
    function getPatientRecord(uint patientId) public view returns (
        string memory,
        uint,
        string memory,
        string memory,
        string memory,
        string memory
    ) {
        require(patientRecords[patientId].patientId != 0, "Patient record not found");
        PatientRecord memory record = patientRecords[patientId];
        return (
            record.filename,
            record.age,
            record.joinedDate,
            record.healthConditions,
            record.medications,
            record.doctorNotes
        );
    }

    // Retrieve all patient IDs
    function getAllPatientIds() public view returns (uint[] memory) {
        return patientIds;
    }

    function deletePatientRecord(uint patientId) public onlyAdmin {
        require(patientRecords[patientId].patientId != 0, "Patient does not exist");

        delete patientRecords[patientId];

        // Remove patientId from the list
        for (uint i = 0; i < patientIds.length; i++) {
            if (patientIds[i] == patientId) {
                patientIds[i] = patientIds[patientIds.length - 1];
                patientIds.pop();
                break;
            }
        }
    }

    function editPatientRecord(
        uint patientId,
        uint age,
        string memory joinedDate,
        string memory healthConditions,
        string memory medications,
        string memory doctorNotes
    ) public onlyAdmin {
        require(patientRecords[patientId].patientId != 0, "Patient does not exist");

        PatientRecord storage record = patientRecords[patientId];
        record.age = age;
        record.joinedDate = joinedDate;
        record.healthConditions = healthConditions;
        record.medications = medications;
        record.doctorNotes = doctorNotes;
    }

    // Function to add a medical record for a patient
    function addMedicalRecord(uint patId, string memory filePath,string memory date,string memory desc) public {
        require(patId > 0, "Invalid patient ID");
        require(bytes(filePath).length > 0, "Invalid file path");

        // Increment the record counter
        recordCounter += 1;

        // Create and add the medical record
        medicalRecords[patId].push(MedicalRecord({
            recordId: recordCounter,
            patientId: patId,
            filePath: filePath,
            date: date,
            description: desc
        }));

        // Emit the event
        emit MedicalRecordAdded(patId, recordCounter, filePath);
    }

    // Function to retrieve all medical records for a specific patient
    function getMedicalRecords(uint patId) public view returns (MedicalRecord[] memory) {
        require(medicalRecords[patId].length > 0, "No medical records found for this patient");
        return medicalRecords[patId];
    }

    // Function to retrieve a specific medical record by record ID
    function getMedicalRecordById(uint patId, uint recordId) public view returns (uint, uint, string memory,string memory,string memory) {
        MedicalRecord[] memory records = medicalRecords[patId];
        for (uint i = 0; i < records.length; i++) {
            if (records[i].recordId == recordId) {
                return (records[i].recordId, records[i].patientId, records[i].filePath,records[i].date,records[i].description);
            }
        }
        revert("Medical record not found");
    }

    function getAllMedicalRecords() public view returns (MedicalRecord[] memory) {
        uint totalRecordsCount = 0;

        // Calculate the total number of records
        for (uint i = 0; i < patientIds.length; i++) {
            totalRecordsCount += medicalRecords[patientIds[i]].length;
        }

        // Create an array to hold all records
        MedicalRecord[] memory allRecords = new MedicalRecord[](totalRecordsCount);

        // Add all records to the array
        uint currentIndex = 0;
        for (uint i = 0; i < patientIds.length; i++) {
            uint patientId = patientIds[i];
            MedicalRecord[] memory records = medicalRecords[patientId];
            for (uint j = 0; j < records.length; j++) {
                allRecords[currentIndex] = records[j];
                currentIndex++;
            }
        }

        return allRecords;
    }

}