{
  "CallerReference": "__CALLER_REF__",
  "Comment": "Agentic demo viewer only (S3 origin)",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 1,
    "Items": [
      {
        "Id": "s3viewer",
        "DomainName": "__BUCKET_DOMAIN__",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "s3viewer",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": ["GET", "HEAD"],
      "CachedMethods": {
        "Quantity": 2,
        "Items": ["GET", "HEAD"]
      }
    },
    "Compress": true,
    "ForwardedValues": {
      "QueryString": true,
      "Cookies": { "Forward": "none" }
    },
    "MinTTL": 0,
    "DefaultTTL": 60,
    "MaxTTL": 300
  },
  "PriceClass": "PriceClass_All",
  "Enabled": true,
  "Aliases": { "Quantity": 0 },
  "HttpVersion": "http2",
  "IsIPV6Enabled": true
}
