from auth import check_password

def test_wrong_password():
    # Agar password galat hai, toh False aana chahiye
    result = check_password("admin", "wrong_pass_123")
    assert result == False, "Security Flaw: Login allowed with wrong password!"