
from typing import TYPE_CHECKING, Any, Dict, Optional, Pattern, Union, List
import json
import os
import requests
import enum
from datetime import date, datetime
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field, root_validator
from pydantic.types import ConstrainedStr
from pydantic.error_wrappers import ErrorWrapper, ValidationError
from pydantic.errors import MissingError, NoneIsNotAllowedError
from Classes import *
from flask import Flask, jsonify, request

app = FastAPI()

class MedicationRequest(BaseModel):
    medication: str
    dosage: str

medications = []

base_url = 'https://uts-ws.nlm.nih.gov/rest/'

with open('key.txt', 'r') as file:
    api_key = file.read().replace('\n', '')


# Creates a patient
@app.post("/patients/{patient_id}")
def create_patient(patient: Patient, patient_id: int):
    # Check if the patient json database already exists
    if 'patients.json' not in os.listdir():
        raise HTTPException(status_code=404, detail='Patient not found')
        patients_JSON = {'{}'}
        with open('patients.json', 'w') as outfile:
            json.dump(patients_JSON, outfile)
    with open("patients.json", 'r+') as infile:
        patient_db = json.load(infile)
    patient_db[patient_id] = patient.dict()

    # Write the JSON object to a file
    with open("patients.json", "w", encoding='utf-8') as outfile:
        outfile.write('\n')
        json.dump(patient_db, outfile, ensure_ascii=False, indent=4, default=str)


# Update a patient instance
@app.put("/patients/{identifier}")
def update_patient(identifier: str, patient: Patient):
    with open("patients.json", "r+") as infile:
        patient_db = json.load(infile)
        if identifier not in patient_db:
            return "Patient not found"
        patient_db[identifier] = patient.dict()
    with open("patients.json", "w") as outfile:
        outfile.write('\n')
        json.dump(patient_db, outfile, indent=4, default=str)


# Retrieve a patient instance
@app.get("/patients")
def read_patient(patient_id: int = None):
    with open("patients.json", "r+") as infile:
        patient_db = json.load(infile)
        if patient_id is not None:
            return patient_db


# Make a function that makes a GET request to UMLS for the ui code associated with a diagnosis.
def ICD10_Code(diagnosis: str):
    endpoint = 'search/current'
    query_param = f'?string={diagnosis}&sab=ICD10CM&returnIdType=code&apiKey={api_key}'
    response = requests.get(base_url + endpoint + query_param)
    result = response.json()['result']['results']
    return result[0]['ui']


# Make a POST function that updates the conditions.json file with the ui code of the patient's condition.
@app.post("/condition/{patient_id}")
def Create_Conditon(patient_id: int, condition: Condition):
    with open('conditions.json', 'r') as infile:
        condition_data = json.load(infile)
    # Make an object that inherits from the Condition class in Classes.py
    condition_data = condition.dict()
    # Assign the subject attribute the value of the given patient id
    condition_data['subject'] = patient_id
    # Make a diagnosis object that obtains from the condition text section
    diagnosis = condition_data['code']['text']
    # Make an object that uses the ICD10_Code funtion defined above to populate the text section of the condition
    get_ICD10_Code = ICD10_Code(diagnosis)
    # Now populate the condition_data object with the correct ICD10 code!
    condition_data['code']['coding'] = get_ICD10_Code
    # Now dump to the conditions.json!!!
    with open("conditions.json", "w") as outfile:
        outfile.write('\n')
        json.dump(condition_data, outfile, indent=4, default=str)


# Creating a PUT endpoint to update the Condition file
@app.put("/condition/{patient_id}/{condition_id}")
def update_condition(patient_id: int, condition_id: str, condition: Condition):
    with open("conditions.json", 'r+') as infile:
        condition_db = json.load(infile)
    condition_db[patient_id] = condition.dict()
    condition_db['subject'] = patient_id
    diagnosis = condition_db['code']['text']
    get_ICD10_Code = ICD10_Code(diagnosis)
    condition_db['code']['coding']
    with open("conditions.json", "w") as outfile:
        outfile.write('\n')
        json.dump(condition_db, outfile, indent=4, default=str)


# Make a function that retrieves the LOINC code from UMLS
def LOINC_CODE(labValue: str):
    endpoint = 'content/current'
    query_param = f'/source/LNC/{labValue}?apiKey={api_key}'
    response = requests.get(base_url + endpoint + query_param)
    if response.status_code != 200:
        return None
    result = response.json()['result']['name']
    return result


# Creating a POST endpoint to lead to an Observation file
@app.post("/observation/{patient_id}")
def Create_Observation(patient_id: int, observation: Observation):
    with open('observations.json', 'r') as infile:
        observation_data = json.load(infile)
    observation_data = observation.dict()
    observation_data['subject'] = patient_id
    labValue = observation_data['code']['text']
    get_LabValue = LOINC_CODE(labValue)
    observation_data['code']['coding'] = get_LabValue
    with open("observations.json", "w") as outfile:
        outfile.write('\n')
        json.dump(observation_data, outfile, indent=4, default=str)

#Creating a PUT endpoint to update the Observation file
@app.put("/observation/{patient_id}/{observation_id}")
def create_observation(patient_id: int, observation_id: str, observation: Observation):
    with open("observations.json", 'r+') as infile:
        observation_db = json.load(infile)
    observation_db[patient_id] = observation.dict()
    observation_db['subject'] = patient_id
    labValue = observation_db['code']['text']
    get_LabValue = LOINC_CODE(labValue)
    observation_db['code']['coding']
    with open("observations.json", "w") as outfile:
        outfile.write('\n')
        json.dump(observation_db, outfile, indent=4, default=str)

#Creating a GET endpoint to read the Observation file
@app.get("/observations/{patient_id}")
def read_observation(patient_id: int):
    with open("observations.json", "r+") as infile:
        observation_db = json.load(infile)
        if patient_id is not None:
            return observation_db

#Creating a POST endpoint to lead to medications file
@app.post("/medications/{patient_id}/{rxnorm_code}")
def create_medication_request(patient_id: int, rxnorm_code: str, medication_request: MedicationRequest):
    medication_request_dict = medication_request.dict()
    medication_request_dict['subject'] = patient_id
    medication_request_dict['medication'] = {
        "reference": f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxnorm_code}/properties.json",
        "display": f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxnorm_code}/properties.json"
    }
    medications.append(medication_request_dict)
    return medication_request_dict

# Creating a PUT endpoint to update the medications file
@app.put("/medications/{patient_id}/{medication_id}")
def update_medication_request(patient_id: int, medication_id: str, updated_medication_request: MedicationRequest):
    with open("medications.json", 'r') as infile:
        medication_db = json.load(infile)
    if str(patient_id) not in medication_db:
        raise HTTPException(status_code=404, detail='Patient not found')
    found_medication = None
    for medication in medication_db[str(patient_id)]:
        if medication['id'] == medication_id:
            found_medication = medication
            break
    if not found_medication:
        raise HTTPException(status_code=404, detail='Medication not found')
    found_medication.update(updated_medication_request.dict())
    with open("medications.json", "w", encoding='utf-8') as outfile:
        json.dump(medication_db, outfile, ensure_ascii=False, indent=4, default=str)
    return {"message": f"Medication with ID {medication_id} for patient with ID {patient_id} has been updated."}

# GET endpoint that retrieves medications requests by RxNORM and patient ID
@app.get("/medications/{patient_id}/{rxnorm_code}")
def get_medication_requests(patient_id: int, rxnorm_code: str):
    medication_requests = []
    for medication in medications:
        if medication['subject'] == patient_id and medication['medication']['reference'].split('/')[-2] == rxnorm_code:
            medication_requests.append(medication)
    return medication_requests

