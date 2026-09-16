
from .base import SatQueryTool, ToolCapabilities, ToolResult
from satquery.evidence.models import Evidence
from satquery.temporal.tracking import track_regions
from satquery.temporal.events import create_change_event
from satquery.temporal.aggregation import TemporalAggregation


class TemporalValidationTool(SatQueryTool):
    name = "temporal_validation"
    description = "Tracks changed regions and summarizes temporal change events."
    capabilities = ToolCapabilities(temporal=True, metadata=True)

    def execute(self, context, arguments: dict) -> ToolResult:
        t1_mask = arguments.get("t1_mask")
        t2_mask = arguments.get("t2_mask")

        if t1_mask is None or t2_mask is None:
            return ToolResult(
                success=False,
                tool_name=self.name,
                errors=["T1 and T2 masks are required"]
            )

        try:
            tracks = track_regions(
                t1_mask,
                t2_mask,
                threshold_iou=arguments.get("threshold_iou", 0.5),
                t1_timestamp=arguments.get("t1_timestamp"),
                t2_timestamp=arguments.get("t2_timestamp"),
            )

            events = [
                create_change_event(track)
                for track in tracks
            ]

            event_measurements = [
                measurement
                for event in events
                for measurement in event.measurements
            ]

            aggregation = TemporalAggregation(event_measurements)
            summary = aggregation.summary()

            state_counts = {}
            for event in events:
                state_counts[event.state] = (
                    state_counts.get(event.state, 0) + 1
                )

            data = {
                "track_count": len(tracks),
                "event_count": len(events),
                "state_counts": state_counts,
                "events": [
                    {
                        "event_id": event.event_id,
                        "track_id": event.track_id,
                        "start_time": event.start_time,
                        "end_time": event.end_time,
                        "state": event.state,
                        "measurements": event.measurements,
                    }
                    for event in events
                ],
                "aggregation": summary,
            }

            evidence = Evidence(
                source_type="temporal_analysis",
                source="T1/T2 temporal masks",
                tool=self.name,
                metadata={
                    "track_count": len(tracks),
                    "event_count": len(events),
                    "state_counts": state_counts,
                    "aggregation": summary,
                },
            )

            return ToolResult(
                success=True,
                tool_name=self.name,
                data=data,
                evidence=[evidence],
            )

        except Exception as exc:
            return ToolResult(
                success=False,
                tool_name=self.name,
                errors=[str(exc)],
            )
