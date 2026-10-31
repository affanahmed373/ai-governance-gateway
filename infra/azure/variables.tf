variable "prefix" {
  type    = string
  default = "aigw"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "location" {
  type    = string
  default = "westeurope"
}

variable "tags" {
  type = map(string)
  default = {
    project = "ai-governance-gateway"
  }
}
