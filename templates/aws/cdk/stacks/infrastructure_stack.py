"""Infrastructure Stack - ECR, IAM, KMS, KB S3, S3 Vectors, Bedrock KB 등 기반 인프라.

AgentCore 배포를 위한 기반 인프라를 구성합니다.
"""
from aws_cdk import (
    Duration,
    Stack,
    RemovalPolicy,
    aws_bedrock as bedrock,
    aws_dynamodb as dynamodb,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_kms as kms,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_events,
    aws_logs as logs,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_s3vectors as s3vectors,
    aws_sqs as sqs,
    CfnOutput,
)
from constructs import Construct


class InfrastructureStack(Stack):
    """AgentCore 기반 인프라 스택."""
    
    def __init__(self, scope: Construct, construct_id: str, stack_prefix: str = "AIOps", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # 리소스명 접두사 (소문자)
        prefix = stack_prefix.lower()
        
        # === KMS 키 (암호화) ===
        self.kms_key = kms.Key(
            self, "AgentCoreKey",
            description=f"{stack_prefix} Agent encryption key",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.RETAIN,
        )
        
        # CloudWatch Logs가 KMS 키를 사용할 수 있도록 권한 부여
        self.kms_key.grant_encrypt_decrypt(
            iam.ServicePrincipal(f"logs.{self.region}.amazonaws.com")
        )
        
        # === ECR 리포지토리 (Agent 컨테이너) ===
        self.ecr_repo = ecr.Repository(
            self, "AgentRepository",
            repository_name=f"{prefix}-agents",
            encryption=ecr.RepositoryEncryption.KMS,
            encryption_key=self.kms_key,
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True,
            image_scan_on_push=True,  # 보안 스캔
        )
        
        # === Knowledge Base S3 버킷 (데이터 소스) ===
        self.kb_bucket = s3.Bucket(
            self, "KnowledgeBaseBucket",
            bucket_name=f"{prefix}-kb-{self.account}-{self.region}",
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )
        
        # === S3 Vectors (벡터 스토어) ===
        vector_bucket = s3vectors.CfnVectorBucket(
            self, "VectorBucket",
            vector_bucket_name=f"{prefix}-vectors-{self.account}",
        )
        vector_bucket.apply_removal_policy(RemovalPolicy.DESTROY)
        
        vector_index = s3vectors.CfnIndex(
            self, "VectorIndex",
            vector_bucket_name=vector_bucket.vector_bucket_name,
            index_name=f"{prefix}-kb-index",
            dimension=1024,  # Titan V2 Embeddings
            distance_metric="cosine",
            data_type="float32",
            metadata_configuration={
                "nonFilterableMetadataKeys": [
                    "AMAZON_BEDROCK_TEXT",
                    "AMAZON_BEDROCK_METADATA",
                ],
            },
        )
        vector_index.add_dependency(vector_bucket)
        
        # === Bedrock KB 서비스 역할 ===
        self.kb_role = iam.Role(
            self, "KBServiceRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Bedrock Knowledge Base service role",
        )
        
        # 임베딩 모델 호출
        self.kb_role.add_to_policy(iam.PolicyStatement(
            actions=["bedrock:InvokeModel"],
            resources=[
                f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0",
            ],
        ))
        
        # S3 데이터 소스 읽기
        self.kb_role.add_to_policy(iam.PolicyStatement(
            actions=["s3:ListBucket"],
            resources=[self.kb_bucket.bucket_arn],
        ))
        self.kb_role.add_to_policy(iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[f"{self.kb_bucket.bucket_arn}/*"],
        ))
        
        # S3 Vectors 읽기/쓰기
        self.kb_role.add_to_policy(iam.PolicyStatement(
            actions=[
                "s3vectors:PutVectors",
                "s3vectors:GetVectors",
                "s3vectors:DeleteVectors",
                "s3vectors:QueryVectors",
                "s3vectors:GetIndex",
            ],
            resources=[
                f"arn:aws:s3vectors:{self.region}:{self.account}:bucket/{vector_bucket.vector_bucket_name}/index/{vector_index.index_name}",
            ],
        ))
        
        # === Bedrock Knowledge Base ===
        embedding_model_arn = f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0"
        
        self.knowledge_base = bedrock.CfnKnowledgeBase(
            self, "KnowledgeBase",
            name=f"{prefix}-knowledge-base",
            role_arn=self.kb_role.role_arn,
            knowledge_base_configuration={
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": embedding_model_arn,
                    "embeddingModelConfiguration": {
                        "bedrockEmbeddingModelConfiguration": {
                            "dimensions": 1024,
                        },
                    },
                },
            },
            storage_configuration={
                "type": "S3_VECTORS",
                "s3VectorsConfiguration": {
                    "vectorBucketArn": vector_bucket.attr_vector_bucket_arn,
                    "indexArn": vector_index.attr_index_arn,
                },
            },
        )
        self.knowledge_base.add_dependency(vector_index)
        self.knowledge_base.node.add_dependency(self.kb_role)
        
        # KB ID (다른 스택에서 참조)
        self.kb_id = self.knowledge_base.attr_knowledge_base_id
        
        # === Bedrock DataSource (S3 → KB) ===
        self.data_source = bedrock.CfnDataSource(
            self, "KBDataSource",
            knowledge_base_id=self.kb_id,
            name=f"{prefix}-kb-s3-source",
            data_source_configuration={
                "type": "S3",
                "s3Configuration": {
                    "bucketArn": self.kb_bucket.bucket_arn,
                    "inclusionPrefixes": ["knowledge-base/"],
                },
            },
        )
        
        # === KB 자동 Sync 파이프라인 (S3 → SQS → Lambda → StartIngestionJob) ===
        sync_dlq = sqs.Queue(self, "KBSyncDLQ",
            queue_name=f"{prefix}-kb-sync-dlq",
            retention_period=Duration.days(14),
        )

        sync_queue = sqs.Queue(self, "KBSyncQueue",
            queue_name=f"{prefix}-kb-sync",
            visibility_timeout=Duration.seconds(120),
            dead_letter_queue=sqs.DeadLetterQueue(max_receive_count=3, queue=sync_dlq),
        )

        # S3 이벤트 → SQS (knowledge-base/ prefix의 PUT/DELETE)
        self.kb_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.SqsDestination(sync_queue),
            s3.NotificationKeyFilter(prefix="knowledge-base/"),
        )
        self.kb_bucket.add_event_notification(
            s3.EventType.OBJECT_REMOVED,
            s3n.SqsDestination(sync_queue),
            s3.NotificationKeyFilter(prefix="knowledge-base/"),
        )

        # Lambda: StartIngestionJob 호출
        sync_fn = _lambda.Function(self, "KBSyncFunction",
            function_name=f"{prefix}-kb-sync",
            runtime=_lambda.Runtime.PYTHON_3_12,
            architecture=_lambda.Architecture.ARM_64,
            handler="index.handler",
            timeout=Duration.seconds(60),
            code=_lambda.Code.from_inline(
                'import boto3, os\n'
                'client = boto3.client("bedrock-agent")\n'
                'def handler(event, context):\n'
                '    try:\n'
                '        resp = client.start_ingestion_job(\n'
                '            knowledgeBaseId=os.environ["KB_ID"],\n'
                '            dataSourceId=os.environ["DS_ID"],\n'
                '        )\n'
                '        print(f"Ingestion started: {resp[\'ingestionJob\'][\'ingestionJobId\']}")\n'
                '    except client.exceptions.ConflictException:\n'
                '        print("Ingestion already in progress, skipping")\n'
            ),
            environment={
                "KB_ID": self.kb_id,
                "DS_ID": self.data_source.attr_data_source_id,
            },
        )

        sync_fn.add_to_role_policy(iam.PolicyStatement(
            actions=["bedrock:StartIngestionJob"],
            resources=[
                f"arn:aws:bedrock:{self.region}:{self.account}:knowledge-base/{self.kb_id}",
            ],
        ))

        # SQS → Lambda (배치 윈도우 60초: 여러 파일 업로드 시 한 번만 실행)
        sync_fn.add_event_source(lambda_events.SqsEventSource(
            sync_queue,
            batch_size=10,
            max_batching_window=Duration.seconds(60),
        ))

        # === DynamoDB 피드백 테이블 ===
        self.feedback_table = dynamodb.Table(
            self, "FeedbackTable",
            table_name=f"{prefix}-feedback",
            partition_key=dynamodb.Attribute(
                name="message_id", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="timestamp", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
        )
        
        # === CloudWatch 로그 그룹 ===
        self.log_group = logs.LogGroup(
            self, "AgentLogs",
            log_group_name=f"/{prefix}/agents",
            retention=logs.RetentionDays.ONE_MONTH,
            encryption_key=self.kms_key,
            removal_policy=RemovalPolicy.DESTROY,
        )
        
        # === IAM 역할 (AgentCore Runtime) ===
        self.agent_role = iam.Role(
            self, "AgentCoreRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="AgentCore Runtime execution role",
        )
        
        # Bedrock 모델 호출 권한
        self.agent_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream",
            ],
            resources=["arn:aws:bedrock:*::foundation-model/*"],
        ))
        
        # CloudWatch 로그 권한
        self.agent_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "logs:CreateLogStream",
                "logs:PutLogEvents",
            ],
            resources=[self.log_group.log_group_arn + ":*"],
        ))
        
        # KMS 복호화 권한
        self.kms_key.grant_decrypt(self.agent_role)
        
        # KB S3 버킷 읽기 권한
        self.kb_bucket.grant_read(self.agent_role)
        
        # === IAM 역할 (Agent Builder - Kiro CLI) ===
        self.builder_role = iam.Role(
            self, "AgentBuilderRole",
            assumed_by=iam.AccountPrincipal(self.account),
            description="Agent Builder (Kiro CLI) role",
        )
        
        # ECR 푸시 권한
        self.ecr_repo.grant_pull_push(self.builder_role)
        
        # KB S3 버킷 읽기/쓰기 권한
        self.kb_bucket.grant_read_write(self.builder_role)
        
        # AgentCore 관리 권한
        self.builder_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:CreateAgent",
                "bedrock:UpdateAgent",
                "bedrock:DeleteAgent",
                "bedrock:GetAgent",
                "bedrock:ListAgents",
            ],
            resources=["*"],
        ))
        
        # === Outputs ===
        CfnOutput(self, "ECRRepositoryUri",
            value=self.ecr_repo.repository_uri,
            description="ECR repository URI",
        )
        
        CfnOutput(self, "AgentRoleArn",
            value=self.agent_role.role_arn,
            description="AgentCore Runtime role ARN",
        )
        
        CfnOutput(self, "KMSKeyArn",
            value=self.kms_key.key_arn,
            description="Encryption key ARN",
        )
        
        CfnOutput(self, "KBBucketName",
            value=self.kb_bucket.bucket_name,
            description="Knowledge Base S3 bucket (data source)",
        )
        
        CfnOutput(self, "KnowledgeBaseId",
            value=self.kb_id,
            description="Bedrock Knowledge Base ID",
        )
        
        CfnOutput(self, "DataSourceId",
            value=self.data_source.attr_data_source_id,
            description="Bedrock KB Data Source ID",
        )
        
        CfnOutput(self, "FeedbackTableName",
            value=self.feedback_table.table_name,
            description="Feedback DynamoDB table name",
        )
