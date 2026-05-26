"use client";

import type { ChartSpec } from "@/lib/types";
import { ChartContainer, ChartTooltip } from "@/components/ui/chart";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  Scatter,
  ScatterChart,
  XAxis,
  YAxis,
} from "recharts";

const COLORS = ["#9d5728", "#4f6f52", "#7b5e7b", "#547088", "#b07a3c", "#6f6258"];

export function ChartRenderer({ spec }: { spec: ChartSpec }) {
  if (!spec || !Array.isArray(spec.data)) {
    return <ChartFallback />;
  }
  if (spec.type === "kpi") {
    return <KpiChartBlock spec={spec} />;
  }
  if (!spec.x_key && spec.type !== "pie" && spec.type !== "donut") {
    return <ChartFallback />;
  }
  if (spec.type === "line") return <LineChartBlock spec={spec} />;
  if (spec.type === "bar") return <BarChartBlock spec={spec} />;
  if (spec.type === "horizontal_bar") return <HorizontalBarChartBlock spec={spec} />;
  if (spec.type === "stacked_bar") return <StackedBarChartBlock spec={spec} />;
  if (spec.type === "area") return <AreaChartBlock spec={spec} />;
  if (spec.type === "pie") return <PieChartBlock spec={spec} />;
  if (spec.type === "donut") return <DonutChartBlock spec={spec} />;
  if (spec.type === "scatter") return <ScatterChartBlock spec={spec} />;
  if (spec.type === "histogram") return <HistogramChartBlock spec={spec} />;
  return <ChartFallback />;
}

export function KpiChartBlock({ spec }: { spec: ChartSpec }) {
  const key = spec.value_key ?? Object.keys(spec.data[0] ?? {})[0];
  return <div className="border border-[#d9cdbf] bg-[#fbf7f1] p-4"><p className="text-xs uppercase tracking-[0.14em] text-[#8f6a4e]">{spec.title}</p><p className="mt-2 text-3xl font-semibold">{String(spec.data[0]?.[key] ?? "")}</p></div>;
}

export function LineChartBlock({ spec }: { spec: ChartSpec }) {
  return <CartesianFrame title={spec.title}><LineChart data={spec.data}><Grid /><XAxis dataKey={spec.x_key ?? ""} /><YAxis /><ChartTooltip /><Line type="monotone" dataKey={spec.y_key ?? ""} stroke="#9d5728" strokeWidth={2} dot={false} /></LineChart></CartesianFrame>;
}

export function BarChartBlock({ spec }: { spec: ChartSpec }) {
  return <CartesianFrame title={spec.title}><BarChart data={spec.data}><Grid /><XAxis dataKey={spec.x_key ?? ""} /><YAxis /><ChartTooltip /><Bar dataKey={spec.y_key ?? ""} fill="#9d5728" /></BarChart></CartesianFrame>;
}

export function HorizontalBarChartBlock({ spec }: { spec: ChartSpec }) {
  return <CartesianFrame title={spec.title}><BarChart data={spec.data} layout="vertical"><Grid /><XAxis type="number" /><YAxis type="category" dataKey={spec.x_key ?? ""} width={120} /><ChartTooltip /><Bar dataKey={spec.y_key ?? ""} fill="#9d5728" /></BarChart></CartesianFrame>;
}

export function StackedBarChartBlock({ spec }: { spec: ChartSpec }) {
  const series = Array.from(new Set(spec.data.map((row) => String(row[spec.series_key ?? "series"] ?? "Series"))));
  const pivoted = pivot(spec, series);
  return <CartesianFrame title={spec.title}><BarChart data={pivoted}><Grid /><XAxis dataKey={spec.x_key ?? ""} /><YAxis /><ChartTooltip />{series.map((item, index) => <Bar key={item} dataKey={item} stackId="a" fill={COLORS[index % COLORS.length]} />)}</BarChart></CartesianFrame>;
}

export function AreaChartBlock({ spec }: { spec: ChartSpec }) {
  return <CartesianFrame title={spec.title}><AreaChart data={spec.data}><Grid /><XAxis dataKey={spec.x_key ?? ""} /><YAxis /><ChartTooltip /><Area type="monotone" dataKey={spec.y_key ?? ""} stroke="#4f6f52" fill="#dbe8d8" /></AreaChart></CartesianFrame>;
}

export function PieChartBlock({ spec }: { spec: ChartSpec }) {
  return <PieFrame spec={spec} innerRadius={0} />;
}

export function DonutChartBlock({ spec }: { spec: ChartSpec }) {
  return <PieFrame spec={spec} innerRadius={52} />;
}

export function ScatterChartBlock({ spec }: { spec: ChartSpec }) {
  return <CartesianFrame title={spec.title}><ScatterChart><Grid /><XAxis dataKey={spec.x_key ?? ""} name={spec.x_key ?? ""} /><YAxis dataKey={spec.y_key ?? ""} name={spec.y_key ?? ""} /><ChartTooltip cursor={{ strokeDasharray: "3 3" }} /><Scatter data={spec.data} fill="#9d5728" /></ScatterChart></CartesianFrame>;
}

export function HistogramChartBlock({ spec }: { spec: ChartSpec }) {
  return <BarChartBlock spec={spec} />;
}

function CartesianFrame({ title, children }: { title: string; children: React.ReactElement }) {
  return <div className="border border-[#d9cdbf] bg-[#fbf7f1] p-3"><p className="mb-3 text-sm font-semibold text-[#51473f]">{title}</p><ChartContainer config={{}} className="h-72 w-full">{children}</ChartContainer></div>;
}

function Grid() {
  return <CartesianGrid stroke="#e6dacd" strokeDasharray="3 3" />;
}

function PieFrame({ spec, innerRadius }: { spec: ChartSpec; innerRadius: number }) {
  const labelKey = spec.label_key ?? spec.x_key ?? "label";
  const valueKey = spec.value_key ?? spec.y_key ?? "value";
  return <div className="border border-[#d9cdbf] bg-[#fbf7f1] p-3"><p className="mb-3 text-sm font-semibold text-[#51473f]">{spec.title}</p><ChartContainer config={{}} className="h-72 w-full"><PieChart><ChartTooltip /><Pie data={spec.data} dataKey={valueKey} nameKey={labelKey} innerRadius={innerRadius}>{spec.data.map((_, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}</Pie></PieChart></ChartContainer></div>;
}

function pivot(spec: ChartSpec, series: string[]) {
  const xKey = spec.x_key ?? "x";
  const yKey = spec.y_key ?? "y";
  const seriesKey = spec.series_key ?? "series";
  const byX = new Map<string, Record<string, unknown>>();
  for (const row of spec.data) {
    const x = String(row[xKey] ?? "");
    const target = byX.get(x) ?? { [xKey]: x };
    target[String(row[seriesKey] ?? "Series")] = row[yKey] ?? 0;
    byX.set(x, target);
  }
  return Array.from(byX.values()).map((row) => {
    for (const key of series) row[key] ??= 0;
    return row;
  });
}

function ChartFallback() {
  return <div className="border border-[#d9cdbf] bg-[#fbf7f1] p-3 text-sm text-[#655c52]">Unsupported chart.</div>;
}
