## Prerequisite

- Python 3.9 installed

- CDK >= 2.133 installed

## Deploy architecture

If you want to receive sms from sns:

Open 
`_clean_serverless_architecture_demo/_clean_serverless_architecture_demo_stack.py`

then, put a valid phone number in the sns subscription
```
        sub_sms = sns.Subscription(self, "SubscriptionSMS",
            endpoint="+33600000000", # <========== Replace with a valid phone number
            protocol=sns.SubscriptionProtocol.SMS,
            topic=topic
        )
```

In the terminal:

```
$> cdk deploy
```

## Test API

In the AWS console, go to API Gateway>Endpoint>Any>Test

Request body:
```
{
    "stock_id": "A000",
    "stock_level": 1
}
```

Click on [TEST] button

In the AWS console, Go to DynamoDB>Tables>CleanServerlessTable>Explore Table Items

Verify the item has been inserted

## Test SQS Queue

Open 
`lambda/simple_lambda.py`

replace 
`api_gateway_adapter(event)`
with
`sqs_adapter_receive_message(event)`

In the terminal:
```
$> cdk deploy
```

Execute sqs script
```
$>python put-stock-to-sqs.py
```

When finished, in the AWS console, go to Athena

execute sql statement:
```sql
SELECT * FROM "demo"."stock_level" limit 10;
```

Verify the items have been inserted

---
N.B.: You should not receive any sms in this test since the script does 
not generate values lower or equal to 2