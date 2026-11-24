resource "aws_s3_bucket" "images" {
  bucket = "lt-demo-shop-product-images-2c9q"
}

resource "aws_s3_bucket_website_configuration" "images" {
  bucket = aws_s3_bucket.images.id

  index_document {
    suffix = "index.html"
  }
}

resource "aws_s3_bucket_public_access_block" "images" {
  bucket                  = aws_s3_bucket.images.id
  block_public_acls       = true
  block_public_policy     = false
  ignore_public_acls      = true
  restrict_public_buckets = false
}

resource "aws_cloudfront_distribution" "site" {
  enabled = true

  origin {
    domain_name = aws_s3_bucket.images.bucket_regional_domain_name
    origin_id   = "images"
  }

  default_cache_behavior {
    target_origin_id       = "images"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
