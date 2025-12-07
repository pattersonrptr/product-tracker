import random
import json
import os


class RotatingUserAgentMixin:
    _default_user_agents_file = "user-agents.json"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._user_agents = self._load_user_agents()

    def _get_user_agents_file_path(self):
        mixin_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "resources"
        )
        return os.path.join(mixin_dir, self._default_user_agents_file)

    def _load_user_agents(self):
        filepath = self._get_user_agents_file_path()

        try:
            with open(filepath, "r") as f:
                user_agents = json.load(f)
            return user_agents
        except FileNotFoundError:
            print(
                f"Warning: User-agents file '{self._default_user_agents_file}' not found at '{filepath}'. Rotating User-Agent will be disabled."
            )
            return []
        except json.JSONDecodeError:
            print(
                f"Error: Invalid JSON format in '{self._default_user_agents_file}' at '{filepath}'. Rotating User-Agent will be disabled."
            )
            return []

    def get_random_user_agent(self):
        if self._user_agents:
            return random.choice(self._user_agents)
        return None
