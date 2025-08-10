{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowCloudFrontOACReadOnly",
      "Effect": "Allow",
      "Principal": { "Service": "cloudfront.amazonaws.com" },
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::__BUCKET_NAME__/*",
      "Condition": {
        "StringEquals": {
          "AWS:SourceArn": "__CF_DISTRIBUTION_ARN__"
        }
      }
    }
  ]
}