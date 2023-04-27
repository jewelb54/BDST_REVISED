
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
from classes import *


app = FastAPI()

medications = []

encounters = []

api_key = '20d07ba0-6c9c-4a01-b16d-8e409aae6f28'
base_url = 'https://uts-ws.nlm.nih.gov/rest/'

@app.get("/")
def read_root():
    return {"Hello": "World"}

def create_patients_file_if_not_exists():
    if not os.path.isfile("patients.json"):
        with open("patients.json", "w") as f:
            json.dump({}, f, indent=4)

@app.post("/patients")
def create_patient(patient: Patient):
    create_patients_file_if_not_exists()
    patient_id = str(uuid.uuid4())
    with open("patients.json", "r+") as f:
        patients = json.load(f)
        patients[patient_id] = patient.dict()
        f.seek(0)
        json.dump(patients, f, indent=4)
        f.truncate()
    return {patient_id: patients[patient_id]}

@app.put("/patients/{patient_id}")
def update_patient(patient: Patient, patient_id: str):
    create_patients_file_if_not_exists()
    with open("patients.json", "r+") as f:
        patients = json.load(f)
        if patient_id not in patients:
            raise HTTPException(status_code=404, detail="Patient not found")
        patients[patient_id] = patient.dict()
        f.seek(0)
        json.dump(patients, f, indent=4)
        f.truncate()
    return patients[patient_id]

@app.get("/patients")
def read_patients(patient_id: str = None):
    create_patients_file_if_not_exists()
    with open("patients.json", "r") as f:
        patients = json.load(f)
        if patient_id is not None:
            if patient_id not in patients.keys():
                print(f"Patient ID {patient_id} not found in patients file")
                raise HTTPException(status_code=404, detail="Patient not found")
            else:
                print(f"Patient ID {patient_id} found in patients file")
                return patients[patient_id]
        else:
            print("No patient ID specified, returning all patients")
            return patients

def search_icd10cm_code(diagnosis: str):
    endpoint = 'search/current'
    query_param = f'?string={diagnosis}&sab=ICD10CM&returnIdType=code&apiKey={api_key}'
    response = requests.get(base_url + endpoint + query_param)
    results = response.json().get('result', {}).get('results', [])
    return results[0]['ui'] if results else None


@app.post("/condition/{patient_id}")
def create_condition(patient_id: str, condition: Condition):
    with open('conditions.json', 'r+') as infile:
        conditions = json.load(infile)

    condition_data = condition.dict()
    condition_data['subject'] = patient_id

    diagnosis = condition_data['code']['text']
    icd10_code = search_icd10cm_code(diagnosis)
    condition_data['code']['coding'][0]['code'] = icd10_code

    conditions.append(condition_data)

    with open("conditions.json", "w") as outfile:
        json.dump(conditions, outfile, indent=4)

    return condition_data


@app.put("/condition/{patient_id}/{condition_id}")
def update_condition(patient_id: str, condition_id: str, condition: Condition):
    with open("conditions.json", 'r+') as infile:
        conditions = json.load(infile)

    for idx, cond in enumerate(conditions):
        if cond['id'] == condition_id and cond['subject'] == patient_id:
            condition_data = condition.dict()
            condition_data['subject'] = patient_id

            diagnosis = condition_data['code']['text']
            icd10_code = search_icd10cm_code(diagnosis)
            condition_data['code']['coding'][0]['code'] = icd10_code

            conditions[idx] = condition_data

            with open("conditions.json", "w") as outfile:
                json.dump(conditions, outfile, indent=4)

            return condition_data

    raise HTTPException(status_code=404, detail="Condition not found")

@app.get("/condition/{patient_id}/{condition_id}")
def get_condition(patient_id: str, condition_id: str):
    with open("conditions.json", "r") as infile:
        conditions = json.load(infile)

    for condition in conditions:
        if condition["id"] == condition_id and condition["subject"] == patient_id:
            return condition

    raise HTTPException(status_code=404, detail="Condition not found")

# Replace the base_url with the correct UMLS base URL
umls_base_url = 'https://uts-ws.nlm.nih.gov/rest/'

# Function to get LOINC information (name and code) from UMLS
def get_loinc_info(lab_value: str):
    endpoint = 'search/current'
    query_param = f'?string={lab_value}&sab=LOINC&returnIdType=code&apiKey={api_key}'
    response = requests.get(umls_base_url + endpoint + query_param)
    results = response.json().get('result', {}).get('results', [])
    if not results:
        return None
    return {"name": results[0]['name'], "code": results[0]['ui']}

# Creating a POST endpoint to create an Observation
@app.post("/observation/{patient_id}")
def create_observation(patient_id: str, observation: Observation):
    with open('observations.json', 'r+') as infile:
        observations = json.load(infile)

    observation_data = observation.dict()
    observation_data['subject'] = patient_id

    lab_value = observation_data['code']['text']
    loinc_info = get_loinc_info(lab_value)
    if loinc_info:
        observation_data['code']['coding'][0]['code'] = loinc_info['code']
        observation_data['code']['coding'][0]['display'] = loinc_info['name']
    else:
        raise HTTPException(status_code=400, detail="LOINC code not found")

    observations.append(observation_data)

    with open("observations.json", "w") as outfile:
        json.dump(observations, outfile, indent=4, default=str)

    return observation_data

# Modify the PUT endpoint to update the Observation
@app.put("/observation/{patient_id}/{observation_id}")
def update_observation(patient_id: str, observation_id: str, observation: Observation):
    with open("observations.json", 'r+') as infile:
        observations = json.load(infile)

    for idx, obs in enumerate(observations):
        if obs['id'] == observation_id and obs['subject'] == patient_id:
            observation_data = observation.dict()
            observation_data['subject'] = patient_id

            lab_value = observation_data['code']['text']
            loinc_info = get_loinc_info(lab_value)
            if loinc_info:
                observation_data['code']['coding'][0]['code'] = loinc_info['code']
                observation_data['code']['coding'][0]['display'] = loinc_info['name']
            else:
                raise HTTPException(status_code=400, detail="LOINC code not found")

            observations[idx] = observation_data

            with open("observations.json", "w") as outfile:
                json.dump(observations, outfile, indent=4, default=str)

            return observation_data

    raise HTTPException(status_code=404, detail="Observation not found")


@app.get("/observations/{patient_id}/{loinc_code}")
def read_observation_by_patient_id_and_loinc_code(patient_id: int, loinc_code: str):
    with open("observations.json", "r+") as infile:
        observations = json.load(infile)

    filtered_observations = [obs for obs in observations if obs['subject'] == patient_id and obs['code']['coding'][0]['code'] == loinc_code]

    if filtered_observations:
        return filtered_observations
    else:
        raise HTTPException(status_code=404, detail="Observation not found")

# Function to get RxNORM information (name and code) from UMLS
def get_rxnorm_info(rxnorm_code: str):
    endpoint = f'content/current/CUI/{rxnorm_code}'
    query_param = f'?apiKey={api_key}'
    response = requests.get(umls_base_url + endpoint + query_param)
    result = response.json().get('result', {})
    return {"name": result['str'], "code": result['ui']}

# Creating a POST endpoint to create a medication request
@app.post("/medication-request/{patient_id}/{rxnorm_code}")
def create_medication_request(patient_id: str, rxnorm_code: str, medication_request: MedicationRequest):
    with open('medications.json', 'r+') as infile:
        medications = json.load(infile)

    medication_request_data = medication_request.dict()
    medication_request_data['subject'] = patient_id

    rxnorm_info = get_rxnorm_info(rxnorm_code)
    if rxnorm_info:
        medication_request_data['medication']['coding'][0]['code'] = rxnorm_info['code']
        medication_request_data['medication']['coding'][0]['display'] = rxnorm_info['name']
    else:
        raise HTTPException(status_code=400, detail="RxNorm code not found")

    medications.append(medication_request_data)

    with open("medications.json", "w") as outfile:
        json.dump(medications, outfile, indent=4, default=str)

    return medication_request_data

# Creating a PUT endpoint to update the medication request
@app.put("/medication-request/{patient_id}/{medication_request_id}")
def update_medication_request(patient_id: str, medication_request_id: str, updated_medication_request: MedicationRequest):
    with open("medications.json", 'r+') as infile:
        medications = json.load(infile)

    found_medication_request = None
    for idx, medication_request in enumerate(medications):
        if medication_request['id'] == medication_request_id and medication_request['subject'] == patient_id:
            found_medication_request = medication_request
            break

    if not found_medication_request:
        raise HTTPException(status_code=404, detail='Medication request not found')

    updated_medication_request_data = updated_medication_request.dict()
    updated_medication_request_data['subject'] = patient_id

    rxnorm_info = get_rxnorm_info(updated_medication_request_data['medication']['coding'][0]['code'])
    if rxnorm_info:
        updated_medication_request_data['medication']['coding'][0]['display'] = rxnorm_info['name']
    else:
        raise HTTPException(status_code=400, detail="RxNorm code not found")

    medications[idx] = updated_medication_request_data

    with open("medications.json", "w") as outfile:
        json.dump(medications, outfile, indent=4, default=str)

    return updated_medication_request_data

# GET endpoint that retrieves medication requests by RxNorm code and patient ID
@app.get("/medication-requests/{patient_id}/{rxnorm_code}")
def get_medication_requests(patient_id: str, rxnorm_code: str):
    with open("medications.json", "r") as infile:
        medications = json.load(infile)

    medication_requests = []
    for medication_request in medications:
        if medication_request['subject'] == patient_id and medication_request['medication']['coding'][0]['code'] == rxnorm_code:
            medication_requests.append(medication_request)

    return medication_requests

#Implementing encounter resources:
def validate_condition_ids(condition_ids: List[str]):
    with open('conditions.json', 'r') as infile:
        conditions = json.load(infile)
    return all(condition_id in [condition['id'] for condition in conditions] for condition_id in condition_ids)

def validate_observation_ids(observation_ids: List[str]):
    with open('observations.json', 'r') as infile:
        observations = json.load(infile)
    return all(observation_id in [observation['id'] for observation in observations] for observation_id in observation_ids)

def validate_medication_request_ids(medication_request_ids: List[str]):
    with open('medications.json', 'r') as infile:
        medication_requests = json.load(infile)
    return all(medication_request_id in [medication_request['id'] for medication_request in medication_requests] for medication_request_id in medication_request_ids)

def create_encounters_file_if_not_exists():
    if not os.path.exists("encounters.json"):
        with open("encounters.json", "w") as f:
            f.write("[]")

@app.post("/encounter")
def create_encounter(patient_id: str, encounter_data: dict):
    # Perform validation checks
    if not validate_patient_id(patient_id):
        raise HTTPException(status_code=404, detail="Patient not found")
    if not validate_condition_ids(encounter_data.get("condition_ids", [])):
        raise HTTPException(status_code=404, detail="Condition not found")
    if not validate_observation_ids(encounter_data.get("observation_ids", [])):
        raise HTTPException(status_code=404, detail="Observation not found")
    if not validate_medication_request_ids(encounter_data.get("medication_request_ids", [])):
        raise HTTPException(status_code=404, detail="Medication request not found")

    create_encounters_file_if_not_exists()

    encounter_data["id"] = str(uuid.uuid4())
    encounter_data["patient_id"] = patient_id

    with open("encounters.json", "r") as file:
        encounters = json.load(file)

    encounters.append(encounter_data)

    with open("encounters.json", "w") as file:
        json.dump(encounters, file, indent=4)

    return encounter_data

@app.get("/encounters")
def read_encounters(encounter_id: str = None):
    if encounter_id is not None:
        for encounter in encounters:
            if encounter["id"] == encounter_id:
                return encounter
        raise HTTPException(status_code=404, detail="Encounter not found")
    return {"encounters": encounters}

@app.put("/encounter/{encounter_id}")
def update_encounter(encounter_id: str, updated_encounter: Encounter):
    for idx, encounter in enumerate(encounters):
        if encounter['id'] == encounter_id:
            updated_encounter_data = updated_encounter.dict()
            updated_encounter_data['id'] = encounter_id
            encounters[idx] = updated_encounter_data
            return {"message": f"Encounter with ID {encounter_id} has been updated."}
    raise HTTPException(status_code=404, detail="Encountera not found")