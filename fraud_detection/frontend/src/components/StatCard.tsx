/**
 * Modern statistics card with glass-morphism and animated counters
 */
import { ReactNode } from 'react';

export interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  variant?: 'default' | 'success' | 'warning' | 'danger';
}

const variantStyles = {
  default: {
    card: 'bg-card hover:bg-card/80 border-border',
    icon: 'bg-primary/10 text-primary',
    glow: 'hover:shadow-primary/10',
    gradient: 'from-primary/5 to-transparent',
  },
  success: {
    card: 'bg-card hover:bg-card/80 border-success/20',
    icon: 'bg-success/10 text-success',
    glow: 'hover:shadow-success/20',
    gradient: 'from-success/5 to-transparent',
  },
  warning: {
    card: 'bg-card hover:bg-card/80 border-warning/20',
    icon: 'bg-warning/10 text-warning',
    glow: 'hover:shadow-warning/20',
    gradient: 'from-warning/5 to-transparent',
  },
  danger: {
    card: 'bg-card hover:bg-card/80 border-destructive/20',
    icon: 'bg-destructive/10 text-destructive',
    glow: 'hover:shadow-destructive/20',
    gradient: 'from-destructive/5 to-transparent',
  },
};

export const StatCard = ({
  title,
  value,
  subtitle,
  icon,
  trend,
  variant = 'default',
}: StatCardProps) => {
  const styles = variantStyles[variant];

  return (
    <div
      className={`group relative overflow-hidden rounded-2xl border backdrop-blur-sm shadow-lg transition-all duration-300 hover:shadow-xl ${styles.card} ${styles.glow}`}
    >
      {/* Gradient background overlay */}
      <div className={`absolute inset-0 bg-gradient-to-br ${styles.gradient} opacity-50`} />

      {/* Content */}
      <div className="relative p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex-1">
            <p className="text-xs font-bold text-muted-foreground uppercase tracking-wider mb-1">
              {title}
            </p>
          </div>
          {icon && (
            <div className={`p-3 rounded-xl ${styles.icon} transition-transform duration-300 group-hover:scale-110`}>
              {icon}
            </div>
          )}
        </div>

        <div className="space-y-2">
          <p className="text-4xl font-black text-card-foreground tracking-tight">
            {value}
          </p>

          {subtitle && (
            <p className="text-sm font-medium text-muted-foreground">
              {subtitle}
            </p>
          )}

          {trend && (
            <div className="flex items-center gap-2 pt-2">
              <div className={`flex items-center gap-1 px-2 py-1 rounded-lg text-xs font-bold ${
                trend.isPositive
                  ? 'bg-success/10 text-success'
                  : 'bg-destructive/10 text-destructive'
              }`}>
                <span>{trend.isPositive ? '↑' : '↓'}</span>
                <span>{Math.abs(trend.value)}%</span>
              </div>
              <span className="text-xs text-muted-foreground">vs last hour</span>
            </div>
          )}
        </div>
      </div>

      {/* Bottom accent line */}
      <div className={`h-1 bg-gradient-to-r ${styles.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-300`} />
    </div>
  );
};
