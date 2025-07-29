# app/utils/order_id_generator.py

import datetime
import random
import string

def generate_order_id():
    prefix = "SNS"  # Short for S&S Collection
    date_part = datetime.datetime.now().strftime("%Y%m%d")
    rand_part = ''.join(random.choices(string.digits, k=4))
    return f"{prefix}{date_part}{rand_part}"
