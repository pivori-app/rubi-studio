# ============================================================================
# Rubi Studio - Windows Server 2022 + MetaTrader 5 on Scaleway (AMSTERDAM)
# ============================================================================
# Version: 1.1.0
# Purpose: Terraform configuration to deploy Windows Server 2022 with MT5
# Author: Expert Architecte Senior Backend
# Date: 23 Octobre 2025
# Location: Amsterdam 1 (nl-ams-1)
# ============================================================================

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = "~> 2.47"
    }
  }

  # Uncomment to use remote state
  # backend "s3" {
  #   bucket         = "rubi-studio-terraform"
  #   key            = "windows-mt5/terraform.tfstate"
  #   region         = "nl-ams"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }
}

# ============================================================================
# PROVIDER CONFIGURATION
# ============================================================================

provider "scaleway" {
  zone       = var.scaleway_zone
  region     = var.scaleway_region
  access_key = var.scaleway_access_key
  secret_key = var.scaleway_secret_key
  project_id = var.scaleway_project_id
}

# ============================================================================
# VARIABLES
# ============================================================================

variable "scaleway_access_key" {
  description = "Scaleway Access Key"
  type        = string
  sensitive   = true
}

variable "scaleway_secret_key" {
  description = "Scaleway Secret Key"
  type        = string
  sensitive   = true
}

variable "scaleway_project_id" {
  description = "Scaleway Project ID"
  type        = string
  sensitive   = true
}

variable "scaleway_zone" {
  description = "Scaleway Zone"
  type        = string
  default     = "nl-ams-1"  # Amsterdam 1 (PAR DÉFAUT)
  
  validation {
    condition     = contains(["fr-par-1", "nl-ams-1", "pl-waw-1"], var.scaleway_zone)
    error_message = "Zone must be: fr-par-1 (Paris), nl-ams-1 (Amsterdam), or pl-waw-1 (Warsaw)."
  }
}

variable "scaleway_region" {
  description = "Scaleway Region"
  type        = string
  default     = "nl-ams"  # Amsterdam (PAR DÉFAUT)
  
  validation {
    condition     = contains(["fr-par", "nl-ams", "pl-waw"], var.scaleway_region)
    error_message = "Region must be: fr-par (Paris), nl-ams (Amsterdam), or pl-waw (Warsaw)."
  }
}

variable "instance_name" {
  description = "Nom de l'instance Windows"
  type        = string
  default     = "rubi-studio-mt5-windows"
}

variable "instance_type" {
  description = "Type d'instance Scaleway"
  type        = string
  default     = "ELEMENTS-VC1M"  # 2 vCPU, 8GB RAM (RECOMMANDÉ)
  
  validation {
    condition     = contains(["ELEMENTS-VC1S", "ELEMENTS-VC1M", "ELEMENTS-GP1-S"], var.instance_type)
    error_message = "Instance type must be ELEMENTS-VC1S, ELEMENTS-VC1M, or ELEMENTS-GP1-S."
  }
}

variable "root_volume_size_gb" {
  description = "Taille du volume root en GB"
  type        = number
  default     = 50
  
  validation {
    condition     = var.root_volume_size_gb >= 30 && var.root_volume_size_gb <= 200
    error_message = "Root volume size must be between 30 and 200 GB."
  }
}

variable "enable_ipv6" {
  description = "Activer IPv6"
  type        = bool
  default     = false
}

variable "rdp_allowed_ips" {
  description = "Liste des IPs autorisées pour RDP"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # À restreindre en production
}

variable "environment" {
  description = "Environnement (dev, staging, production)"
  type        = string
  default     = "production"
  
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "tags" {
  description = "Tags pour l'instance"
  type        = list(string)
  default     = ["rubi-studio", "mt5", "windows", "trading", "amsterdam"]
}

# ============================================================================
# LOCALS
# ============================================================================

locals {
  zone_names = {
    "fr-par-1" = "Paris 1 (France)"
    "nl-ams-1" = "Amsterdam 1 (Pays-Bas)"
    "pl-waw-1" = "Warsaw 1 (Pologne)"
  }

  region_names = {
    "fr-par" = "Paris (France)"
    "nl-ams" = "Amsterdam (Pays-Bas)"
    "pl-waw" = "Warsaw (Pologne)"
  }

  instance_specs = {
    "ELEMENTS-VC1S" = {
      vcpu  = 2
      ram   = 4
      cost  = 10
      tier  = "budget"
    }
    "ELEMENTS-VC1M" = {
      vcpu  = 2
      ram   = 8
      cost  = 20
      tier  = "standard"
    }
    "ELEMENTS-GP1-S" = {
      vcpu  = 4
      ram   = 8
      cost  = 25
      tier  = "performance"
    }
  }

  specs = local.instance_specs[var.instance_type]
  
  common_tags = concat(
    var.tags,
    [
      "environment:${var.environment}",
      "terraform:true",
      "zone:${local.zone_names[var.scaleway_zone]}",
      "created:${formatdate("YYYY-MM-DD", timestamp())}"
    ]
  )
}

# ============================================================================
# SECURITY GROUP
# ============================================================================

resource "scaleway_instance_security_group" "mt5_sg" {
  name                    = "${var.instance_name}-sg"
  description             = "Security group for MetaTrader 5 Windows Server (${local.zone_names[var.scaleway_zone]})"
  inbound_default_policy  = "drop"
  outbound_default_policy = "accept"
  project_id             = var.scaleway_project_id

  tags = local.common_tags

  # ========================================================================
  # INBOUND RULES
  # ========================================================================

  # RDP (Remote Desktop Protocol) - Port 3389
  dynamic "inbound_rule" {
    for_each = var.rdp_allowed_ips
    content {
      action   = "accept"
      protocol = "tcp"
      port     = 3389
      ip       = inbound_rule.value
    }
  }

  # Backend API Communication - Port 8000
  inbound_rule {
    action   = "accept"
    protocol = "tcp"
    port     = 8000
    ip       = "0.0.0.0/0"
  }

  # HTTPS - Port 443
  inbound_rule {
    action   = "accept"
    protocol = "tcp"
    port     = 443
    ip       = "0.0.0.0/0"
  }

  # HTTP - Port 80
  inbound_rule {
    action   = "accept"
    protocol = "tcp"
    port     = 80
    ip       = "0.0.0.0/0"
  }

  # DNS - Port 53 (UDP)
  inbound_rule {
    action   = "accept"
    protocol = "udp"
    port     = 53
    ip       = "0.0.0.0/0"
  }

  # NTP (Time Synchronization) - Port 123 (UDP)
  inbound_rule {
    action   = "accept"
    protocol = "udp"
    port     = 123
    ip       = "0.0.0.0/0"
  }

  # ICMP (Ping)
  inbound_rule {
    action   = "accept"
    protocol = "icmp"
    ip       = "0.0.0.0/0"
  }
}

# ============================================================================
# INSTANCE WINDOWS SERVER 2022
# ============================================================================

resource "scaleway_instance_server" "mt5_windows" {
  name              = var.instance_name
  type              = var.instance_type
  image             = "windows-server-2022"
  root_volume_size_gb = var.root_volume_size_gb
  
  security_group_id = scaleway_instance_security_group.mt5_sg.id
  
  # Enable public IPv4
  enable_ipv4 = true
  enable_ipv6 = var.enable_ipv6
  
  # Tags for organization
  tags = local.common_tags
  
  # Metadata for initialization
  user_data = base64encode(templatefile("${path.module}/windows_init.ps1", {
    backend_url = "http://localhost:8000"
    api_token   = "your-api-token"
    environment = var.environment
  }))

  # Prevent accidental deletion
  lifecycle {
    prevent_destroy = false
    ignore_changes  = [user_data]
  }

  depends_on = [scaleway_instance_security_group.mt5_sg]
}

# ============================================================================
# ELASTIC IP (Static Public IP)
# ============================================================================

resource "scaleway_instance_ip" "mt5_ip" {
  server_id = scaleway_instance_server.mt5_windows.id
  
  tags = local.common_tags
}

# ============================================================================
# OUTPUTS
# ============================================================================

output "instance_id" {
  description = "ID de l'instance Windows"
  value       = scaleway_instance_server.mt5_windows.id
}

output "instance_name" {
  description = "Nom de l'instance"
  value       = scaleway_instance_server.mt5_windows.name
}

output "instance_type" {
  description = "Type d'instance"
  value       = var.instance_type
}

output "instance_ip" {
  description = "Adresse IP publique de l'instance"
  value       = scaleway_instance_ip.mt5_ip.address
  sensitive   = false
}

output "location" {
  description = "Localisation de l'instance"
  value       = local.zone_names[var.scaleway_zone]
}

output "instance_specs" {
  description = "Spécifications de l'instance"
  value = {
    vcpu     = local.specs.vcpu
    ram      = "${local.specs.ram}GB"
    ssd      = "${var.root_volume_size_gb}GB"
    cost     = "${local.specs.cost}€/mois"
    location = local.zone_names[var.scaleway_zone]
  }
}

output "rdp_connection_string" {
  description = "Chaîne de connexion RDP"
  value       = "mstsc /v:${scaleway_instance_ip.mt5_ip.address}"
}

output "rdp_instructions" {
  description = "Instructions de connexion RDP"
  value       = <<-EOT
╔════════════════════════════════════════════════════════════════════════════╗
║                    CONNEXION WINDOWS SERVER 2022                           ║
║                   ${local.zone_names[var.scaleway_zone]}                   ║
╚════════════════════════════════════════════════════════════════════════════╝

Adresse IP : ${scaleway_instance_ip.mt5_ip.address}
Localisation : ${local.zone_names[var.scaleway_zone]}
Zone : ${var.scaleway_zone}

Méthode 1 : Ligne de commande
──────────────────────────────
mstsc /v:${scaleway_instance_ip.mt5_ip.address}

Méthode 2 : Remote Desktop Connection (GUI)
────────────────────────────────────────────
1. Ouvrir "Remote Desktop Connection" (mstsc)
2. Entrer l'adresse IP : ${scaleway_instance_ip.mt5_ip.address}
3. Cliquer sur "Connect"
4. Utiliser les credentials Scaleway
5. Accepter le certificat auto-signé

Méthode 3 : PowerShell
──────────────────────
$ip = "${scaleway_instance_ip.mt5_ip.address}"
mstsc /v:$ip

Prochaines étapes après connexion :
────────────────────────────────────
1. Télécharger MetaTrader 5
2. Installer MT5
3. Configurer le compte broker
4. Copier RubiStudioConnector.mq5 dans MQL5/Experts/
5. Compiler l'EA dans MetaEditor
6. Configurer les paramètres de connexion
7. Attacher l'EA à un graphique

Informations de l'instance :
────────────────────────────
- Localisation : ${local.zone_names[var.scaleway_zone]}
- Zone : ${var.scaleway_zone}
- Type : ${var.instance_type}
- vCPU : ${local.specs.vcpu}
- RAM : ${local.specs.ram}GB
- SSD : ${var.root_volume_size_gb}GB
- Coût : ${local.specs.cost}€/mois
- Environnement : ${var.environment}

╚════════════════════════════════════════════════════════════════════════════╝
  EOT
}

output "security_group_id" {
  description = "ID du security group"
  value       = scaleway_instance_security_group.mt5_sg.id
}

output "security_group_name" {
  description = "Nom du security group"
  value       = scaleway_instance_security_group.mt5_sg.name
}

output "cost_per_month" {
  description = "Coût estimé par mois"
  value       = "${local.specs.cost}€/mois"
}

output "cost_per_year" {
  description = "Coût estimé par an"
  value       = "${local.specs.cost * 12}€/an"
}

output "deployment_info" {
  description = "Informations de déploiement"
  value = {
    deployed_at = formatdate("YYYY-MM-DD HH:mm:ss", timestamp())
    provider    = "Scaleway"
    region      = var.scaleway_region
    zone        = var.scaleway_zone
    location    = local.zone_names[var.scaleway_zone]
    image       = "Windows Server 2022"
    status      = "Ready for MetaTrader 5 installation"
  }
}

output "zone_options" {
  description = "Zones disponibles"
  value = {
    "fr-par-1" = "Paris 1 (France)"
    "nl-ams-1" = "Amsterdam 1 (Pays-Bas)"
    "pl-waw-1" = "Warsaw 1 (Pologne)"
  }
}

output "how_to_change_zone" {
  description = "Comment changer de zone"
  value       = <<-EOT
Pour changer de zone, modifiez terraform.tfvars :

Exemple pour Amsterdam (PAR DÉFAUT) :
────────────────────────────────────
scaleway_zone   = "nl-ams-1"
scaleway_region = "nl-ams"

Exemple pour Paris :
────────────────────
scaleway_zone   = "fr-par-1"
scaleway_region = "fr-par"

Exemple pour Warsaw :
─────────────────────
scaleway_zone   = "pl-waw-1"
scaleway_region = "pl-waw"

Puis relancer :
───────────────
terraform plan
terraform apply
  EOT
}

