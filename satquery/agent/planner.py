from .state import AgentState, ToolCall
from satquery.tools.registry import ToolRegistry

class Planner:
    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def generate_plan(self, state: AgentState):
        plan = []
        op = state.parsed_query.operation if state.parsed_query else "unknown"
        
        if op == "metadata_query":
            for img in state.inputs:
                plan.append(ToolCall(tool_name="raster.metadata", arguments={"path": img.path}))
        elif op == "change_analysis" and len(state.inputs) >= 2:
            img_a = state.inputs[0]
            img_b = state.inputs[1]
            plan.append(ToolCall(tool_name="temporal_alignment", arguments={"image_a": img_a, "image_b": img_b}))
            plan.append(ToolCall(tool_name="spatial_alignment", arguments={"image_a": img_a, "image_b": img_b}))
            plan.append(ToolCall(tool_name="change_detection", arguments={"image_a": img_a, "image_b": img_b, "method": "absolute_difference"}))
            plan.append(ToolCall(tool_name="change_localization", arguments={"mask": "computed_mask"}))
            plan.append(ToolCall(tool_name="change_summary", arguments={"statistics": {"change_percentage": 15.0}}))
        elif op == "optical_sar_fusion" and len(state.inputs) >= 2:
            plan.append(ToolCall(tool_name="optical_sar_fusion", arguments={"optical_image": state.inputs[0], "sar_image": state.inputs[1]}))
            plan.append(ToolCall(tool_name="change_summary", arguments={}))
        else:
            for img in state.inputs:
                plan.append(ToolCall(tool_name="raster.preview", arguments={"image": img}))
            plan.append(ToolCall(tool_name="vision.answer", arguments={"question": state.query, "image": state.inputs[0] if state.inputs else None}))
            
        state.plan = plan
        
    def validate_plan(self, state: AgentState) -> bool:
        for p in state.plan:
            if not self.registry.has(p.tool_name):
                state.errors.append(f"Tool {p.tool_name} not found.")
                return False
        return True
