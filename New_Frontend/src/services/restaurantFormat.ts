export function formatPriceLevelLabel(priceLevel?: number): string {
  const level = typeof priceLevel === "number" && Number.isFinite(priceLevel) ? Math.round(priceLevel) : 2;
  if (level <= 1) return "Bình dân";
  if (level === 2) return "Trung cấp";
  return "Cao cấp";
}

