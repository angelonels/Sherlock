import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ChartRenderer } from "@/features/charts/chart-renderer";
import type { ChartSpec } from "@/lib/types";

const specs: ChartSpec[] = [
  { type: "kpi", title: "Total revenue", value_key: "total", data: [{ total: 100 }] },
  { type: "line", title: "Revenue by month", x_key: "month", y_key: "revenue", data: [{ month: "Jan", revenue: 100 }] },
  { type: "bar", title: "Revenue by category", x_key: "category", y_key: "revenue", data: [{ category: "A", revenue: 100 }] },
  { type: "horizontal_bar", title: "Top products", x_key: "product", y_key: "revenue", data: [{ product: "Long product", revenue: 100 }] },
  { type: "stacked_bar", title: "Revenue by segment", x_key: "region", y_key: "revenue", series_key: "segment", data: [{ region: "West", segment: "A", revenue: 100 }] },
  { type: "area", title: "Volume by date", x_key: "date", y_key: "volume", data: [{ date: "2026-01-01", volume: 100 }] },
  { type: "pie", title: "Share", label_key: "region", value_key: "share", data: [{ region: "West", share: 60 }] },
  { type: "donut", title: "Donut share", label_key: "region", value_key: "share", data: [{ region: "West", share: 60 }] },
  { type: "scatter", title: "Revenue vs units", x_key: "units", y_key: "revenue", data: [{ units: 2, revenue: 100 }] },
  { type: "histogram", title: "Distribution", x_key: "bin", y_key: "count", data: [{ bin: "0-10", count: 3 }] },
];

describe("ChartRenderer", () => {
  it("dispatches all 10 chart types", () => {
    render(<>{specs.map((spec) => <ChartRenderer key={spec.type} spec={spec} />)}</>);

    for (const spec of specs) {
      expect(screen.getByText(spec.title)).toBeVisible();
    }
  });

  it("renders invalid charts with a fallback", () => {
    render(<ChartRenderer spec={{ type: "unknown", title: "Broken", data: [] }} />);

    expect(screen.getByText("Unsupported chart.")).toBeVisible();
  });
});
