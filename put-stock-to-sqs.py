import boto3
import time
import datetime
import random
from tqdm import tqdm

sqs = boto3.client('sqs')
sts = boto3.client('sts')

def current_aws_account_number():
    return sts.get_caller_identity().get('Account')

for stock_event_number in tqdm(range(3000)):
    stock_id = random.choice(['A', 'B', 'C']) + str(random.randint(1, 5)) * 3
    stock_level = random.randint(2, 100)
    line = f"{stock_id};{stock_level}"

    try:
        response = sqs.send_message(
            QueueUrl = f'https://sqs.eu-west-1.amazonaws.com/{current_aws_account_number()}/CleanServerlessQueue',
            MessageBody = (line)
        )
    except:
        pass
    
    # print(stock_event_number, response)
    #time.sleep(0.0005)