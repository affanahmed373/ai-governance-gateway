variable "prefix" {
  type    = string
  default = "aigw"
}

variable "location" {
  type        = string
  description = "Azure region. Default is northeurope; some subscriptions cannot create Log Analytics in westeurope."
  default     = "northeurope"
}

variable "image" {
  type        = string
  description = "Public container image built by CI."
  default     = "ghcr.io/affanahmed373/ai-governance-gateway:latest"
}

variable "tags" {
  type = map(string)
  default = {
    project = "ai-governance-gateway"
    purpose = "public-demo"
  }
}
