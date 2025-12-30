import { Globe, MapPin, Star, User } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Avatar, AvatarFallback } from "../../components/ui/avatar";
import { Card } from "../../components/ui/card";
import { ImageWithFallback } from "../../components/figma/ImageWithFallback";
import { formatPriceLevelLabel } from "../../services/restaurantFormat";
import { cn } from "../../components/ui/utils";

export interface ChatRecommendationRestaurant {
  id: string;
  name: string;
  cuisine?: string;
  address?: string;
  rating?: number;
  reviewCount?: number;
  priceLevel?: number;
  image?: string;
  googleMapsUrl?: string;
  website?: string;
  detailId?: string;
}

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  recommendations?: ChatRecommendationRestaurant[];
}

export function ChatMessage({ role, content, recommendations }: ChatMessageProps) {
  const isUser = role === "user";
  const navigate = useNavigate();

  return (
    <div
      className={cn(
        "flex w-full gap-3 px-4 py-3",
        isUser ? "flex-row-reverse justify-start" : "justify-start",
      )}
    >
      <Avatar className="h-9 w-9 flex-shrink-0 ring-1 ring-border">
        <AvatarFallback
          className={cn(
            "text-sm font-medium",
            isUser ? "bg-primary text-primary-foreground" : "bg-secondary text-secondary-foreground",
          )}
        >
          {isUser ? <User className="h-4 w-4" /> : <span className="text-base">AI</span>}
        </AvatarFallback>
      </Avatar>

      <div className="min-w-0 flex-1 space-y-3">
        <div
          className={cn(
            "max-w-[48rem] rounded-xl px-4 py-3 text-sm leading-relaxed shadow-sm",
            isUser ? "bg-primary text-primary-foreground ml-auto" : "bg-card border text-foreground",
          )}
        >
          <div className="whitespace-pre-wrap break-words">{content}</div>
        </div>

        {!isUser && recommendations && recommendations.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {recommendations.map((r) => {
              const rating = typeof r.rating === "number" ? r.rating : 0;
              const hasReviewCount = typeof r.reviewCount === "number";
              const reviewCount = hasReviewCount ? r.reviewCount : 0;
              const priceLevel = typeof r.priceLevel === "number" ? r.priceLevel : 2;
              const detailId = r.detailId;
              const externalUrl = r.googleMapsUrl || r.website;

              return (
                <Card
                  key={r.id}
                  className={cn(
                    "overflow-hidden rounded-xl border bg-card shadow-sm transition-shadow",
                    (detailId || externalUrl) && "cursor-pointer hover:shadow-md",
                  )}
                  onClick={() => {
                    if (detailId) {
                      navigate(`/restaurants/${detailId}`);
                    } else if (externalUrl) {
                      window.open(externalUrl, "_blank", "noopener,noreferrer");
                    }
                  }}
                >
                  <div className="flex gap-3 p-3">
                    <ImageWithFallback
                      src={r.image || ""}
                      alt={r.name}
                      className="w-16 h-16 rounded-lg object-cover flex-shrink-0 border border-border bg-background"
                    />

                    <div className="min-w-0 flex-1">
                      <div className="font-medium truncate">{r.name}</div>
                      {r.cuisine && <div className="text-xs text-muted-foreground truncate">{r.cuisine}</div>}

                      <div className="mt-1 flex items-center gap-2 text-xs text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Star className="h-3.5 w-3.5 fill-yellow-400 text-yellow-400" />
                          <span className="tabular-nums">{rating.toFixed(1)}</span>
                          {hasReviewCount && <span>({reviewCount})</span>}
                        </div>
                        <span>•</span>
                        <span className="text-highlight">{formatPriceLevelLabel(priceLevel)}</span>
                      </div>

                      {r.address && (
                        <div className="mt-2 flex items-start gap-1 text-xs text-muted-foreground">
                          <MapPin className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />
                          {r.googleMapsUrl ? (
                            <a
                              href={r.googleMapsUrl}
                              target="_blank"
                              rel="noreferrer"
                              className="underline underline-offset-4 decoration-primary/40 hover:decoration-primary hover:text-primary transition-colors line-clamp-2"
                              onClick={(e) => e.stopPropagation()}
                              title="Mở Google Maps"
                            >
                              {r.address}
                            </a>
                          ) : (
                            <span className="line-clamp-2">{r.address}</span>
                          )}
                        </div>
                      )}

                      {r.website && (
                        <div className="mt-2 flex items-start gap-1 text-xs text-muted-foreground">
                          <Globe className="h-3.5 w-3.5 mt-0.5 flex-shrink-0" />
                          <a
                            href={r.website}
                            target="_blank"
                            rel="noreferrer"
                            className="underline underline-offset-4 decoration-primary/40 hover:decoration-primary hover:text-primary transition-colors line-clamp-1"
                            onClick={(e) => e.stopPropagation()}
                            title="Mở website"
                          >
                            {r.website}
                          </a>
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
