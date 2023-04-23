#importing needed packages
from dataclasses import dataclass
from datetime import datetime, time
from pydantic import Field, BaseModel
from typing import TYPE_CHECKING, Any, Dict, Optional, Pattern, Union, List

#Define classes

@dataclass
class Period:
    start: datetime
    end: datetime


class CodeableConcept(BaseModel):
    coding: str = None
    text: str = None


@dataclass
class Address:
    use: str
    text: str
    line: str
    city: str
    district: str
    state: str
    postalcode: str
    country: str
    period: Period = None


class HumanName(BaseModel):
    code: str = None
    family: str = None
    given: str = None
    prefix: str = None
    suffix: str = None


class Identifier(BaseModel):
    use: Optional[str] = None
    system: Optional[str] = None
    value: Optional[str] = None
    period: Period = None
    assigner: Optional[str] = None


@dataclass
class Contact:
    relationship: Optional[str] = None
    name: HumanName = None
    telecom: Optional[int] = None
    address: Address = None
    gender: Optional[str] = None
    Organization: Optional[str] = None
    period: Period = None


@dataclass
class Communication:
    language: str
    preferred: bool


@dataclass
class link:
    other: str = None


class clinicalStatus(BaseModel):
    # active | recurrence | relapes | inactive | remission | resolved
    clinical_status: str


class verificationStatus(BaseModel):
    # Unconfirmed | provisional | differential | confirmed | refuted | entered-in-error
    verification_status: str = None


class Severity(BaseModel):
    severity: Optional[str] = None


class Code(BaseModel):
    coding: Optional[str] = None
    text: Optional[str] = None


class OnsetDateTime(BaseModel):
    onsetDateTime: datetime = None


class OnsetAge(BaseModel):
    onsetage: datetime = None


class OnsetPeriod(BaseModel):
    onsetperiod: datetime = None


class OnsetRange(BaseModel):
    onsetrange: str


class RecordedDate(BaseModel):
    recordeddate: datetime = None


class Reference(BaseModel):
    reference: str = None
    type: str = None
    identifier: Identifier
    display: str = None


class Effective(BaseModel):
    effectiveDateTime: datetime
    effectivePeriod: Period
    effectiveTiming: datetime
    effectiveInstant: datetime


class SampleData(BaseModel):
    origin: str
    period: Period
    factor: int
    lowerLimit: int
    uppperLimit: int
    dimensions: int
    data: str


class Value(BaseModel):
    valueQuantity: int
    valueCodeableConcept: CodeableConcept
    valueString: str = None
    valueBoolean: bool
    valueInteger: int
    valueRange: int = None
    valueRatio: int = None
    valueSampledData: SampleData
    valueTime: datetime
    valueDateTime: datetime
    valuPeriod: Period


class Annotation(BaseModel):
    author: HumanName
    time: datetime
    text: str


class ReferenceRange(BaseModel):
    low: int
    high: int
    type: CodeableConcept
    appliesTo: CodeableConcept
    age: int
    text: str


class Component(BaseModel):
    code: CodeableConcept
    value: Value
    dataAbsentRange: CodeableConcept
    iterpretation: CodeableConcept
    referenceRange: ReferenceRange


# Class for which the patient post function inherits
class Patient(BaseModel):
    resource_type: str = None
    identifier: Identifier
    active: bool
    birthDate: datetime = None
    telecom: int
    name: HumanName
    gender: str
    deceasedBoolean: bool
    deceasedDateTime: datetime = None
    address: Address
    maritalStatus: str
    multipleBirthBoolean: bool
    multipleBirthInteger: int
    contact: Contact
    comunication: Communication
    generalPractitioner: str
    managingOrganization: str
    link: link


# Class for which the Condition POST function inherits from
class Condition(BaseModel):
    resource_type: str = 'Condition'
    identifier: Identifier
    clinicalStatus: clinicalStatus
    verificationstatus: verificationStatus
    category: CodeableConcept
    severity: Severity
    code: Code
    bodysite: CodeableConcept
    subject: Reference
    encounter: Reference
    onsetdatetime: OnsetDateTime
    onsetage: OnsetAge
    onsetperiod: OnsetPeriod
    onsetrange: OnsetRange
    recordeddate: RecordedDate
    recorder: str = None


# Class for which the Observation POST function inherits from
class Observation(BaseModel):
    identifier: Identifier
    basedon: Reference
    partOf: Reference
    status: Code
    category: CodeableConcept
    code: Code
    subject: Reference
    focus: Reference
    encounter: Reference
    effective: Effective
    issued: datetime
    performer: Reference
    value: Value
    dataAbsentReason: CodeableConcept
    interpretation: CodeableConcept
    note: Annotation
    bodySite: CodeableConcept
    method: CodeableConcept
    specimen: Reference
    device: Reference
    referenceRange: ReferenceRange
    hasMember: Reference
    derivedFrom: Reference
    component: Component