import { Badge } from "@/components/ui/badge";
import { categoryColor } from "@/lib/categories";

export function CategoryBadge({ category }: { category: string }) {
  return (
    <Badge
      variant="outline"
      className="border-transparent text-xs font-medium"
      style={{
        backgroundColor: `color-mix(in oklch, ${categoryColor(category)} 18%, transparent)`,
        color: categoryColor(category),
      }}
    >
      {category}
    </Badge>
  );
}
