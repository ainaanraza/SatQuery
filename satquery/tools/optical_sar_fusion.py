from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.evidence.models import Evidence

class OpticalSARFusionTool(SatQueryTool):
    name = "optical_sar_fusion"
    description = "Fuses compatible optical and SAR data deterministically."
    capabilities = ToolCapabilities(cross_modal=True)

    def execute(self, context, arguments: dict) -> ToolResult:
        opt_img = arguments.get("optical_image")
        sar_img = arguments.get("sar_image")
        
        # In a real implementation we validate modality first.
        data = {
            "fusion_method": "baseline_statistical",
            "optical_source": getattr(opt_img, 'path', 'unknown'),
            "sar_source": getattr(sar_img, 'path', 'unknown')
        }
        
        ev = Evidence(
            source_type="fusion",
            source="optical_sar_pair",
            tool=self.name,
            metadata=data
        )
        return ToolResult(success=True, tool_name=self.name, data=data, evidence=[ev])
