resource "random_id" "db_final" {
  byte_length = 4
}

resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_db_instance" "main" {
  identifier                = "${local.name_prefix}-db"
  engine                    = "postgres"
  engine_version            = "16.2"
  instance_class            = var.db_instance_class
  allocated_storage         = var.db_allocated_storage
  db_subnet_group_name      = aws_db_subnet_group.main.name
  vpc_security_group_ids    = [aws_security_group.db.id]
  db_name                   = var.db_name
  username                  = var.db_username
  password                  = var.db_password
  storage_encrypted         = var.db_storage_encrypted
  deletion_protection       = var.db_deletion_protection
  skip_final_snapshot       = var.db_skip_final_snapshot
  final_snapshot_identifier = var.db_skip_final_snapshot ? null : "${local.name_prefix}-final-${random_id.db_final.hex}"
  backup_retention_period   = var.db_backup_retention_days
  multi_az                  = false
  publicly_accessible       = var.db_publicly_accessible
}
