services_fields = {
    'create_customer': [
        'P_TRXN_NO', 'P_CPR_CR', 'P_CUST_NAME', 'P_USER_NAME','P_CONTACT_NO',
        'P_EMAIL', 'P_ORDER_NO', 'P_AUTHENTICATE', "P_CIRCUIT_NO", "P_ATTRIBUTE1",
        "P_ATTRIBUTE2"
    ],
	'delete_customer': [
        'P_TRXN_NO', 'P_CPR_CR', 'P_USER_NAME', 'P_ORDER_NO','P_AUTHENTICATE',
        'P_ATTRIBUTE1','P_ATTRIBUTE2'
    ],
	'create_service': [
        'P_TRXN_NO', 'P_CPR_CR', 'P_USER_NAME', 'P_ORDER_NO', 'P_PACKAGE_ID',
        'P_AUTHENTICATE','P_ATTRIBUTE1','P_ATTRIBUTE2'
    ],
	'disconnect_service': [
        'P_TRXN_NO', 'P_CPR_CR', 'P_USER_NAME', 'P_ORDER_NO', 'P_PACKAGE_ID',
        'P_AUTHENTICATE','P_ATTRIBUTE1','P_ATTRIBUTE2'
    ],
	'control_action': [
        'P_TRXN_NO', 'P_CPR_CR', 'P_USER_NAME', 'P_CREDIT_ACTION','P_AUTHENTICATE',
        'P_ATTRIBUTE1','P_ATTRIBUTE2'
    ],
}
mandatory_fields = {
    'create_customer': ['P_TRXN_NO', 'P_CPR_CR', 'P_CUST_NAME', 'P_USER_NAME','P_CONTACT_NO', 'P_EMAIL', 'P_ORDER_NO', 'P_AUTHENTICATE'],
	'delete_customer': ['P_TRXN_NO', 'P_CPR_CR', 'P_USER_NAME', 'P_ORDER_NO','P_AUTHENTICATE'],
	'create_service': ['P_TRXN_NO', 'P_CPR_CR', 'P_USER_NAME', 'P_ORDER_NO', 'P_PACKAGE_ID','P_AUTHENTICATE'],
	'disconnect_service': ['P_TRXN_NO', 'P_CPR_CR', 'P_USER_NAME', 'P_ORDER_NO', 'P_PACKAGE_ID','P_AUTHENTICATE'],
	'control_action': ['P_TRXN_NO', 'P_CPR_CR', 'P_USER_NAME', 'P_CREDIT_ACTION','P_AUTHENTICATE'],
}

fields_and_types = {
    "P_TRXN_NO": "int", "P_CPR_CR": "string", "P_CUST_NAME": "string",
    "P_USER_NAME": "string", "P_CONTACT_NO": "string", "P_EMAIL": "string",
    "P_ORDER_NO": "string", "P_AUTHENTICATE": "string", "P_CIRCUIT_NO": "string",
    "P_PACKAGE_ID": "string", "P_CREDIT_ACTION": "string"
}

fields_and_length = {
    "P_CPR_CR": 15, "P_CUST_NAME": 100,
    "P_USER_NAME": 50, "P_CONTACT_NO": 10, "P_EMAIL": 30,
    "P_ORDER_NO": 15, "P_AUTHENTICATE": 15,
    "P_PACKAGE_ID": 15, "P_CREDIT_ACTION": 15,
    "P_ATTRIBUTE1": 30, "P_ATTRIBUTE2": 30,
}
