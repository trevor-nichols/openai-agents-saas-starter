resource "aws_iam_role" "task_execution" {
  name = "${local.name_prefix}-ecs-exec"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "task_execution" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_secretsmanager_secret" "registry" {
  count = local.registry_enabled ? 1 : 0
  name  = "${local.name_prefix}-registry-credentials"
}

resource "aws_secretsmanager_secret_version" "registry" {
  count         = local.registry_enabled ? 1 : 0
  secret_id     = aws_secretsmanager_secret.registry[0].id
  secret_string = jsonencode({ username = var.registry_username, password = var.registry_password })
}

resource "aws_iam_role_policy" "task_execution_registry" {
  count = local.registry_enabled ? 1 : 0
  name  = "${local.name_prefix}-registry"
  role  = aws_iam_role.task_execution.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = aws_secretsmanager_secret.registry[0].arn
      }
    ]
  })
}

resource "aws_iam_role" "task" {
  name = "${local.name_prefix}-ecs-task"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "task_s3" {
  name = "${local.name_prefix}-s3"
  role = aws_iam_role.task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject", "s3:ListBucket"]
        Resource = [
          "arn:aws:s3:::${var.storage_bucket_name}",
          "arn:aws:s3:::${var.storage_bucket_name}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy" "task_secrets" {
  count = length(local.secret_arns) > 0 ? 1 : 0
  name  = "${local.name_prefix}-secrets"
  role  = aws_iam_role.task.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue", "secretsmanager:PutSecretValue"]
        Resource = local.secret_arns
      }
    ]
  })
}
