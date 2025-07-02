"""
Response helper utilities for API route transformations.
"""
from typing import List
from src.models.core_models import Ticket


def create_tickets_from_changes(changes: List[str]) -> List[Ticket]:
    """
    Helper function to create tickets from a list of changes.
    
    Args:
        changes: List of change descriptions
        
    Returns:
        List of Ticket objects with title and description
    """
    tickets = []
    for change in changes:
        tickets.append(Ticket(
            title=change[:50] + "..." if len(change) > 50 else change,
            description=change,
            technical_details=None,
            acceptance_criteria=None,
            cursor_prompt=None
        ))
    return tickets 