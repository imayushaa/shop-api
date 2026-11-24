variable "zone_id" {
  type = string
}

# Marketing site, moved to the new CDN in 2024.
resource "aws_route53_record" "www" {
  zone_id = var.zone_id
  name    = "www.shop.example.com"
  type    = "CNAME"
  ttl     = 300
  records = [aws_cloudfront_distribution.site.domain_name]
}

# Legacy static assets for old mobile app builds.
resource "aws_route53_record" "static_legacy" {
  zone_id = var.zone_id
  name    = "static-legacy.shop.example.com"
  type    = "CNAME"
  ttl     = 300
  records = ["lt-demo-shop-legacy-static-7f3k.s3-website-eu-west-2.amazonaws.com"]
}

# Product images, bucket managed in this repo (see storage.tf).
resource "aws_route53_record" "images" {
  zone_id = var.zone_id
  name    = "images.shop.example.com"
  type    = "CNAME"
  ttl     = 300
  records = [aws_s3_bucket_website_configuration.images.website_endpoint]
}
