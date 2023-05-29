import shortuuid
from datetime import datetime

def generate_payment_reference():
    uuid = shortuuid.uuid()
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    reference = f'{uuid}{timestamp}'

    return reference