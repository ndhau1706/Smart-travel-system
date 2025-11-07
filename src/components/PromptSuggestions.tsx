import { Card } from "./ui/card";
import { UtensilsCrossed, MapPin, Sparkles, Coffee } from "lucide-react";

interface PromptSuggestionsProps {
  onSelectPrompt: (prompt: string) => void;
}

const suggestions = [
  {
    icon: UtensilsCrossed,
    title: "Pho",
    prompt: "Tell me about the best Pho in Vietnam!",
    gradient: "from-pink-600 via-rose-500 to-pink-600",
    emoji: "🍜",
  },
  {
    icon: MapPin,
    title: "Banh Mi",
    prompt: "Where can I find the most authentic Banh Mi?",
    gradient: "from-fuchsia-600 via-pink-500 to-fuchsia-600",
    emoji: "🥖",
  },
  {
    icon: Sparkles,
    title: "Street Food",
    prompt: "What Vietnamese street food should I try?",
    gradient: "from-rose-600 via-pink-500 to-rose-600",
    emoji: "🌶️",
  },
  {
    icon: Coffee,
    title: "Vietnamese Coffee",
    prompt: "How is Vietnamese coffee different from regular coffee?",
    gradient: "from-pink-700 via-fuchsia-600 to-pink-700",
    emoji: "☕",
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
            className="p-5 bg-gradient-to-br from-pink-100/90 via-purple-100/90 to-fuchsia-100/90 backdrop-blur-md border-2 border-pink-300 hover:border-pink-400 cursor-pointer transition-all duration-300 hover:scale-110 hover:shadow-2xl hover:rotate-1 group rounded-3xl"
            style={{ boxShadow: '0 0 25px rgba(255,182,193,0.4), inset 0 0 20px rgba(255,255,255,0.4)' }}
            onClick={() => onSelectPrompt(suggestion.prompt)}
          >
            <div className="flex items-start gap-3">
              <div 
                className={`p-3 rounded-2xl bg-gradient-to-br ${suggestion.gradient} shadow-lg group-hover:scale-125 transition-transform border-2 border-pink-200`}
                style={{ boxShadow: '0 0 20px rgba(255,182,193,0.5), inset 0 0 10px rgba(255,255,255,0.4)' }}
              >
                <span className="text-2xl drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]">{suggestion.emoji}</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-700 group-hover:text-gray-900 transition-colors">
                  {suggestion.prompt}
                </p>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
