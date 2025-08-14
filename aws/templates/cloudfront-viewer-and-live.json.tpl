{
  "CallerReference": "__CALLER_REF__",
  "Comment": "Agentic demo: viewer (S3) + live (MediaPackage HLS) with /live/* path",
  "DefaultRootObject": "index.html",
  "Origins": {
    "Quantity": 3,
    "Items": [
      {
        "Id": "s3viewer",
        "DomainName": "__BUCKET_DOMAIN__",
        "OriginAccessControlId": "__OAC_ID__",
        "S3OriginConfig": {
          "OriginAccessIdentity": ""
        }
      },
      {
        "Id": "mediapackage-live",
        "DomainName": "__MP_DOMAIN__",
        "OriginPath": "__MP_ORIGIN_PATH__",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "https-only",
          "OriginSslProtocols": {
            "Quantity": 3,
            "Items": [ "TLSv1.2", "TLSv1.1", "TLSv1" ]
          },
          "OriginReadTimeout": 30,
          "OriginKeepaliveTimeout": 5
        }
      },
      {
        "Id": "control-plane",
        "DomainName": "__CTRL_DOMAIN__",
        "CustomOriginConfig": {
          "HTTPPort": 80,
          "HTTPSPort": 443,
          "OriginProtocolPolicy": "https-only",
          "OriginSslProtocols": {
            "Quantity": 3,
            "Items": [ "TLSv1.2", "TLSv1.1", "TLSv1" ]
          },
          "OriginReadTimeout": 30,
          "OriginKeepaliveTimeout": 5
        }
      }
    ]
  },
  "DefaultCacheBehavior": {
    "TargetOriginId": "s3viewer",
    "ViewerProtocolPolicy": "redirect-to-https",
    "AllowedMethods": {
      "Quantity": 2,
      "Items": [ "GET", "HEAD" ],
      "CachedMethods": {
        "Quantity": 2,
        "Items": [ "GET", "HEAD" ]
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
  "CacheBehaviors": {
    "Quantity": 3,
    "Items": [
      {
        "PathPattern": "live/*",
        "TargetOriginId": "mediapackage-live",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
          "Quantity": 2,
          "Items": [ "GET", "HEAD" ],
          "CachedMethods": {
            "Quantity": 2,
            "Items": [ "GET", "HEAD" ]
          }
        },
        "FunctionAssociations": {
          "Quantity": 1,
          "Items": [
            {
              "EventType": "viewer-request",
              "FunctionARN": "__LIVE_FN_ARN__"
            }
          ]
        },
        "Compress": true,
        "ForwardedValues": {
          "QueryString": true,
          "Cookies": { "Forward": "none" }
        },
        "MinTTL": 0,
        "DefaultTTL": 1,
        "MaxTTL": 5
      },
      {
        "PathPattern": "api/*",
        "TargetOriginId": "control-plane",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
          "Quantity": 4,
          "Items": [ "GET", "HEAD", "OPTIONS", "POST" ],
          "CachedMethods": {
            "Quantity": 2,
            "Items": [ "GET", "HEAD" ]
          }
        },
        "Compress": true,
        "ForwardedValues": {
          "QueryString": true,
          "Cookies": { "Forward": "none" }
        },
        "MinTTL": 0,
        "DefaultTTL": 0,
        "MaxTTL": 0
      },
      {
        "PathPattern": "telemetry/*",
        "TargetOriginId": "control-plane",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
          "Quantity": 3,
          "Items": [ "GET", "HEAD", "OPTIONS" ],
          "CachedMethods": {
            "Quantity": 2,
            "Items": [ "GET", "HEAD" ]
          }
        },
        "Compress": true,
        "ForwardedValues": {
          "QueryString": true,
          "Cookies": { "Forward": "none" }
        },
        "MinTTL": 0,
        "DefaultTTL": 0,
        "MaxTTL": 0
      }
    ]
  },
  "PriceClass": "PriceClass_All",
  "Enabled": true,
  "ViewerCertificate": { "CloudFrontDefaultCertificate": true },
  "Aliases": { "Quantity": 0 },
  "HttpVersion": "http2",
  "IsIPV6Enabled": true
}