import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

export function PanelHeader({
  title,
  icon: Icon,
  subtitle,
  right,
}: {
  title: string;
  icon?: LucideIcon;
  subtitle?: string;
  right?: ReactNode;
}) {
  return (
    <div className="mb-4 flex items-start justify-between gap-4">
      <div className="flex items-start gap-2.5">
        {Icon && (
          <div className="mt-0.5 flex h-7 w-7 items-center justify-center rounded-md border border-primary/30 bg-primary/10 text-primary">
            <Icon className="h-3.5 w-3.5" />
          </div>
        )}
        <div>
          <h3 className="text-sm font-semibold tracking-tight text-foreground">{title}</h3>
          {subtitle && <p className="text-xs text-muted-foreground">{subtitle}</p>}
        </div>
      </div>
      {right}
    </div>
  );
}
