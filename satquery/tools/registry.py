from .base import SatQueryTool

class ToolRegistry:
    def __init__(self):
        self._tools = {}
        
    def register(self, tool: SatQueryTool):
        self._tools[tool.name] = tool
        
    def get(self, name: str) -> SatQueryTool:
        return self._tools.get(name)
        
    def has(self, name: str) -> bool:
        return name in self._tools
        
    def list(self) -> list:
        return list(self._tools.values())
