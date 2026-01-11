from agf.task_manager.utils import generate_short_id


def test_generate_short_id_correct_length():
    """Test that generate_short_id produces IDs of correct length"""
    id_6 = generate_short_id(6)
    assert len(id_6) == 6

    id_10 = generate_short_id(10)
    assert len(id_10) == 10


def test_generate_short_id_randomness():
    """Test that multiple calls produce different IDs"""
    ids = [generate_short_id(6) for _ in range(10)]
    # All IDs should be unique
    assert len(set(ids)) == 10


def test_generate_short_id_valid_alphabet():
    """Test that all characters are from the valid alphabet"""
    alphabet = "abcdefghjklmnpqrstuwxyz"
    id_str = generate_short_id(100)  # Test with a longer ID

    for char in id_str:
        assert char in alphabet


def test_generate_short_id_lowercase():
    """Test that all characters are lowercase"""
    id_str = generate_short_id(20)
    assert id_str.islower()
