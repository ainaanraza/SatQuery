from satquery.tools.change_summary import ChangeSummaryTool


def test_change_summary_uses_actual_change_percentage():
    tool = ChangeSummaryTool()

    result = tool.execute(
        context=None,
        arguments={
            "statistics": {
                "change_percentage": 25.0
            }
        }
    )

    assert result.success is True
    assert "25.0%" in result.data["summary"]
    assert "15.0%" not in result.data["summary"]