from aws_cdk import (
    Stack,
    Size,
    Duration,
    RemovalPolicy,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_sns as sns,
    aws_sqs as sqs,
    aws_lambda_event_sources as event_sources,
    aws_kinesisfirehose_alpha as firehose,
    aws_kinesisfirehose_destinations_alpha as destinations,
    aws_s3 as s3,
    aws_glue as glue,
)
from constructs import Construct

class CleanServerlessArchitectureDemoStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

# ----------------------------------------------------------------------------------------
# LAMBDA + API GATEWAY + DYNAMODB
# ----------------------------------------------------------------------------------------
        simple_lambda = _lambda.Function(self, "SimpleLambda",
            function_name="CleanServerlessFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="simple_lambda.handler",
            code=_lambda.Code.from_asset("lambda"),
        )
        
        api = apigw.LambdaRestApi(self, "Endpoint",
            handler=simple_lambda,
        )
        
        table = dynamodb.Table(self, "SimpleTable", table_name = 'CleanServerlessTable',
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        table.grant_read_write_data(simple_lambda)
        
# ----------------------------------------------------------------------------------------
# SNS
# ----------------------------------------------------------------------------------------
        topic = sns.Topic(self, "CleanServerlessTopic",
            topic_name="CleanServerlessTopic"
        )
        topic.grant_publish(simple_lambda)

        sub_sms = sns.Subscription(self, "SubscriptionSMS",
            endpoint="+33000000000", # ========================> Replace with a valid phone number
            protocol=sns.SubscriptionProtocol.SMS,
            topic=topic
        )
        
# ----------------------------------------------------------------------------------------
# SQS
# ----------------------------------------------------------------------------------------
        queue = sqs.Queue(self, "Queue",
            queue_name = "CleanServerlessQueue",
        )
        queue.grant_consume_messages(simple_lambda)

        simple_lambda.add_event_source(
            event_sources.SqsEventSource(queue,
                batch_size=1
            )
        )
        
# ----------------------------------------------------------------------------------------
# S3 + FIREHOSE
# ----------------------------------------------------------------------------------------
        bucket = s3.Bucket(self, "Bucket", 
            bucket_name=f"clean-serverless-bucket-{self.account}"
        )
        
        delivery_stream = firehose.DeliveryStream(self, "DeliveryStream", 
            delivery_stream_name = "CleanServerlessTableDeliveryStream",
            destinations=[
                destinations.S3Bucket(bucket, 
                    buffering_size=Size.mebibytes(1),
                    buffering_interval=Duration.minutes(1),
                )
            ]
        )
        delivery_stream.grant_put_records(simple_lambda)
 
# ----------------------------------------------------------------------------------------
# ATHENA
# ----------------------------------------------------------------------------------------
        glue_database = glue.CfnDatabase(self,'demo_database',
            catalog_id=self.account,
            database_input=glue.CfnDatabase.DatabaseInputProperty(
                name='demo',
            )
        )
        
        glue_table = glue.CfnTable(self, "MyCfnTable", 
                catalog_id=self.account,
                database_name="demo",
                table_input=glue.CfnTable.TableInputProperty(
                    name="stock_level",
                    storage_descriptor=glue.CfnTable.StorageDescriptorProperty(
                        columns=[
                        glue.CfnTable.ColumnProperty(
                            name="stock_id",
                            type="string"
                        ), 
                        glue.CfnTable.ColumnProperty(
                            name="stock_level",
                            type="int"
                        )],
                        location=f"s3://clean-serverless-bucket-{self.account}/",
                        input_format="org.apache.hadoop.mapred.TextInputFormat",
                        output_format="org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                        serde_info=glue.CfnTable.SerdeInfoProperty(
                            parameters={
                                "field.delim": ";",
                                "serialization.format": ",",
                            },
                            serialization_library="org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe"
                        ),
                    )
                ),
        )
        
        glue_table.node.add_dependency(glue_database)