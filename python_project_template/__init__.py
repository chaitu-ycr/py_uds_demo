"""Module for initializing the python_project_template package."""

class MyClass:
    """Class for demonstrating basic functionality."""

    def __init__(self) -> None:
        """Initializes the MyClass instance."""
        print("message from my class init.")

    def say_hello(self):
        """Prints hello and returns True."""
        print("hello!")
        return True

    def say_goodbye(self):
        """Prints goodbye and returns False."""
        print("goodbye!")
        return False
