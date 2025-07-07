"""
Response helper utilities for API route transformations.
"""
from typing import List, Union, Dict
from src.models.core_models import Ticket


def create_tickets_from_changes(changes: List[Union[str, Dict[str, str]]]) -> List[Ticket]:
    """
    Helper function to create tickets from a list of changes.
    
    Args:
        changes: List of change descriptions (strings) or dictionaries with 'title' and 'description' keys
        
    Returns:
        List of Ticket objects with title and description
    """
    tickets = []
    for change in changes:
        if isinstance(change, dict):
            tickets.append(Ticket(
                title=change["title"],
                description=change["description"],
                technical_details=None,
                acceptance_criteria=None,
                cursor_prompt=None
            ))
    return tickets 