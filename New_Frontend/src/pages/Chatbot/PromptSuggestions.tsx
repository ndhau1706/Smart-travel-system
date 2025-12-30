import { Card } from "../../components/ui/card";
import { UtensilsCrossed, MapPin, Sparkles, Coffee } from "lucide-react";

interface PromptSuggestionsProps {
  onSelectPrompt: (prompt: string) => void;
}

const suggestions = [
  {
    icon: UtensilsCrossed,
    title: "Món ăn",
    prompt: "Gợi ý cho mình quán phở ngon ở Quận 1, giá trung cấp.",
  },
  {
    icon: MapPin,
    title: "Khu vực",
    prompt: "Có quán ăn ngon gần Thủ Đức không?",
  },
  {
    icon: Sparkles,
    title: "Street food",
    prompt: "Hôm nay mình nên thử món street food nào?",
  },
  {
    icon: Coffee,
    title: "Cà phê",
    prompt: "Gợi ý quán cafe yên tĩnh, giá bình dân.",
  },
];

export function PromptSuggestions({ onSelectPrompt }: PromptSuggestionsProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-2xl">
      {suggestions.map((suggestion, index) => {
        const Icon = suggestion.icon;
        return (
          <Card
            key={index}
            className="cursor-pointer rounded-xl border bg-card p-4 shadow-sm hover:shadow-md transition-shadow"
            onClick={() => onSelectPrompt(suggestion.prompt)}
          >
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <Icon className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-muted-foreground">{suggestion.title}</p>
                <p className="text-sm text-foreground">{suggestion.prompt}</p>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
