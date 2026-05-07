import sys

from gym_assistant import run


if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) > 1 else 0
    run(source)
