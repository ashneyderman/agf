import secrets


def generate_short_id(length: int) -> str:
    """
    Generate a cryptographically random short ID.

    Args:
        length: The length of the ID to generate

    Returns:
        A random string of lowercase letters (excluding ambiguous characters)
    """
    alphabet = "abcdefghjklmnpqrstuwxyz"
    return ''.join(secrets.choice(alphabet) for _ in range(length))
