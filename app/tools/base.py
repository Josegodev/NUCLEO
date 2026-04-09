class BaseTool:
    name: str
    description: str

    def run(self, payload: dict) -> dict:
        raise NotImplementedError