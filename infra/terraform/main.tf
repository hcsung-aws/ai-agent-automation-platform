# Game Ops Multi-Agent Infrastructure
# Terraform configuration for AWS resources (excluding Knowledge Base)

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  default = "us-east-1"
}

variable "project_name" {
  default = "game-ops-agent"
}

data "aws_caller_identity" "current" {}

# S3 Bucket for data and Athena results
resource "aws_s3_bucket" "data_bucket" {
  bucket        = "${var.project_name}-${data.aws_caller_identity.current.account_id}"
  force_destroy = true

  tags = {
    Project = var.project_name
  }
}

# DynamoDB - Incident Tickets
resource "aws_dynamodb_table" "incident_tickets" {
  name         = "incident-tickets"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "ticket_id"
  range_key    = "created_at"

  attribute {
    name = "ticket_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  attribute {
    name = "game_name"
    type = "S"
  }

  global_secondary_index {
    name            = "game-index"
    hash_key        = "game_name"
    range_key       = "created_at"
    projection_type = "ALL"
  }

  tags = {
    Project = var.project_name
  }
}

# DynamoDB - Execution Logs
resource "aws_dynamodb_table" "execution_logs" {
  name         = "execution-logs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"
  range_key    = "timestamp"

  attribute {
    name = "session_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  tags = {
    Project = var.project_name
  }
}

# Glue Database for analytics
resource "aws_glue_catalog_database" "game_logs" {
  name        = "game_logs"
  description = "MMORPG game analytics database"
}

# IAM Role for Agent execution
resource "aws_iam_role" "agent_role" {
  name = "GameOpsAgentRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = [
            "bedrock.amazonaws.com",
            "lambda.amazonaws.com",
            "glue.amazonaws.com"
          ]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Project = var.project_name
  }
}

# IAM Policy for Agent
resource "aws_iam_role_policy" "agent_policy" {
  name = "GameOpsAgentPolicy"
  role = aws_iam_role.agent_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchAccess"
        Effect = "Allow"
        Action = [
          "cloudwatch:GetMetricStatistics",
          "cloudwatch:ListMetrics",
          "cloudwatch:GetMetricData"
        ]
        Resource = "*"
      },
      {
        Sid    = "EC2ReadAccess"
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeInstanceStatus",
          "ec2:DescribeTags"
        ]
        Resource = "*"
      },
      {
        Sid    = "CloudFormationAccess"
        Effect = "Allow"
        Action = [
          "cloudformation:DescribeStacks",
          "cloudformation:DescribeStackEvents",
          "cloudformation:ListStacks"
        ]
        Resource = "*"
      },
      {
        Sid    = "BedrockAccess"
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:Retrieve",
          "bedrock:RetrieveAndGenerate"
        ]
        Resource = "*"
      },
      {
        Sid    = "AthenaAccess"
        Effect = "Allow"
        Action = [
          "athena:StartQueryExecution",
          "athena:GetQueryExecution",
          "athena:GetQueryResults",
          "athena:StopQueryExecution"
        ]
        Resource = "*"
      },
      {
        Sid    = "GlueAccess"
        Effect = "Allow"
        Action = [
          "glue:GetDatabase",
          "glue:GetDatabases",
          "glue:GetTable",
          "glue:GetTables",
          "glue:GetPartitions",
          "glue:CreateTable",
          "glue:CreatePartition",
          "glue:DeleteTable"
        ]
        Resource = "*"
      },
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_bucket.arn,
          "${aws_s3_bucket.data_bucket.arn}/*"
        ]
      },
      {
        Sid    = "DynamoDBAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.incident_tickets.arn,
          "${aws_dynamodb_table.incident_tickets.arn}/index/*",
          aws_dynamodb_table.execution_logs.arn
        ]
      }
    ]
  })
}

# Outputs
output "agent_role_arn" {
  value = aws_iam_role.agent_role.arn
}

output "data_bucket_name" {
  value = aws_s3_bucket.data_bucket.id
}

output "incident_table_name" {
  value = aws_dynamodb_table.incident_tickets.name
}

output "execution_logs_table_name" {
  value = aws_dynamodb_table.execution_logs.name
}

output "glue_database_name" {
  value = aws_glue_catalog_database.game_logs.name
}
