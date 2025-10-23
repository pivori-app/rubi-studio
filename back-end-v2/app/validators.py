"""
Validators pour Rubi Studio
Validation des variables contre les schémas JSON
"""

from typing import Dict, Any
from jsonschema import validate, ValidationError, Draft7Validator
import logging

logger = logging.getLogger(__name__)


def validate_variables_against_schema(variables: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide les variables contre un schéma JSON et enrichit avec les valeurs par défaut
    
    Args:
        variables: Dictionnaire des variables fournies
        schema: Schéma JSON définissant les variables attendues
    
    Returns:
        Dictionnaire des variables validées et enrichies
    
    Raises:
        ValueError: Si la validation échoue
    """
    if not schema:
        # Pas de schéma = pas de validation
        return variables
    
    # Créer un validateur
    validator = Draft7Validator(schema)
    errors = list(validator.iter_errors(variables))
    
    if errors:
        error_messages = []
        for error in errors:
            path = ".".join(str(p) for p in error.path) if error.path else "root"
            error_messages.append(f"{path}: {error.message}")
        
        raise ValueError(
            f"Variable validation failed:\n" + "\n".join(error_messages)
        )
    
    # Enrichir avec les valeurs par défaut
    enriched = variables.copy()
    properties = schema.get("properties", {})
    
    for prop_name, prop_schema in properties.items():
        if prop_name not in enriched and "default" in prop_schema:
            enriched[prop_name] = prop_schema["default"]
            logger.info(f"Added default value for '{prop_name}': {prop_schema['default']}")
    
    return enriched


def generate_example_variables(schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Génère des exemples de variables à partir d'un schéma JSON
    
    Args:
        schema: Schéma JSON
    
    Returns:
        Dictionnaire d'exemples de variables
    """
    examples = {}
    properties = schema.get("properties", {})
    
    for prop_name, prop_schema in properties.items():
        if "example" in prop_schema:
            examples[prop_name] = prop_schema["example"]
        elif "default" in prop_schema:
            examples[prop_name] = prop_schema["default"]
        elif "enum" in prop_schema and prop_schema["enum"]:
            examples[prop_name] = prop_schema["enum"][0]
        else:
            # Générer une valeur par défaut selon le type
            prop_type = prop_schema.get("type", "string")
            if prop_type == "string":
                examples[prop_name] = f"example_{prop_name}"
            elif prop_type == "number" or prop_type == "integer":
                examples[prop_name] = 0
            elif prop_type == "boolean":
                examples[prop_name] = False
            elif prop_type == "array":
                examples[prop_name] = []
            elif prop_type == "object":
                examples[prop_name] = {}
    
    return examples


def get_required_variables(schema: Dict[str, Any]) -> list:
    """
    Obtient la liste des variables requises d'un schéma
    
    Args:
        schema: Schéma JSON
    
    Returns:
        Liste des noms de variables requises
    """
    return schema.get("required", [])


def get_variable_description(schema: Dict[str, Any], variable_name: str) -> str:
    """
    Obtient la description d'une variable depuis le schéma
    
    Args:
        schema: Schéma JSON
        variable_name: Nom de la variable
    
    Returns:
        Description de la variable ou chaîne vide
    """
    properties = schema.get("properties", {})
    if variable_name in properties:
        return properties[variable_name].get("description", "")
    return ""

