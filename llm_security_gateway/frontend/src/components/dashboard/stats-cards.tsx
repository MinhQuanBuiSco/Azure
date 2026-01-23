"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatNumber } from "@/lib/utils";
import {
  Activity,
  ShieldAlert,
  ShieldCheck,
  Clock,
  Zap,
} from "lucide-react";

interface StatsCardsProps {
  stats: {
    total_requests: number;
    allowed_requests: number;
    blocked_requests: number;
    filtered_requests: number;
    total_tokens: number;
    avg_response_time_ms: number;
  };
}

export function StatsCards({ stats }: StatsCardsProps) {
  const cards = [
    {
      title: "Total Requests",
      value: formatNumber(stats.total_requests),
      icon: Activity,
      color: "text-blue-600",
      bgColor: "bg-blue-100",
    },
    {
      title: "Allowed",
      value: formatNumber(stats.allowed_requests),
      icon: ShieldCheck,
      color: "text-green-600",
      bgColor: "bg-green-100",
    },
    {
      title: "Blocked",
      value: formatNumber(stats.blocked_requests),
      icon: ShieldAlert,
      color: "text-red-600",
      bgColor: "bg-red-100",
    },
    {
      title: "Tokens Used",
      value: formatNumber(stats.total_tokens),
      icon: Zap,
      color: "text-purple-600",
      bgColor: "bg-purple-100",
    },
    {
      title: "Avg Response",
      value: `${stats.avg_response_time_ms?.toFixed(0) || 0}ms`,
      icon: Clock,
      color: "text-orange-600",
      bgColor: "bg-orange-100",
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
      {cards.map((card) => (
        <Card key={card.title}>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              {card.title}
            </CardTitle>
            <div className={`rounded-full p-2 ${card.bgColor}`}>
              <card.icon className={`h-4 w-4 ${card.color}`} />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{card.value}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
