"""
IRS Mock Data
Realistic response payloads for testing the IRS A2A Client.
"""

MOCK_TRANSCRIPT_2024 = {
    "taxYear": 2024,
    " taxpayerId": "***-**-1234",
    "filingStatus": "Single",
    "adjustedGrossIncome": 150000,
    "taxableIncome": 138000,
    "totalTax": 24000,
    "transactions": [
        {"code": "150", "description": "Tax Return Filed", "date": "2025-04-15", "amount": 24000},
        {
            "code": "806",
            "description": "W-2 or 1099 Withholding",
            "date": "2025-04-15",
            "amount": -25000,
        },
        {
            "code": "766",
            "description": "Credit to your account",
            "date": "2025-04-15",
            "amount": -2000,
        },
        {"code": "846", "description": "Refund issued", "date": "2025-05-01", "amount": 3000},
    ],
}

MOCK_STATUS_RESPONSE = {
    "submissionId": "123456789012345",
    "status": "Accepted",
    "receivedDate": "2025-04-15T10:00:00Z",
    "acceptanceDate": "2025-04-15T10:05:00Z",
    "errors": [],
}
