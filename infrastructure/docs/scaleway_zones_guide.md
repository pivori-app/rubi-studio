# 🌍 Guide Complet : Zones Scaleway pour Windows Server 2022 + MT5

**Date :** 23 Octobre 2025  
**Auteur :** Expert Architecte Senior Backend

---

## 🗺️ Zones Disponibles sur Scaleway

### 1️⃣ Amsterdam 1 (nl-ams-1) ✅ RECOMMANDÉ

**Localisation :** Pays-Bas 🇳🇱

**Avantages :**
- ✅ Latence faible vers l'Europe
- ✅ Infrastructure moderne
- ✅ Coûts compétitifs
- ✅ Bande passante illimitée
- ✅ Meilleure performance pour trading

**Inconvénients :**
- ❌ Légèrement plus loin de la France

**Coût :** 20€/mois (VC1M)

**Latence estimée :**
- Paris → Amsterdam : ~5ms
- Londres → Amsterdam : ~10ms
- New York → Amsterdam : ~100ms

---

### 2️⃣ Paris 1 (fr-par-1)

**Localisation :** France 🇫🇷

**Avantages :**
- ✅ Latence très faible depuis la France
- ✅ Conformité RGPD garantie
- ✅ Données en France

**Inconvénients :**
- ❌ Légèrement plus cher
- ❌ Moins de ressources disponibles

**Coût :** 20€/mois (VC1M)

**Latence estimée :**
- Paris → Paris : ~1ms
- Amsterdam → Paris : ~5ms
- New York → Paris : ~100ms

---

### 3️⃣ Warsaw 1 (pl-waw-1)

**Localisation :** Pologne 🇵🇱

**Avantages :**
- ✅ Coûts très bas
- ✅ Bonne infrastructure
- ✅ Latence acceptable

**Inconvénients :**
- ❌ Plus loin de l'Europe de l'Ouest
- ❌ Moins de support en français

**Coût :** 18€/mois (VC1M)

**Latence estimée :**
- Paris → Warsaw : ~15ms
- Amsterdam → Warsaw : ~10ms
- New York → Warsaw : ~110ms

---

## 📊 Comparaison Détaillée

| Critère | Amsterdam | Paris | Warsaw |
|:--------|:----------|:------|:-------|
| **Localisation** | Pays-Bas 🇳🇱 | France 🇫🇷 | Pologne 🇵🇱 |
| **Zone** | nl-ams-1 | fr-par-1 | pl-waw-1 |
| **Coût (VC1M)** | 20€/mois | 20€/mois | 18€/mois |
| **Latence France** | 5ms | 1ms | 15ms |
| **Latence Europe** | Excellent | Bon | Bon |
| **Latence USA** | ~100ms | ~100ms | ~110ms |
| **Infrastructure** | Moderne | Moderne | Bonne |
| **Support** | Bon | Excellent | Bon |
| **RGPD** | ✅ UE | ✅ France | ✅ UE |
| **Recommandé pour Trading** | ✅✅✅ | ✅✅ | ✅ |

---

## 🎯 Recommandation

### ✅ AMSTERDAM 1 (nl-ams-1)

**Pourquoi :**
- ✅ Meilleure latence globale en Europe
- ✅ Infrastructure la plus moderne
- ✅ Coûts compétitifs
- ✅ Idéal pour le trading (latence faible)
- ✅ Bande passante illimitée

**Cas d'usage :**
- Trading haute fréquence
- Applications sensibles à la latence
- Serveurs Europe

---

## 🔄 Comment Changer de Zone

### Méthode 1 : Terraform (RECOMMANDÉ) ✅

**Fichier :** `terraform.tfvars`

```hcl
# Amsterdam (PAR DÉFAUT)
scaleway_zone   = "nl-ams-1"
scaleway_region = "nl-ams"

# OU Paris
# scaleway_zone   = "fr-par-1"
# scaleway_region = "fr-par"

# OU Warsaw
# scaleway_zone   = "pl-waw-1"
# scaleway_region = "pl-waw"
```

**Appliquer les changements :**

```bash
# Vérifier le plan
terraform plan

# Appliquer
terraform apply
```

**Durée :** ~5 minutes

---

### Méthode 2 : Variables en Ligne de Commande

```bash
# Amsterdam
terraform apply \
  -var="scaleway_zone=nl-ams-1" \
  -var="scaleway_region=nl-ams"

# Paris
terraform apply \
  -var="scaleway_zone=fr-par-1" \
  -var="scaleway_region=fr-par"

# Warsaw
terraform apply \
  -var="scaleway_zone=pl-waw-1" \
  -var="scaleway_region=pl-waw"
```

---

### Méthode 3 : Environnement

```bash
# Amsterdam
export TF_VAR_scaleway_zone="nl-ams-1"
export TF_VAR_scaleway_region="nl-ams"
terraform apply

# Paris
export TF_VAR_scaleway_zone="fr-par-1"
export TF_VAR_scaleway_region="fr-par"
terraform apply

# Warsaw
export TF_VAR_scaleway_zone="pl-waw-1"
export TF_VAR_scaleway_region="pl-waw"
terraform apply
```

---

## 🚀 Procédure Complète : Déployer en Amsterdam

### Étape 1 : Créer terraform.tfvars

```bash
cat > terraform.tfvars << EOF
scaleway_access_key = "votre-access-key"
scaleway_secret_key = "votre-secret-key"
scaleway_project_id = "votre-project-id"

# Zone : Amsterdam 1
scaleway_zone   = "nl-ams-1"
scaleway_region = "nl-ams"

# Configuration
instance_type       = "ELEMENTS-VC1M"
root_volume_size_gb = 50
environment         = "production"
EOF
```

### Étape 2 : Initialiser

```bash
cd /home/ubuntu/scaleway_infrastructure/terraform
terraform init
```

### Étape 3 : Planifier

```bash
terraform plan
```

**Résultat attendu :**
```
Plan: 3 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + instance_id = "..."
  + instance_ip = "..."
  + location = "Amsterdam 1 (Pays-Bas)"
```

### Étape 4 : Appliquer

```bash
terraform apply
```

### Étape 5 : Récupérer les Informations

```bash
# Afficher la localisation
terraform output location

# Afficher l'IP
terraform output instance_ip

# Afficher les instructions RDP
terraform output rdp_instructions
```

**Résultat :**
```
location = "Amsterdam 1 (Pays-Bas)"
instance_ip = "51.159.xxx.xxx"
```

---

## 📊 Latence Réseau

### Test de Latence

```bash
# Tester la latence vers Amsterdam
ping -c 4 51.159.xxx.xxx

# Résultat attendu : 5-10ms depuis la France
```

### Latence par Localisation

| Origine | Amsterdam | Paris | Warsaw |
|:--------|:----------|:------|:-------|
| **France** | 5ms | 1ms | 15ms |
| **Belgique** | 2ms | 8ms | 20ms |
| **Allemagne** | 3ms | 10ms | 15ms |
| **Royaume-Uni** | 10ms | 15ms | 25ms |
| **USA** | 100ms | 100ms | 110ms |
| **Asie** | 150ms | 150ms | 160ms |

---

## 💰 Coûts Comparatifs

### VC1M (2 vCPU, 8GB RAM, 50GB SSD)

| Zone | Coût/mois | Coût/an |
|:-----|:----------|:--------|
| Amsterdam | 20€ | 240€ |
| Paris | 20€ | 240€ |
| Warsaw | 18€ | 216€ |

**Différence :** Négligeable (2€/mois max)

---

## 🔐 Considérations de Sécurité

### RGPD (Règlement Général sur la Protection des Données)

**Amsterdam (Pays-Bas) :** ✅ Conforme RGPD (UE)  
**Paris (France) :** ✅ Conforme RGPD (France)  
**Warsaw (Pologne) :** ✅ Conforme RGPD (UE)

Toutes les zones sont conformes RGPD.

---

## 🎯 Recommandations par Cas d'Usage

### Trading Haute Fréquence
→ **Amsterdam** (latence minimale)

### Application Sensible à la Latence
→ **Amsterdam** (meilleure performance)

### Conformité RGPD Stricte (France)
→ **Paris** (données en France)

### Optimisation des Coûts
→ **Warsaw** (18€/mois)

### Équilibre Optimal
→ **Amsterdam** (20€/mois, latence excellente)

---

## 📝 Configuration Terraform Complète

### Fichier : `windows_mt5_instance_amsterdam.tf`

Configuration prête à l'emploi avec :
- ✅ Amsterdam 1 par défaut
- ✅ Support de toutes les zones
- ✅ Validation des paramètres
- ✅ Outputs détaillés
- ✅ Documentation complète

**Utilisation :**

```bash
# Déployer en Amsterdam (PAR DÉFAUT)
terraform apply

# Changer de zone
terraform apply -var="scaleway_zone=fr-par-1" -var="scaleway_region=fr-par"
```

---

## 🔄 Migration entre Zones

### Sauvegarder l'État

```bash
# Sauvegarder l'état Terraform
terraform state pull > terraform.state.backup
```

### Changer de Zone

```bash
# Modifier terraform.tfvars
scaleway_zone   = "fr-par-1"
scaleway_region = "fr-par"

# Appliquer
terraform apply
```

### Restaurer si Nécessaire

```bash
# Restaurer l'état
terraform state push terraform.state.backup
```

---

## ✅ Checklist de Déploiement

- [ ] Valider la zone (Amsterdam recommandé)
- [ ] Créer terraform.tfvars
- [ ] Vérifier les credentials Scaleway
- [ ] Lancer `terraform init`
- [ ] Vérifier `terraform plan`
- [ ] Lancer `terraform apply`
- [ ] Attendre 5 minutes
- [ ] Récupérer l'IP publique
- [ ] Tester la connexion RDP
- [ ] Installer MetaTrader 5
- [ ] Configurer le connecteur

---

## 📞 Support

**Questions :**
- Quelle zone choisir ? → **Amsterdam** (recommandé)
- Puis-je changer après ? → Oui, avec Terraform
- Quel coût ? → 20€/mois (Amsterdam)
- Quelle latence ? → 5ms depuis la France

**Fichiers :**
- ✅ `windows_mt5_instance_amsterdam.tf` - Configuration Terraform
- ✅ `scaleway_zones_guide.md` - Ce guide

---

## 🚀 Prêt à Déployer ?

**Amsterdam 1 est configuré par défaut. Lancez simplement :**

```bash
terraform apply
```

**Bienvenue à Amsterdam ! 🇳🇱**

