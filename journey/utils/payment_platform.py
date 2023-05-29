import os, requests
import json

from factory import Faker

def get_acceptance_token():
    api_key = os.environ['WOMPI_PUBLIC_KEY']
    api_endpoint = f"{os.environ['WOMPI_HOST']}/merchants/{api_key}"

    payload = {}
    headers = {}

    response = requests.request("GET", api_endpoint, headers=headers, data=payload)
    response_data = response.json()
    acceptance_token = response_data['data']['presigned_acceptance']['acceptance_token']
    return acceptance_token


def get_tokenized_card(card_holder):
    # Generar datos fake para la tarjeta
    card_number = '4242424242424242'
    cvc = Faker("credit_card_security_code").evaluate(None, None, extra={"locale": None})
    credit_card_expire = Faker("credit_card_expire").evaluate(None, None, extra={"locale": None}).split('/')
    exp_month = credit_card_expire[0]
    exp_year = credit_card_expire[1]

    api_endpoint = f"{os.environ['WOMPI_HOST']}/tokens/cards"
    api_key = os.environ['WOMPI_PUBLIC_KEY']

    payload = {
        "number": card_number,
        "cvc": cvc,
        "exp_month": exp_month,
        "exp_year": exp_year,
        "card_holder": card_holder,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
    }

    response = requests.post(api_endpoint, json=payload, headers=headers)
    response_data = response.json()
    return response_data['data']['id']

def get_payment_source(token, acceptance_token, customer_email):
    api_endpoint = f"{os.environ['WOMPI_HOST']}/payment_sources"
    api_key = os.environ['WOMPI_PRIVATE_KEY']

    payload = json.dumps({
        "type": "CARD",
        "token": token,
        "customer_email": customer_email,
        "acceptance_token": acceptance_token
    })
    headers = {
        'ACCESS_TOKEN': '{{token}}',
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    response = requests.request("POST", api_endpoint, headers=headers, data=payload)
    response_data = response.json()
    if response.status_code == 201:
        payment_source = response_data['data']['id']
        return {"status": response.status_code, "payment_source": payment_source}
    else:
        return {"status": response.status_code, "data": response_data}
