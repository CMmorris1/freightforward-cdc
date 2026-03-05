terraform {
  backend "s3" {
    bucket         = "sw-concepts-s3-bucket"
    key            = "projects/my-app/terraform.tfstate" # Path within the bucket
    region         = "us-east-1"                          # Use your bucket's region
    encrypt        = true
  }
}