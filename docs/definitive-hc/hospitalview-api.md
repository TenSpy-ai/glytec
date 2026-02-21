Getting started

Welcome! We're glad you're here. Our documentation provides details on our HospitalView API. This page will always provide you with the most up-to-date information as we continue to enhance our API offerings. If you have questions about access or subscriptions, contact your System admin or Definitive Healthcare Account Manager.  
This documentation is interactive;hit the ‘Authorize’ button to get started.  
For more help, contact [support@definitivehc.com](mailto:support@definitivehc.com).

Required product permissionsYou'll need an active Definitive Healthcare account and API access permissions to access HospitalView API.  
1\. HospitalView endpoints require a HospitalView product subscription.2. PhysicianView endpoints require a PhysicianView product subscription.

Step 1: API key specificationsA valid API key is required to access both the HospitalView API.  
API key expirationAt this time, GUID-based API keys don't expire.  
Please reach out to our Support team at [support@definitivehc.com](mailto:support@definitivehc.com)  or the Definitive Healthcare Integrations team at [integrations@definitivehc.com](mailto:integrations@definitivehc.com) for assistance with API keys.

Step 2: AuthenticationTo authenticate, make sure that your user-specific API is included in the request header. Header values are case sensitive.Enter the text "ApiKey", followed by a space, before you enter your API key.  
Curl example:curl -X 'GET' \\'https://api-data.defhc.com/v1/hospitals/1973?page%5Bsize%5D=10&page%5Boffset%5D=1' \\-H 'accept: text/plain' \\-H 'Authorization: ApiKey 00000000-0000-0000-0000-000000000000'

Authorize

### HospitalView API specifications

GET/v1/hospitals/{id}

Provides summary level details for the hospital specified

Sample request:

     GET /v1/hospitals/{id}
    

Sample response:

     {
       "meta": {
         "pageSize": 1,
         "totalRecords": 1,
         "pageOffset": 1,
         "totalPages": 1
       },
       "data": {
         "facilityName": "Sample Text for Medical Center",
         "definitiveId": 5,
         "medicareProviderNumber": "08002F",
         "facilityPrimaryNpi": 111111111,
         "facilityNpiList":
             [
               111111111,
               123456789
             ]
         "firmType": "Hospital",
         "hospitalType": "VA Hospital",
         "addressLine1": "1601 Address Street",
         "addressLine2": null,
         "city": "SampleCity",
         "state": "DE",
         "zip": "71671",
         "latitude": "39.XXXX",
         "latitudeCoordinates": 39.XXXX,
         "longitude": "-75.XXXX",
         longitudeCoordinates": -75.XXXX,
         "county": "Bradley",
         "region": "NorthEast",
         "geographicClassification": "Urban",
         "cbsaCode": 37980,
         "cbsaDescription": "Philadelphia-Camden",
         "definitiveProfileLink": "https://www.defhc.com/hospitals/DEFINITIVEID",
         "medicalSchoolAffiliates": "Sample Acedemic Medical College University",
         "medicalSchoolAffiliatesList": 
           [ 
                "Sample Acedemic Medical College University", 
                "Tufts University School of Medicine" 
           ],
         "networkId": 541798,
         "networkName": "Sample Health System",
         "networkParentId": 7265,
         "networkParentName": "Sample Health System",
         "description": "Sample Medical Center proudly serves Veterans in multiple locations for convenient access to the services we provide. In addition to the Medical Center, Community Based Outpatient Clinics are located in Georgetown and Dover, DE",
         "website": "www.SAMPLEHEALTHCENTER.org",
         "networkOwnership": "Owned",
         "ownership": "Governmental - Federal",
         "companyStatus": "Active",
         "phone": "302.000.0000",
         "fiscalYearEndMonth": 6,
         "fiscalYearEndDay": 30,
         "academicMedicalCenter": true
         "accreditationAgency": "The Joint Commission",
         "accreditationAgencyList": 
           [ 
                 "The Joint Commission", 
                 "Second Accreditation Agency" 
           ],
         "pediatricTraumaCenter": "Level I",
         "traumaCenter": "Level I",
         "IDNIntegrationLevel": "System III (vertical integration)",
         "facility340BId": "H999999",
         "taxId": "09-9999999",
         "medicareAdministrativeContract": "Sample Company"
         "marketConcentrationIndex": 0.005
         "payorMixMedicaid": 0.700
         "payorMixMedicare": 0.700
         "payorMixSelfPay": 0.700
         "primaryPhysiciansCount": 224,
         "secondaryPhysiciansCount": 117
       }
     }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

Hospital ID

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "facilityName": "string",
        "definitiveId": 0,
        "medicareProviderNumber": "string",
        "facilityPrimaryNpi": 0,
        "facilityNpiList": [
          0
        ],
        "firmType": "string",
        "hospitalType": "string",
        "addressLine1": "string",
        "addressLine2": "string",
        "city": "string",
        "state": "string",
        "zip": "string",
        "latitude": "string",
        "latitudeCoordinates": 0,
        "longitude": "string",
        "longitudeCoordinates": 0,
        "county": "string",
        "region": "string",
        "geographicClassification": "string",
        "cbsaCode": 0,
        "cbsaDescription": "string",
        "definitiveProfileLink": "string",
        "medicalSchoolAffiliates": "string",
        "medicalSchoolAffiliatesList": [
          "string"
        ],
        "networkId": 0,
        "networkName": "string",
        "networkParentId": 0,
        "networkParentName": "string",
        "description": "string",
        "website": "string",
        "networkOwnership": "string",
        "ownership": "string",
        "companyStatus": "string",
        "phone": "string",
        "fiscalYearEndDay": 0,
        "fiscalYearEndMonth": 0,
        "academicMedicalCenter": true,
        "accreditationAgency": "string",
        "accreditationAgencyList": [
          "string"
        ],
        "pediatricTraumaCenter": "string",
        "traumaCenter": "string",
        "IDNIntegrationLevel": "string",
        "facility340BId": "string",
        "taxId": "string",
        "medicareAdministrativeContract": "string",
        "marketConcentrationIndex": 0,
        "payorMixMedicaid": 0,
        "payorMixMedicare": 0,
        "payorMixSelfPay": 0,
        "primaryPhysiciansCount": 0,
        "secondaryPhysiciansCount": 0
      }
    }

_No links_

GET/v1/hospitals/{id}/technologies/currentimplementations

Provides array of currently implemented technologies for the hospital specified

Sample request:

    GET /v1/hospitals/{id}/technologies/currentimplementations
    

Sample response:

    {  
        "meta":{
            "pageSize": 1,
            "totalRecords": 2,
            "PageOffset": 1,
            "totalPages": 1
        },
        "data":[
            {
                "category": "Clinical Systems",
                "technology": "Telemedicine",
                "vendor": "WellDoc",
                "product": "BlueStar",
                "vendorStatus": "Installed Vendor",
                "implementationYear": 2020,
                "unitsInstalled": null,
                "definitiveId": 1973
            },
            {
                "category": "Clinical & Business Intelligence",
                "technology": "Clinical Decision Support System",
                "vendor": "Prevencio",
                "product": null,
                "vendorStatus": "Installed Vendor",
                "implementationYear": null,
                "unitsInstalled": null,
                "definitiveId": 1973
            }
         ]
    }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

Hospital ID

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "category": "string",
        "technology": "string",
        "vendor": "string",
        "product": "string",
        "vendorStatus": "string",
        "implementationYear": 0,
        "unitsInstalled": 0,
        "definitiveId": 0
      }
    }

_No links_

POST/v1/hospitals/{id}/technologies/currentimplementations/search

Provides array of currently implemented technologies with the hospital and the specified search parameter.

    When filtering data, the following OperatorTypes can be used (valid value data types in parentheses):
    
    Equals (numeric, string, date)
    NotEquals(numeric, string, date)
    GreaterThan(numeric, date)
    LessThan(numeric, date)
    GreaterThanOrEqual(numeric, date)
    LessThanOrEqual(numeric, date)
    In(numeric, string, date)
    NotIn(numeric, string, date)
    StartsWith(string)
    EndsWith(string)
    Contains(string)
    IsNull(if used, Value not required for filter)
    IsNotNull(if used, Value not required for filter)
    True(Boolean - if used, Value not required for filter)
    False(Boolean - if used, Value not required for filter)
    
    When using operators "contains", "starts with" and "ends with", you must enter at least 3 characters when filtering.         
    

Sample request:

    POST /v1/hospitals/{id}/technologies/currentimplementations/search
    

Sample request body:

    [
        {
            "propertyName":"Category",
            "operatorType": "Equals",                    
            "value": "Clinical Systems"
        }
    ]
    

Sample response:

    {  
        "meta":{
            "pageSize": 1,
            "totalRecords": 2,
            "PageOffset": 1,
            "totalPages": 1
        },
        "data":[
            {
                "category": "Clinical Systems",
                "technology": "Telemedicine",
                "vendor": "WellDoc",
                "product": "BlueStar",
                "vendorStatus": "Installed Vendor",
                "implementationYear": 2020,
                "unitsInstalled": null,
                "definitiveId": 1973
            },
            {
                "category": "Clinical & Business Intelligence",
                "technology": "Clinical Decision Support System",
                "vendor": "Prevencio",
                "product": null,
                "vendorStatus": "Installed Vendor",
                "implementationYear": null,
                "unitsInstalled": null,
                "definitiveId": 1973
            }
         ]
    }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

Hospital ID

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Request body

Please enter Filter Parameters in the request body

*   Example Value
*   Schema

    [
      {
        "propertyName": "string",
        "operatorType": "Equals",
        "value": "string"
      }
    ]

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "category": "string",
        "technology": "string",
        "vendor": "string",
        "product": "string",
        "vendorStatus": "string",
        "implementationYear": 0,
        "unitsInstalled": 0,
        "definitiveId": 0
      }
    }

_No links_

GET/v1/hospitals/{id}/newsandintelligence

Provides array of news articles for the hospital specified

Sample request:

    GET /v1/hospitals/{id}/newsandintelligence
    

Sample response:

    {
      "meta": {
        "pageSize": 2,
        "totalRecords": 2,
        "pageOffset": 1,
        "totalPages": 1
      },
      "data": [
        {
          "publicationDate": "2016-03-01",
          "intelligenceType": "New Capabilities",
          "newsEventTitle": "Mass General Concierge Service",
          "bodyOfArticle": "Massachusetts General Hospital plans to launch a concierge service in August 2016 that will charge patients $6,000. Patients who pay the annual membership fee will receive specialized services such as on-demand, 24-hour access to their physicians; personalized nutrition counseling; and wellness and exercise counseling. Patients will also have easy access to specialists and other resources. The move has drawn support from some arenas, and criticism from others.",
          "publicationId": 97481,
          "definitiveId": 1973
        },
        {
          "publicationDate": "2017-02-08",
          "intelligenceType": "Legal/Regulatory",
          "newsEventTitle": "Security breach: Fake doc roams Boston hospitals",
          "bodyOfArticle": "FierceHealthcare and The Boston Globe report Brigham and Women’s Hospital experienced a strange case of impersonation when a woman, Cheryl Wang, forged recommendation letters to shadow surgeons during surgeries and while attending patient rounds. The incident happened in September 2016 and the woman reappeared at the hospital in December 2016. The same woman also entered Massachusetts General Hospital and attempted to enter Boston Children's Hospital.",
          "publicationId": 119429,
          "definitiveId": 1973
        }
      ]
    }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

Hospital ID

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "publicationDate": "string",
        "intelligenceType": "string",
        "newsEventTitle": "string",
        "bodyOfArticle": "string",
        "publicationId": 0,
        "definitiveId": 0
      }
    }

_No links_

POST/v1/hospitals/{id}/newsandintelligence/search

Provides array of news articles with the hospital and the specified search parameter.

    When filtering data, the following OperatorTypes can be used (valid value data types in parentheses):
    
    Equals (numeric, string, date)
    NotEquals(numeric, string, date)
    GreaterThan(numeric, date)
    LessThan(numeric, date)
    GreaterThanOrEqual(numeric, date)
    LessThanOrEqual(numeric, date)
    In(numeric, string, date)
    NotIn(numeric, string, date)
    StartsWith(string)
    EndsWith(string)
    Contains(string)
    IsNull(if used, Value not required for filter)
    IsNotNull(if used, Value not required for filter)
    True(Boolean - if used, Value not required for filter)
    False(Boolean - if used, Value not required for filter)
    
    When using operators "contains", "starts with" and "ends with", you must enter at least 3 characters when filtering.         
    

Sample request:

    POST /v1/hospitals/{id}/newsandintelligence/search
    

Sample request body:

    [
        {
            "propertyName":"intelligenceType",
            "operatorType": "Equals",
            "value": "New Capabilities" 
        }
    ]
    

Sample response:

    {
      "meta": {
        "pageSize": 2,
        "totalRecords": 2,
        "pageOffset": 1,
        "totalPages": 1
      },
      "data": [
        {
          "publicationDate": "2016-03-01",
          "intelligenceType": "New Capabilities",
          "newsEventTitle": "Mass General Concierge Service",
          "bodyOfArticle": "Massachusetts General Hospital plans to launch a concierge service in August 2016 that will charge patients $6,000. Patients who pay the annual membership fee will receive specialized services such as on-demand, 24-hour access to their physicians; personalized nutrition counseling; and wellness and exercise counseling. Patients will also have easy access to specialists and other resources. The move has drawn support from some arenas, and criticism from others.",
          "publicationId": 97481,
          "definitiveId": 1973
        },
        {
          "publicationDate": "2017-02-08",
          "intelligenceType": "New Capabilities",
          "newsEventTitle": "Security breach: Fake doc roams Boston hospitals",
          "bodyOfArticle": "FierceHealthcare and The Boston Globe report Brigham and Women’s Hospital experienced a strange case of impersonation when a woman, Cheryl Wang, forged recommendation letters to shadow surgeons during surgeries and while attending patient rounds. The incident happened in September 2016 and the woman reappeared at the hospital in December 2016. The same woman also entered Massachusetts General Hospital and attempted to enter Boston Children's Hospital.",
          "publicationId": 119429,
          "definitiveId": 1973
        }
      ]
    }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Request body

Please enter Filter Parameters in the request body

*   Example Value
*   Schema

    [
      {
        "propertyName": "string",
        "operatorType": "Equals",
        "value": "string"
      }
    ]

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "publicationDate": "string",
        "intelligenceType": "string",
        "newsEventTitle": "string",
        "bodyOfArticle": "string",
        "publicationId": 0,
        "definitiveId": 0
      }
    }

_No links_

GET/v1/hospitals/{id}/executives

Provides array of executives affiliated with the hospital specified

Sample request:

    GET /v1/hospitals/{id}/executives
    

Sample response:

    {
       "meta": {
         "pageSize": 1,
         "totalRecords": 1,
         "pageOffset": 1,
         "totalPages": 1
       },
       "data": [
         {
          "personId": 999999,
          "executiveId": 999999,
          "firstName": "John",
          "middleName": "Sample",
          "lastName": "Doe",
          "prefix": null,
          "suffix": null,
          "credentials": null,
          "gender": "Male",
          "department": "Board of Directors/Trustees",
          "positionLevel": "Board of Directors",
          "standardizedTitle": "Board Of Directors/Trustees Member",
          "title": "Member - Governing Board",
          "primaryEmail": null,
          "directPhone": null,
          "locationPhone": "870.000.0000",
          "linkedinProfileURL": null,
          "physicianFlag": true,
          "physicianLeader": false,
          "executiveNPI": null,
          "lastUpdatedDate": "2022-11-01",
          "definitiveId": 226,
          "mobilePhone": "123.456.1234",
          "directEmail": "heathor@ortho.org",
          "mobilePhones": 
                        [ 
                         "122.122.1234", 
                         "122.122.1235" 
                        ],
          "directEmails": 
                        [ 
                         "andrew@system.prg", 
                         "avenger@sheal.org" 
                        ]
        }
       ]
     }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

Hospital Id

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "personId": 0,
        "executiveId": 0,
        "firstName": "string",
        "middleName": "string",
        "lastName": "string",
        "prefix": "string",
        "suffix": "string",
        "credentials": "string",
        "gender": "string",
        "department": "string",
        "positionLevel": "string",
        "standardizedTitle": "string",
        "title": "string",
        "primaryEmail": "string",
        "directPhone": "string",
        "locationPhone": "string",
        "linkedinProfileURL": "string",
        "physicianFlag": true,
        "physicianLeader": true,
        "executiveNPI": 0,
        "lastUpdatedDate": "string",
        "definitiveId": 0,
        "mobilePhone": "string",
        "directEmail": "string",
        "mobilePhones": [
          "string"
        ],
        "directEmails": [
          "string"
        ]
      }
    }

_No links_

POST/v1/hospitals/{id}/executives/search

Provides array of executives affiliated with the hospital and search parameters specified

    When filtering data, the following OperatorTypes can be used (valid value data types in parentheses):
    
    Equals (numeric, string, date)
    NotEquals(numeric, string, date)
    GreaterThan(numeric, date)
    LessThan(numeric, date)
    GreaterThanOrEqual(numeric, date)
    LessThanOrEqual(numeric, date)
    In(numeric, string, date)
    NotIn(numeric, string, date)
    StartsWith(string)    
    EndsWith(string)
    Contains(string)
    IsNull(if used, Value not required for filter)
    IsNotNull(if used, Value not required for filter)
    True(Boolean - if used, Value not required for filter)
    False(Boolean - if used, Value not required for filter)
    
    When using operators "contains", "starts with" and "ends with", you must enter at least 3 characters when filtering.  
    The property "credentials" cannot be filtered by using "contains", "starts with" and "ends with" operators".
    

Sample request:

    POST /v1/hospitals/{id}/executives/search  
    

Sample request body:

    [
        {
         "propertyName": "firstname",
         "operatorType": "In",
         "value": ["Doe", "Anthony"]
        },            
        {
          "propertyName": "physicianLeader",
          "operatorType": "True"
        }
    ]
    

Sample response:

    {
       "meta": {
         "pageSize": 1,
         "totalRecords": 1,
         "pageOffset": 1,
         "totalPages": 1
       },
       "data": [
         {
          "personId": 999999,
          "executiveId": 999999,
          "firstName": "John",
          "middleName": "Sample",
          "lastName": "Doe",
          "prefix": null,
          "suffix": null,
          "credentials": null,
          "gender": "Male",
          "department": "Board of Directors/Trustees",
          "positionLevel": "Board of Directors",
          "standardizedTitle": "Board Of Directors/Trustees Member",
          "title": "Member - Governing Board",
          "primaryEmail": null,
          "directPhone": null,
          "locationPhone": "870.000.0000",
          "linkedinProfileURL": null,
          "physicianFlag": true,
          "physicianLeader": true,
          "executiveNPI": null,
          "lastUpdatedDate": "2022-11-01",
          "definitiveId": 226,
          "mobilePhone": "123.456.1234",
          "directEmail": "heathor@ortho.org",
          "mobilePhones": 
                        [ 
                         "122.122.1234", 
                         "122.122.1235" 
                        ],
          "directEmails": 
                        [ 
                         "andrew@system.prg", 
                         "avenger@sheal.org" 
                        ]
        }
       ]
     }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

Hospital Id

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Request body

Please enter Filter Parameters in the request body

*   Example Value
*   Schema

    [
      {
        "propertyName": "string",
        "operatorType": "Equals",
        "value": "string"
      }
    ]

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "personId": 0,
        "executiveId": 0,
        "firstName": "string",
        "middleName": "string",
        "lastName": "string",
        "prefix": "string",
        "suffix": "string",
        "credentials": "string",
        "gender": "string",
        "department": "string",
        "positionLevel": "string",
        "standardizedTitle": "string",
        "title": "string",
        "primaryEmail": "string",
        "directPhone": "string",
        "locationPhone": "string",
        "linkedinProfileURL": "string",
        "physicianFlag": true,
        "physicianLeader": true,
        "executiveNPI": 0,
        "lastUpdatedDate": "string",
        "definitiveId": 0,
        "mobilePhone": "string",
        "directEmail": "string",
        "mobilePhones": [
          "string"
        ],
        "directEmails": [
          "string"
        ]
      }
    }

_No links_

GET/v1/hospitals/{id}/physicians/affiliated

Provides array of physicians affiliated with the hospital specified

Sample request:

         GET /v1/hospitals/{id}/physicians/affiliated
    

Sample response:

        {
          "meta": {
            "pageSize": 2,
            "totalRecords": 2,
            "pageOffset": 1,
            "totalPages": 1
          },
          "data": [
           {
            "personId": 99999,
            "npi": 999999999,
            "firstName": "John",
            "middleName": "Sample",
            "lastName": "Doe",
            "prefix": "Dr.",
            "suffix": null,
            "credentials": "MD",
            "role": "Physician & Medical Director",
            "gender": "Male",
            "primaryPracticeCity": "SampleCity",
            "primaryPracticeState": "AR",
            "primaryPracticeLocationPhone": "870.000.0000",
            "primarySpecialty": "Surgery - Orthopedic Surgery",
            "primaryHospitalAffiliation": "Sample Medical Center",
            "primaryHospitalAffiliationDefinitiveID": "999",
            "secondaryHospitalAffiliation": "Medical Center of Sample Hospital",
            "secondaryHospitalAffiliationDefinitiveID": "999",
            "medicarePayments": "223946.28",
            "medicareClaimPayments": 223946.28,
            "medicareCharges": "644823.00",
            "medicareClaimCharges": 644823,
            "medicareUniquePatients": 609,
            "numberOfMedicalProcedures": 2599,
            "definitiveId": 999
           }
          ]
      }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

Hospital ID

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "personId": 0,
        "npi": 0,
        "firstName": "string",
        "middleName": "string",
        "lastName": "string",
        "prefix": "string",
        "suffix": "string",
        "credentials": "string",
        "role": "string",
        "gender": "string",
        "primaryPracticeCity": "string",
        "primaryPracticeState": "string",
        "primaryPracticeLocationPhone": "string",
        "primarySpecialty": "string",
        "primaryHospitalAffiliation": "string",
        "primaryHospitalAffiliationDefinitiveID": "string",
        "secondaryHospitalAffiliation": "string",
        "secondaryHospitalAffiliationDefinitiveID": "string",
        "medicarePayments": "string",
        "medicareClaimPayments": 0,
        "medicareCharges": "string",
        "medicareClaimCharges": 0,
        "medicareUniquePatients": 0,
        "numberOfMedicalProcedures": 0,
        "definitiveId": 0
      }
    }

_No links_

POST/v1/hospitals/{id}/physicians/affiliated/search

Provides array of physicians affiliated with the hospital and search parameters specified

    When filtering data, the following OperatorTypes can be used (valid value data types in parentheses):
            
    Equals (numeric, string, date)
    NotEquals(numeric, string, date)
    GreaterThan(numeric, date)
    LessThan(numeric, date)
    GreaterThanOrEqual(numeric, date)
    LessThanOrEqual(numeric, date)
    In(numeric, string, date)
    NotIn(numeric, string, date)
    StartsWith(string)
    EndsWith(string)
    Contains(string)
    IsNull(if used, Value not required for filter)
    IsNotNull(if used, Value not required for filter)
    True(Boolean - if used, Value not required for filter)
    False(Boolean - if used, Value not required for filter)
    
    When using operators "contains", "starts with" and "ends with", you must enter at least 3 characters when filtering.  
    The properties "primaryPracticeState" and "credentials" cannot be filtered by using "contains", "starts with" and "ends with" operators".
    

Sample request:

         POST /v1/hospitals/{id}/physicians/affiliated/search
    

Sample request body:

    [
        {
          "propertyName": "primaryPracticeState",
          "operatorType": "Equals",
          "value": "AR"
        }
    ]
    

Sample response:

    {
      "meta": {
        "pageSize": 2,
        "totalRecords": 2,
        "pageOffset": 1,
        "totalPages": 1
      },
      "data": [
       {
        "personId": 99999,
        "npi":  999999999,
        "firstName": "John",
        "middleName": "Sample",
        "lastName": "Doe",
        "prefix": "Dr.",
        "suffix": null,
        "credentials": "MD",
        "role": "Physician & Medical Director",
        "gender": "Male",
        "primaryPracticeCity": "SampleCity",
        "primaryPracticeState": "AR",
        "primaryPracticeLocationPhone": "870.000.0000",
        "primarySpecialty": "Surgery - Orthopedic Surgery",
        "primaryHospitalAffiliation": "Sample Medical Center",
        "primaryHospitalAffiliationDefinitiveID": "999",
        "secondaryHospitalAffiliation": "Medical Center of Sample Hospital",
        "secondaryHospitalAffiliationDefinitiveID": "999",
        "medicarePayments": "223946.28",
        "medicareClaimPayments": 223946.28,
        "medicareCharges": "644823.00",
        "medicareClaimCharges": 644823,
        "medicareUniquePatients": 609,
        "numberOfMedicalProcedures": 2599,
        "definitiveId": 999
       }
      ]
    }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

Hospital Id

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Request body

Please enter Filter Parameters in the request body

*   Example Value
*   Schema

    [
      {
        "propertyName": "string",
        "operatorType": "Equals",
        "value": "string"
      }
    ]

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "personId": 0,
        "npi": 0,
        "firstName": "string",
        "middleName": "string",
        "lastName": "string",
        "prefix": "string",
        "suffix": "string",
        "credentials": "string",
        "role": "string",
        "gender": "string",
        "primaryPracticeCity": "string",
        "primaryPracticeState": "string",
        "primaryPracticeLocationPhone": "string",
        "primarySpecialty": "string",
        "primaryHospitalAffiliation": "string",
        "primaryHospitalAffiliationDefinitiveID": "string",
        "secondaryHospitalAffiliation": "string",
        "secondaryHospitalAffiliationDefinitiveID": "string",
        "medicarePayments": "string",
        "medicareClaimPayments": 0,
        "medicareCharges": "string",
        "medicareClaimCharges": 0,
        "medicareUniquePatients": 0,
        "numberOfMedicalProcedures": 0,
        "definitiveId": 0
      }
    }

_No links_

GET/v1/hospitals/{id}/quality

Provides array of quality metrics for the hospital specified

Sample request:

         GET /v1/hospitals/{id}/quality
    

Sample response:

    {
        "meta": {
            "pageSize": 2,
            "totalRecords": 2,
            "pageOffset": 1,
            "totalPages": 1
        },
        "data": [
            {
                "name": "hacPenalty",
                "description": "HAC Rate Penalty (FY2021)",
                "dataType": "decimal",
                "numericValue": 10.8256,
                "value": "10.8256",
                "year": null,
                "definitiveId": 1973 
            },
            {
                "name": "hacPenaltyAdjustment",
                "description": "Revenue Loss Due to HAC Penalty (Est. FY2021)",
                "dataType": "integer",
                "numericValue": 10,
                "value": "10",
                "year": null,
                "definitiveId": 1973
            }
        ]
    }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

Hospital Id

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "name": "string",
        "description": "string",
        "numericValue": 0,
        "value": "string",
        "year": 0,
        "definitiveId": 0
      }
    }

_No links_

POST/v1/hospitals/{id}/quality/search

Provides array of quality metrics with the hospital and search parameters specified

When filtering data, the following OperatorTypes can be used (valid value data types in parentheses):

    Equals (numeric, string, date)
    NotEquals(numeric, string, date)
    GreaterThan(numeric, date)
    LessThan(numeric, date)
    GreaterThanOrEqual(numeric, date)
    LessThanOrEqual(numeric, date)
    In(numeric, string, date)
    NotIn(numeric, string, date)
    StartsWith(string)
    EndsWith(string)
    Contains(string)
    IsNull(if used, Value not required for filter)
    IsNotNull(if used, Value not required for filter)
    True(Boolean - if used, Value not required for filter)
    False(Boolean - if used, Value not required for filter)
    
    When using operators "contains", "starts with" and "ends with", you must enter at least 3 characters when filtering.        
    

Sample request:

         POST /v1/hospitals/{id}/quality/search          
    

Sample request body:

    [
        {
          "propertyName": "name",
          "operatorType": "Contains",
          "value": "hacPenalty"
        }
    ]
    

Sample response:

    {
        "meta": {
            "pageSize": 2,
            "totalRecords": 2,
            "pageOffset": 1,
            "totalPages": 1
        },
        "data": [
            {
                "name": "hacPenalty",
                "description": "HAC Rate Penalty (FY2021)",
                "dataType": "decimal",
                "numericValue": 10.8256,
                "value": "10.8256",
                "year": null,
                "definitiveId": 1973
            },
            {
                "name": "hacPenaltyAdjustment",
                "description": "Revenue Loss Due to HAC Penalty (Est. FY2021)",
                "dataType": "integer",
                "numericValue": 10,
                "value": "10",
                "year": null,
                "definitiveId": 1973
            }
        ]
    }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

Hospital Id

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Request body

Please enter Filter Parameters in the request body

*   Example Value
*   Schema

    [
      {
        "propertyName": "string",
        "operatorType": "Equals",
        "value": "string"
      }
    ]

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "name": "string",
        "description": "string",
        "numericValue": 0,
        "value": "string",
        "year": 0,
        "definitiveId": 0
      }
    }

_No links_

GET/v1/hospitals/{id}/financials

Provides array of financial and clinical metrics with the hospital and search parameters specified

Sample request:

         GET /v1/hospitals/{id}/financials
    

Sample response:

    {
        "meta": {
            "pageSize": 2,
            "totalRecords": 2,
            "pageOffset": 1,
            "totalPages": 1
        },
        "data": [
            {
              "name": "avgLengthOfStay",
              "description": "Average Length of Stay",
              "dataType": "decimal",
              "numericValue": 3.42,
              "value": "3.42",
              "year": null,
              "definitiveId": 226
            },
            {
              "name": "licensedBeds",
              "description": "Licensed Beds",
              "dataType": "integer",
              "numericValue": 33,
              "value": "33",
              "year": null,
              "definitiveId": 226
            }
        ]
    }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "name": "string",
        "description": "string",
        "numericValue": 0,
        "value": "string",
        "year": 0,
        "definitiveId": 0
      }
    }

_No links_

POST/v1/hospitals/{id}/financials/search

Provides array of financial and clinical metrics for the hospital specified

When filtering data, the following OperatorTypes can be used (valid value data types in parentheses):

    Equals (numeric, string, date)
    NotEquals(numeric, string, date)
    GreaterThan(numeric, date)
    LessThan(numeric, date)
    GreaterThanOrEqual(numeric, date)
    LessThanOrEqual(numeric, date)
    In(numeric, string, date)
    NotIn(numeric, string, date)
    StartsWith(string)
    EndsWith(string)
    Contains(string)
    IsNull(if used, Value not required for filter)
    IsNotNull(if used, Value not required for filter)
    True(Boolean - if used, Value not required for filter)
    False(Boolean - if used, Value not required for filter)
    
    When using operators "contains", "starts with" and "ends with", you must enter at least 3 characters when filtering.        
    

Sample request:

         POST /v1/hospitals/{id}/financials/search
    

Sample request body:

    [
        {
          "propertyName": "description",
          "operatorType": "Contains",
          "value": "Licensed Beds"
        }
    ]
    

Sample response:

    {
        "meta": {
            "pageSize": 1,
            "totalRecords": 1,
            "pageOffset": 1,
            "totalPages": 1
        },
        "data": [
            {
              "name": "licensedBeds",
              "description": "Licensed Beds",
              "dataType": "integer",
              "numericValue": 33, 
              "value": "33",
              "year": null,
              "definitiveId": 226
            }
        ]
    }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

Hospital Id

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Request body

Please enter Filter Parameters in the request body

*   Example Value
*   Schema

    [
      {
        "propertyName": "string",
        "operatorType": "Equals",
        "value": "string"
      }
    ]

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "name": "string",
        "description": "string",
        "numericValue": 0,
        "value": "string",
        "year": 0,
        "definitiveId": 0
      }
    }

_No links_

GET/v1/hospitals/{id}/affiliations

Provides array of facilities affiliated with the hospital specified

Sample request:

         GET /v1/hospitals/{id}/affiliations
    

Sample response:

       {
          "meta": {
            "pageSize": 2,
            "totalRecords": 2,
            "pageOffset": 1,
            "totalPages": 1
          },
          "data": [
             {
              "affiliatedFacilityDefinitiveId": 999999,
              "facilityName": "Sample Medical Center",
              "firmType": "Skilled Nursing Facility",
              "addressLine1": "404 South Sample St",
              "addressLine2": null,
              "city": "SampleCity",
              "state": "AR",
              "zip": "00000",
              "latitude": null,
              "latitudeCoordinates": null,
              "longitude": null,
              "longitudeCoordinates": null,
              "subNetwork": "Sample Medical Center",
              "subNetworkDefinitiveId": 999,
              "definitiveId": 226
            },
            {
              "affiliatedFacilityDefinitiveId": 999990,
              "facilityName": "Sample Medical Center - Family Care Clinic",
              "firmType": "Rural Health Clinic",
              "addressLine1": "304 East Sample Two St",
              "addressLine2": null,
              "city": "SampleCity",
              "state": "AR",
              "zip": "0000",
              "latitude": null,
              "latitudeCoordinates": null,
              "longitude": null,
              "longitudeCoordinates": null,
              "subNetwork": "Sample Medical Center",
              "subNetworkDefinitiveId": 999,
              "definitiveId": 226
            }
          ]
        }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "affiliatedFacilityDefinitiveId": 0,
        "facilityName": "string",
        "firmType": "string",
        "addressLine1": "string",
        "addressLine2": "string",
        "city": "string",
        "state": "string",
        "zip": "string",
        "latitude": "string",
        "latitudeCoordinates": 0,
        "longitude": "string",
        "longitudeCoordinates": 0,
        "subNetwork": "string",
        "subNetworkDefinitiveId": 0,
        "definitiveId": 0
      }
    }

_No links_

POST/v1/hospitals/{id}/affiliations/search

Provides array of facilities affiliated with the hospital and filters specified

    When filtering data, the following OperatorTypes can be used (valid value data types in parentheses):
    
    Equals (numeric, string, date)
    NotEquals(numeric, string, date)
    GreaterThan(numeric, date)
    LessThan(numeric, date)
    GreaterThanOrEqual(numeric, date)
    LessThanOrEqual(numeric, date)
    In(numeric, string, date)
    NotIn(numeric, string, date)
    StartsWith(string)    
    EndsWith(string)
    Contains(string)
    IsNull(if used, Value not required for filter)
    IsNotNull(if used, Value not required for filter)
    True(Boolean - if used, Value not required for filter)
    False(Boolean - if used, Value not required for filter)
    
    When using operators "contains", "starts with" and "ends with", you must enter at least 3 characters when filtering. 
    The property "state" cannot be filtered by using "contains", "starts with" and "ends with" operators".
    

Sample request:

         POST /v1/hospitals/{id}/affiliations/search
    

Sample request body:

    [
        {
           "propertyName": "facilityName",
           "operatorType": "Contains",
           "value": "Sample"
        }
    ]
    

Sample response:

       {
          "meta": {
            "pageSize": 2,
            "totalRecords": 2,
            "pageOffset": 1,
            "totalPages": 1
          },
          "data": [
             {
              "affiliatedFacilityDefinitiveId": 999999,
              "facilityName": "Sample Medical Center",
              "firmType": "Skilled Nursing Facility",
              "addressLine1": "404 South Sample St",
              "addressLine2": null,
              "city": "SampleCity",
              "state": "AR",
              "zip": "00000",
              "latitude": null,
              "latitudeCoordinates": null,
              "longitude": null,
              "longitudeCoordinates": null,
              "subNetwork": "Sample Medical Center",
              "subNetworkDefinitiveId": 999,
              "definitiveId": 226
            },
            {
              "affiliatedFacilityDefinitiveId": 999990,
              "facilityName": "Sample Medical Center - Family Care Clinic",
              "firmType": "Rural Health Clinic",
              "addressLine1": "404 South Sample St",
              "addressLine2": null,
              "city": "SampleCity",
              "state": "AR",
              "zip": "00000",
              "latitude": null,
              "latitudeCoordinates": null,
              "longitude": null,
              "longitudeCoordinates": null,
              "subNetwork": "Sample Medical Center",
              "subNetworkDefinitiveId": 226,
              "definitiveId": 226
            }
          ]
        }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Request body

Please enter Filter Parameters in the request body

*   Example Value
*   Schema

    [
      {
        "propertyName": "string",
        "operatorType": "Equals",
        "value": "string"
      }
    ]

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "affiliatedFacilityDefinitiveId": 0,
        "facilityName": "string",
        "firmType": "string",
        "addressLine1": "string",
        "addressLine2": "string",
        "city": "string",
        "state": "string",
        "zip": "string",
        "latitude": "string",
        "latitudeCoordinates": 0,
        "longitude": "string",
        "longitudeCoordinates": 0,
        "subNetwork": "string",
        "subNetworkDefinitiveId": 0,
        "definitiveId": 0
      }
    }

_No links_

GET/v1/hospitals/{id}/memberships

Provides array of memberships with hospital specified.

Sample request:

         GET /v1/hospitals/{id}/memberships
    

Sample response:

       {
          "meta": {
            "pageSize": 10,
            "totalRecords": 3,
            "pageOffset": 1,
            "totalPages": 1
          },
          "data": [
             {
              "membershipDefinitiveId": 9999999,
              "type": "Accountable Care Organization",
              "name" : "Sample Medical Center 1",
              "subType": "Commercial ACO",        
              "definitiveId": 9999
             },
             {
              "membershipDefinitiveId": 9999998,
              "type": "Group Purchasing Organization",
              "name" : "Sample Medical Center 2",
              "subType": null,        
              "definitiveId": 9999
             },
             {
              "membershipDefinitiveId": 9999997,
              "type": "Health Information Exchange",
              "name" : "Sample Medical Center 3",
              "subType": null,        
              "definitiveId": 9999
             },
          ]
        }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "membershipDefinitiveId": 0,
        "type": "string",
        "name": "string",
        "subType": "string",
        "definitiveId": 0
      }
    }

_No links_

POST/v1/hospitals/{id}/memberships/search

Provides array of memberships with hospital specified.

    When filtering data, the following OperatorTypes can be used (valid value data types in parentheses):
    
    Equals (numeric, string, date)
    NotEquals(numeric, string, date)
    GreaterThan(numeric, date)
    LessThan(numeric, date)
    GreaterThanOrEqual(numeric, date)
    LessThanOrEqual(numeric, date)
    In(numeric, string, date)
    NotIn(numeric, string, date)
    StartsWith(string)    
    EndsWith(string)
    Contains(string)
    IsNull(if used, Value not required for filter)
    IsNotNull(if used, Value not required for filter)
    True(Boolean - if used, Value not required for filter)
    False(Boolean - if used, Value not required for filter)
    
    When using operators "contains", "starts with" and "ends with", you must enter at least 3 characters when filtering.        
    

Sample request:

         POST /v1/hospitals/{id}/memberships/search
    

Sample request body:

    [
        {
           "propertyName": "subType",
           "operatorType": "Contains",
           "value": "Sample"
        }
    ]
    

Sample response:

       {
          "meta": {
            "pageSize": 2,
            "totalRecords": 2,
            "pageOffset": 1,
            "totalPages": 1
                   },              
          "data": [
             {
              "membershipDefinitiveId": 9999999,
              "type": "Accountable Care Organization",
              "name" : "Sample Medical Center 1",
              "subType": "Commercial ACO",        
              "definitiveId": 9999
             },
             {
              "membershipDefinitiveId": 9999998,
              "type": "Group Purchasing Organization",
              "name" : "Sample Medical Center 2",
              "subType": null,        
              "definitiveId": 9999
             },
             {
              "membershipDefinitiveId": 9999997,
              "type": "Health Information Exchange",
              "name" : "Sample Medical Center 3",
              "subType": null,        
              "definitiveId": 9999
             },
          ]
        }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Request body

Please enter Filter Parameters in the request body

*   Example Value
*   Schema

    [
      {
        "propertyName": "string",
        "operatorType": "Equals",
        "value": "string"
      }
    ]

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "membershipDefinitiveId": 0,
        "type": "string",
        "name": "string",
        "subType": "string",
        "definitiveId": 0
      }
    }

_No links_

GET/v1/hospitals/{id}/requests

Provides array of request for proposals, RFP's, for the hospital specified.

Sample request:

         GET /v1/hospitals/{id}/requests/search             
    

Sample response:

       {
          "meta": {
            "pageSize": 1,
            "totalRecords": 1,
            "pageOffset": 1,
            "totalPages": 1
                   },              
          "data": [
             {
               "definitiveId": 990949,
               "facilityName": "Sample name", 
               "type": "Request for Proposal", 
               "datePosted": "2023-08-28", 
               "dateModified": "2023-08-29", 
               "dateDue": "2023-08-31", 
               "postingLink": "https://sample.gov/view", 
               "category": "Medical/Surgical Equipment or Supplies", 
               "contact": {        
                 "name": "John Doe", 
                 "email": "John.doe@va.gov", 
                 "phone": "999.999.9999", 
                 "title": "Contracting Officer" 
               }, 
               "definitiveRfpId": 99999999, 
               "description": "See RFP website for detailed list of requested items.", 
               "classification": "Combined Synopsis/Solicitation"
              }
          ]
       }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "definitiveId": 0,
        "facilityName": "string",
        "type": "string",
        "datePosted": "string",
        "dateModified": "string",
        "dateDue": "string",
        "postingLink": "string",
        "category": "string",
        "contact": {
          "name": "string",
          "email": "string",
          "phone": "string",
          "title": "string"
        },
        "definitiveRfpId": 0,
        "description": "string",
        "classification": "string"
      }
    }

_No links_

POST/v1/hospitals/{id}/requests/search

Provides array of request for proposals, RFP's, for the hospital specified.

    When filtering data, the following OperatorTypes can be used (valid value data types in parentheses):
    
    Equals (numeric, string, date)
    NotEquals(numeric, string, date)
    GreaterThan(numeric, date)
    LessThan(numeric, date)
    GreaterThanOrEqual(numeric, date)
    LessThanOrEqual(numeric, date)
    In(numeric, string, date)
    NotIn(numeric, string, date)
    StartsWith(string)    
    EndsWith(string)
    Contains(string)
    IsNull(if used, Value not required for filter)
    IsNotNull(if used, Value not required for filter)
    True(Boolean - if used, Value not required for filter)
    False(Boolean - if used, Value not required for filter)
    
    When using operators "contains", "starts with" and "ends with", you must enter at least 3 characters when filtering.   
    To filter on the "Contact" object you must use "isNull" and "isNotNull" operators.
    

Sample request:

         POST /v1/hospitals/{id}/requests/search
    

Sample request body:

    [
        {
           "propertyName": "facilityName",
           "operatorType": "Contains",
           "value": "Sample"
        }
    ]
    

Sample response:

       {
          "meta": {
            "pageSize": 1,
            "totalRecords": 1,
            "pageOffset": 1,
            "totalPages": 1
                   },              
          "data": [
             {
               "definitiveId": 990949,
               "facilityName": "Sample name", 
               "type": "Request for Proposal", 
               "datePosted": "2023-08-28", 
               "dateModified": "2023-08-29", 
               "dateDue": "2023-08-31", 
               "postingLink": "https://sample.gov/view", 
               "category": "Medical/Surgical Equipment or Supplies", 
               "contact": {        
                 "name": "John Doe", 
                 "email": "John.doe@va.gov", 
                 "phone": "999.999.9999", 
                 "title": "Contracting Officer" 
               }, 
               "definitiveRfpId": 99999999, 
               "description": "See RFP website for detailed list of requested items.", 
               "classification": "Combined Synopsis/Solicitation"
              }
          ]
       }

#### Parameters

Try it out

Name

Description

id \*

integer($int32)

(path)

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Request body

Please enter Filter Parameters in the request body

*   Example Value
*   Schema

    [
      {
        "propertyName": "string",
        "operatorType": "Equals",
        "value": "string"
      }
    ]

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "definitiveId": 0,
        "facilityName": "string",
        "type": "string",
        "datePosted": "string",
        "dateModified": "string",
        "dateDue": "string",
        "postingLink": "string",
        "category": "string",
        "contact": {
          "name": "string",
          "email": "string",
          "phone": "string",
          "title": "string"
        },
        "definitiveRfpId": 0,
        "description": "string",
        "classification": "string"
      }
    }

_No links_

POST/v1/hospitals/search

Provides array of all available hospitals. Users must provide at least one field parameter to narrow their search results

    At this time, the following properties are unsupported as part of a POST request body.
    1. DefinitiveProfileLink
    2. MedicalSchoolAffiliates  
    3. AccreditationAgency
    
    When filtering data, the following OperatorTypes can be used (valid value data types in parentheses):
    
    Equals (numeric, string, date)
    NotEquals(numeric, string, date)
    GreaterThan(numeric, date)
    LessThan(numeric, date)
    GreaterThanOrEqual(numeric, date)
    LessThanOrEqual(numeric, date)
    In(numeric, string, date)
    NotIn(numeric, string, date)
    StartsWith(string)     
    EndsWith(string)
    Contains(string)
    IsNull(if used, Value not required for filter)
    IsNotNull(if used, Value not required for filter)
    True(Boolean - if used, Value not required for filter)
    False(Boolean - if used, Value not required for filter)
    
    When using operators "contains", "starts with" and "ends with", you must enter at least 3 characters when filtering. 
    The property "state" cannot be filtered by using "contains", "starts with" and "ends with" operators".
    

Sample request:

         POST /v1/hospitals/search       
    

Sample request body:

    [
        {
           "propertyName": "facilityName",
           "operatorType": "Contains",
           "value": "Sample text"
        }
    ]
    

Sample response:

    {
      "meta": {
        "pageSize": 2,
        "totalRecords": 2,
        "pageOffset": 1,
        "totalPages": 1
      },
      "data": [
        {
          "facilityName": "Sample Medical Center - East Campus",
          "definitiveId": 999,
          "medicareProviderNumber": "99999F",
          "facilityPrimaryNpi": 111111111,
          "facilityNpiList":
            [
              111111111,
              123456789
            ]
          "firmType": "Hospital",
          "hospitalType": "Short Term Acute Care Hospital",
          "addressLine1": "1276 Sample Ave",
          "addressLine2": null,
          "city": "SampleCity",
          "state": "NY",
          "zip": "00000",
          "latitude": "40.1XXXXX",
          "latitudeCoordinates": 40.1XXXXX,
          "longitude": "-73.9XXXXXX",
          "longitudeCoordinates": -73.9XXXXXX,
          "county": null,
          "region": "NorthEast",
          "geographicClassification": "Urban",
          "cbsaCode": 35620,
          "cbsaDescription": "New York XXXX",
          "definitiveProfileLink": "https://www.defhc.com/hospitals/DEFINITIVEID",
          "medicalSchoolAffiliates": "New York Medical College",
          "medicalSchoolAffiliatesList": 
            [ 
              "Sample Acedemic Medical College University", 
              "Tufts University School of Medicine" 
            ],
          "networkId": 999999,
          "networkName": "Sample Health System",
          "networkParentId": 999999,
          "networkParentName": "Sample Health System",
          "description": "For more than 100 years, Sample Health System Center has provided quality and compassionate health care to those in need, regardless of their ability to pay.",
          "website": "www.SAMPLEHEALTHCENTER.org",
          "networkOwnership": "Owned",
          "ownership": "Voluntary Nonprofit - Other",
          "companyStatus": "Active",
          "phone": "718.000.0000",
          "fiscalYearEndMonth": 1,
          "fiscalYearEndDay": 31,
          "academicMedicalCenter": true
          "accreditationAgency": "The Joint Commission",
          "accreditationAgencyList": 
            [ 
              "The Joint Commission", 
              "Second Accreditation Agency" 
            ],
          "pediatricTraumaCenter": "Level I",
          "traumaCenter": "Level I"
          "IDNIntegrationLevel": "System III (vertical integration)",
          "facility340BId": "H999999",
          "taxId": "09-9999999" 
          "medicareAdministrativeContract": "Sample Company"
          "marketConcentrationIndex": 0.005
          "payorMixMedicaid": 0.700
          "payorMixMedicare": 0.700
          "payorMixSelfPay": 0.700
        },
        {
          "facilityName": "Sample Health System Name",
          "definitiveId": 999,
          "medicareProviderNumber": "99999F",
          "facilityPrimaryNpi": 111111111,
          "facilityNpiList":
            [
              111111111,
              123456789
            ]
          "firmType": "Hospital",
          "hospitalType": "Short Term Acute Care Hospital",
          "addressLine1": "134 Sample Health Ave",
          "addressLine2": null,
          "city": "SampleCity",
          "state": "NY",
          "zip": "00000",
          "latitude": "42.XXXX",
          "latitudeCoordinates": 42.XXXX,
          "longitude": "-7.XXXXX",
          "longitudeCoordinates": -7.XXXXX,
          "county": null,
          "region": "NorthEast",
          "geographicClassification": "Urban",
          "cbsaCode": 18660,
          "cbsaDescription": "Sample Text",
          "definitiveProfileLink": "https://www.defhc.com/hospitals/DEFINITIVEID",
          "medicalSchoolAffiliates": null,
          "medicalSchoolAffiliatesList": 
            [ 
              "Sample Acedemic Medical College University", 
              "Tufts University School of Medicine" 
            ],
          "networkId": 9999,
          "networkName": "Sample Health Clinic",
          "networkParentId": null,
          "networkParentName": "Sample Health Clinic",             
          "description": "Sample Health Clinic has been in service for more than 110 years.",
          "website": "www.SAMPLEHEALTHCENTER.org",
          "networkOwnership": "Owned",
          "ownership": "Voluntary Nonprofit - Other",
          "companyStatus": "Active",
          "phone": "607.000.0000",
          "fiscalYearEndMonth": 6,
          "fiscalYearEndDay": 30,
          "academicMedicalCenter": true,
          "accreditationAgency": "The Joint Commission"
          "accreditationAgencyList": 
            [ 
               "The Joint Commission", 
               "Second Accreditation Agency" 
            ],
          "pediatricTraumaCenter": "Level I",
          "traumaCenter": "Level I"
          "IDNIntegrationLevel": "System III (vertical integration)",
          "facility340BId": "H999999",
          "taxId": "09-9999999" ,
          "medicareAdministrativeContract": "Sample Company"
          "marketConcentrationIndex": 0.005
          "payorMixMedicaid": 0.700
          "payorMixMedicare": 0.700
          "payorMixSelfPay": 0.700
        }
      ]
    }

#### Parameters

Try it out

Name

Description

page\[size\]

int

(query)

Number of Records

_Default value_ : 10

page\[offset\]

int

(query)

Page Number

_Default value_ : 1

#### Request body

Please enter Filter Parameters in the request body

*   Example Value
*   Schema

    [
      {
        "propertyName": "string",
        "operatorType": "Equals",
        "value": "string"
      }
    ]

#### Responses

Code

Description

Links

200

Success

Media type

Controls `Accept` header.

*   Example Value
*   Schema

    {
      "meta": {
        "pageSize": 0,
        "totalRecords": 0,
        "pageOffset": 0,
        "totalPages": 0
      },
      "data": {
        "facilityName": "string",
        "definitiveId": 0,
        "medicareProviderNumber": "string",
        "facilityPrimaryNpi": 0,
        "facilityNpiList": [
          0
        ],
        "firmType": "string",
        "hospitalType": "string",
        "addressLine1": "string",
        "addressLine2": "string",
        "city": "string",
        "state": "string",
        "zip": "string",
        "latitude": "string",
        "latitudeCoordinates": 0,
        "longitude": "string",
        "longitudeCoordinates": 0,
        "county": "string",
        "region": "string",
        "geographicClassification": "string",
        "cbsaCode": 0,
        "cbsaDescription": "string",
        "definitiveProfileLink": "string",
        "medicalSchoolAffiliates": "string",
        "medicalSchoolAffiliatesList": [
          "string"
        ],
        "networkId": 0,
        "networkName": "string",
        "networkParentId": 0,
        "networkParentName": "string",
        "description": "string",
        "website": "string",
        "networkOwnership": "string",
        "ownership": "string",
        "companyStatus": "string",
        "phone": "string",
        "fiscalYearEndDay": 0,
        "fiscalYearEndMonth": 0,
        "academicMedicalCenter": true,
        "accreditationAgency": "string",
        "accreditationAgencyList": [
          "string"
        ],
        "pediatricTraumaCenter": "string",
        "traumaCenter": "string",
        "IDNIntegrationLevel": "string",
        "facility340BId": "string",
        "taxId": "string",
        "medicareAdministrativeContract": "string",
        "marketConcentrationIndex": 0,
        "payorMixMedicaid": 0,
        "payorMixMedicare": 0,
        "payorMixSelfPay": 0
      }
    }

_No links_

#### Schemas

FilterParameter{

propertyName

\[...\]

operatorType

OperatorTypes\[...\]

value

{...}  
nullable: true

}

HospitalAffiliations{

affiliatedFacilityDefinitiveId

\[...\]

facilityName

\[...\]

firmType

\[...\]

addressLine1

\[...\]

addressLine2

\[...\]

city

\[...\]

state

\[...\]

zip

\[...\]

latitude

\[...\]

latitudeCoordinates

\[...\]

longitude

\[...\]

longitudeCoordinates

\[...\]

subNetwork

\[...\]

subNetworkDefinitiveId

\[...\]

definitiveId

\[...\]

}

HospitalAffiliationsApiResponse{

meta

Meta{...}

data

HospitalAffiliations{...}

}

HospitalExecutives{

personId

\[...\]

executiveId

\[...\]

firstName

\[...\]

middleName

\[...\]

lastName

\[...\]

prefix

\[...\]

suffix

\[...\]

credentials

\[...\]

gender

\[...\]

department

\[...\]

positionLevel

\[...\]

standardizedTitle

\[...\]

title

\[...\]

primaryEmail

\[...\]

directPhone

\[...\]

locationPhone

\[...\]

linkedinProfileURL

\[...\]

physicianFlag

\[...\]

physicianLeader

\[...\]

executiveNPI

\[...\]

lastUpdatedDate

\[...\]

definitiveId

\[...\]

mobilePhone

\[...\]

directEmail

\[...\]

mobilePhones

\[...\]

directEmails

\[...\]

}

HospitalExecutivesApiResponse{

meta

Meta{...}

data

HospitalExecutives{...}

}

HospitalFinancials{

name

\[...\]

description

\[...\]

numericValue

\[...\]

value

\[...\]

year

\[...\]

definitiveId

\[...\]

}

HospitalFinancialsApiResponse{

meta

Meta{...}

data

HospitalFinancials{...}

}

HospitalMemberships{

membershipDefinitiveId

\[...\]

type

\[...\]

name

\[...\]

subType

\[...\]

definitiveId

\[...\]

}

HospitalMembershipsApiResponse{

meta

Meta{...}

data

HospitalMemberships{...}

}

HospitalNewsAndIntelligence{

publicationDate

\[...\]

intelligenceType

\[...\]

newsEventTitle

\[...\]

bodyOfArticle

\[...\]

publicationId

\[...\]

definitiveId

\[...\]

}

HospitalNewsAndIntelligenceApiResponse{

meta

Meta{...}

data

HospitalNewsAndIntelligence{...}

}

HospitalPhysicians{

personId

\[...\]

npi

\[...\]

firstName

\[...\]

middleName

\[...\]

lastName

\[...\]

prefix

\[...\]

suffix

\[...\]

credentials

\[...\]

role

\[...\]

gender

\[...\]

primaryPracticeCity

\[...\]

primaryPracticeState

\[...\]

primaryPracticeLocationPhone

\[...\]

primarySpecialty

\[...\]

primaryHospitalAffiliation

\[...\]

primaryHospitalAffiliationDefinitiveID

\[...\]

secondaryHospitalAffiliation

\[...\]

secondaryHospitalAffiliationDefinitiveID

\[...\]

medicarePayments

\[...\]

medicareClaimPayments

\[...\]

medicareCharges

\[...\]

medicareClaimCharges

\[...\]

medicareUniquePatients

\[...\]

numberOfMedicalProcedures

\[...\]

definitiveId

\[...\]

}

HospitalPhysiciansApiResponse{

meta

Meta{...}

data

HospitalPhysicians{...}

}

HospitalQuality{

name

\[...\]

description

\[...\]

numericValue

\[...\]

value

\[...\]

year

\[...\]

definitiveId

\[...\]

}

HospitalQualityApiResponse{

meta

Meta{...}

data

HospitalQuality{...}

}

HospitalRFPs{

definitiveId

\[...\]

facilityName

\[...\]

type

\[...\]

datePosted

\[...\]

dateModified

\[...\]

dateDue

\[...\]

postingLink

\[...\]

category

\[...\]

contact

RfpContact{...}

definitiveRfpId

\[...\]

description

\[...\]

classification

\[...\]

}

HospitalRFPsApiResponse{

meta

Meta{...}

data

HospitalRFPs{...}

}

HospitalSearch{

facilityName

\[...\]

definitiveId

\[...\]

medicareProviderNumber

\[...\]

facilityPrimaryNpi

\[...\]

facilityNpiList

\[...\]

firmType

\[...\]

hospitalType

\[...\]

addressLine1

\[...\]

addressLine2

\[...\]

city

\[...\]

state

\[...\]

zip

\[...\]

latitude

\[...\]

latitudeCoordinates

\[...\]

longitude

\[...\]

longitudeCoordinates

\[...\]

county

\[...\]

region

\[...\]

geographicClassification

\[...\]

cbsaCode

\[...\]

cbsaDescription

\[...\]

definitiveProfileLink

\[...\]

medicalSchoolAffiliates

\[...\]

medicalSchoolAffiliatesList

\[...\]

networkId

\[...\]

networkName

\[...\]

networkParentId

\[...\]

networkParentName

\[...\]

description

\[...\]

website

\[...\]

networkOwnership

\[...\]

ownership

\[...\]

companyStatus

\[...\]

phone

\[...\]

fiscalYearEndDay

\[...\]

fiscalYearEndMonth

\[...\]

academicMedicalCenter

\[...\]

accreditationAgency

\[...\]

accreditationAgencyList

\[...\]

pediatricTraumaCenter

\[...\]

traumaCenter

\[...\]

IDNIntegrationLevel

\[...\]

facility340BId

\[...\]

taxId

\[...\]

medicareAdministrativeContract

\[...\]

marketConcentrationIndex

\[...\]

payorMixMedicaid

\[...\]

payorMixMedicare

\[...\]

payorMixSelfPay

\[...\]

}

HospitalSearchApiResponse{

meta

Meta{...}

data

HospitalSearch{...}

}

HospitalSummary{

facilityName

\[...\]

definitiveId

\[...\]

medicareProviderNumber

\[...\]

facilityPrimaryNpi

\[...\]

facilityNpiList

\[...\]

firmType

\[...\]

hospitalType

\[...\]

addressLine1

\[...\]

addressLine2

\[...\]

city

\[...\]

state

\[...\]

zip

\[...\]

latitude

\[...\]

latitudeCoordinates

\[...\]

longitude

\[...\]

longitudeCoordinates

\[...\]

county

\[...\]

region

\[...\]

geographicClassification

\[...\]

cbsaCode

\[...\]

cbsaDescription

\[...\]

definitiveProfileLink

\[...\]

medicalSchoolAffiliates

\[...\]

medicalSchoolAffiliatesList

\[...\]

networkId

\[...\]

networkName

\[...\]

networkParentId

\[...\]

networkParentName

\[...\]

description

\[...\]

website

\[...\]

networkOwnership

\[...\]

ownership

\[...\]

companyStatus

\[...\]

phone

\[...\]

fiscalYearEndDay

\[...\]

fiscalYearEndMonth

\[...\]

academicMedicalCenter

\[...\]

accreditationAgency

\[...\]

accreditationAgencyList

\[...\]

pediatricTraumaCenter

\[...\]

traumaCenter

\[...\]

IDNIntegrationLevel

\[...\]

facility340BId

\[...\]

taxId

\[...\]

medicareAdministrativeContract

\[...\]

marketConcentrationIndex

\[...\]

payorMixMedicaid

\[...\]

payorMixMedicare

\[...\]

payorMixSelfPay

\[...\]

primaryPhysiciansCount

\[...\]

secondaryPhysiciansCount

\[...\]

}

HospitalSummaryApiResponse{

meta

Meta{...}

data

HospitalSummary{...}

}

HospitalTechnologiesCurrentImplementations{

category

\[...\]

technology

\[...\]

vendor

\[...\]

product

\[...\]

vendorStatus

\[...\]

implementationYear

\[...\]

unitsInstalled

\[...\]

definitiveId

\[...\]

}

HospitalTechnologiesCurrentImplementationsApiResponse{

meta

Meta{...}

data

HospitalTechnologiesCurrentImplementations{...}

}

Meta{

pageSize

\[...\]

totalRecords

\[...\]

pageOffset

\[...\]

totalPages

\[...\]

}

OperatorTypesinteger($int32)Enum:  
Array \[ 15 \]

RfpContact{

name

\[...\]

email

\[...\]

phone

\[...\]

title

\[...\]

}

Handling errors & versioning

Handling errorsIf errors occur during API configuration, you’ll see specific keys in the HTTP server response. The keys indicate the error type and often how to fix it.

Key

Value

Status code

HTTP server responses indicating the outcome of your request including 400 - bad request, 401 - unauthorized, 403 - forbidden and 500 - internal server error.

Timestamp

Reflects the time the error occurs. Time stamp displays the current date and time and formats it as "YYYY-MM-DDT00:00:00" (e.g., "2023-07-24T12:34:56").

Message

Describes what went wrong, enabling you to identify and solve the problem.

Message examples:

*   Request body contains invalid property name(s). Review the property name(s).
*   Request isn't complete. Review format or missing syntax.
*   Operator entered isn't compatible with the data type of the property name ‘0.’ Use one of the following operators: ‘1.’