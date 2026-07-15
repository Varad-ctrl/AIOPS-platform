import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { MetricHistoryPoint } from "@/types";

interface HistoryChartProps {
  title: string;
  data: MetricHistoryPoint[];
  color?: string;
  unit?: string;
}

export default function HistoryChart({
  title,
  data,
  color = "#5EEAD4",
  unit = "%",
}: HistoryChartProps) {
  const formatted = data.map((point) => ({
    time: new Date(point.timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    }),
    value: point.value,
  }));

  return (
    <div className="panel p-4">
      <p className="label-eyebrow mb-3">{title}</p>
      {formatted.length === 0 ? (
        <div className="h-48 flex items-center justify-center text-sm text-ink-muted">
          No historical data yet
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={192}>
          <AreaChart data={formatted}>
            <defs>
              <linearGradient id={`grad-${title}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={color} stopOpacity={0.35} />
                <stop offset="100%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#1F2733" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="time"
              stroke="#5B6778"
              fontSize={11}
              tickLine={false}
              axisLine={false}
            />
            <YAxis stroke="#5B6778" fontSize={11} tickLine={false} axisLine={false} width={36} />
            <Tooltip
              contentStyle={{
                background: "#161C26",
                border: "1px solid #2B3542",
                borderRadius: 6,
                fontSize: 12,
              }}
              labelStyle={{ color: "#9AA7B8" }}
              formatter={(value: number) => [`${value} ${unit}`, "value"]}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              fill={`url(#grad-${title})`}
            />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </div>
  );
}
