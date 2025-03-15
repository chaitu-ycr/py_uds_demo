import pytest
from py_uds_demo import MyClass

def test_init(capsys):
    # Test initialization of MyClass
    my_instance = MyClass()
    captured = capsys.readouterr()
    assert "message from my class init." in captured.out

def test_say_hello(capsys):
    # Test the say_hello method
    my_instance = MyClass()
    result = my_instance.say_hello()
    captured = capsys.readouterr()
    assert "hello!" in captured.out
    assert result is True

def test_say_goodbye(capsys):
    # Test the say_goodbye method
    my_instance = MyClass()
    result = my_instance.say_goodbye()
    captured = capsys.readouterr()
    assert "goodbye!" in captured.out
    assert result is False

# This main guard allows the script to be run directly
if __name__ == "__main__":
    pytest.main()
