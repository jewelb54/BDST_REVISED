
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Union
from datetime import date, datetime
from enum import Enum

class Identifier(BaseModel):
    system: str
    value: str

class NameUse(str, Enum):
    usual = "usual"
    official = "official"
    temp = "temp"
    nickname = "nickname"
    anonymous = "anonymous"
    old = "old"
    maiden = "maiden"

class HumanName(BaseModel):
    use: Optional[NameUse] = None
    family: str
    given: List[str]

class Gender(str, Enum):
    male = "male"
    female = "female"
    other = "other"
    unknown = "unknown"

class Patient(BaseModel):
    resourceType: str = Field("Patient", const=True)
    id: str
    identifier: List[Identifier]
    name: List[HumanName]
    gender: Gender
    birthDate: str

    class Config:
        schema_extra = {
            "example": {
                "resourceType": "Patient",
                "id": "example",
                "identifier": [
                    {
                        "system": "urn:oid:1.2.36.146.595.217.0.1",
                        "value": "12345"
                    }
                ],
                "name": [
                    {
                        "use": "official",
                        "family": "Chalmers",
                        "given": [
                            "Peter",
                            "James"
                        ]
                    }
                ],
                "gender": "male",
                "birthDate": "1974-12-25"
            }
        }

class Coding(BaseModel):
    system: str
    code: Optional[str] = None
    display: Optional[str] = None

class Code(BaseModel):
    coding: List[Coding]
    text: str

class Condition(BaseModel):
    id: str
    subject: str
    code: Code



class CodeableConcept(BaseModel):
    text: str
    coding: List[Coding]

class Observation(BaseModel):
    id: str
    status: str
    code: CodeableConcept
    valueQuantity: Dict[str, str]
    effectiveDateTime: str
    issued: str

class MedicationRequest(BaseModel):
    id: str
    status: str
    intent: str
    medication: CodeableConcept
    subject: str
    dosage: str

class Encounter(BaseModel):
    id: Optional[str] = None
    status: str
    patient_id: str
    condition_ids: List[str]
    observation_ids: List[str]
    medication_request_ids: List[str]