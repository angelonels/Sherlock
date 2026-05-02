from app.services.chart_service import ChartService


def test_chart_rules_cover_top_output_types_and_caps() -> None:
    service = ChartService(max_chart_rows=2)

    assert service.recommend([{"total": 123}], title="Total").type == "kpi"
    assert service.recommend([{"month": "2026-01", "revenue": 10}, {"month": "2026-02", "revenue": 20}]).type == "line"
    assert service.recommend([{"category": "A", "revenue": 10}, {"category": "B", "revenue": 20}]).type == "bar"
    assert service.recommend([{"product": "Very Long Product Label", "revenue": 10}, {"product": "Another Very Long Product", "revenue": 20}]).type == "horizontal_bar"
    assert service.recommend([{"date": "2026-01-01", "volume": 10}, {"date": "2026-01-02", "volume": 20}]).type == "area"
    assert service.recommend([{"region": "West", "segment": "A", "revenue": 10}, {"region": "West", "segment": "B", "revenue": 20}]).type == "stacked_bar"
    assert service.pie_or_donut([{"region": "West", "share": 60}, {"region": "East", "share": 40}], donut=False).type == "pie"
    assert service.pie_or_donut([{"region": "West", "share": 60}, {"region": "East", "share": 40}]).type == "donut"
    assert service.recommend([{"x": 1, "y": 2}, {"x": 3, "y": 4}]).type == "scatter"
    histogram = service.recommend([{"revenue": 1}, {"revenue": 2}, {"revenue": 3}])
    assert histogram.type == "histogram"
    assert len(histogram.data) == 10

    capped = service.recommend([{"category": "A", "revenue": 1}, {"category": "B", "revenue": 2}, {"category": "C", "revenue": 3}])
    assert len(capped.data) == 2
