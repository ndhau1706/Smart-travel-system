import { Star, MapPin, Clock, DollarSign } from "lucide-react";
import { Card } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { ImageWithFallback } from "../../components/figma/ImageWithFallback";
import { Button } from "../../components/ui/button";
import { formatPriceLevelLabel } from "../../services/restaurantFormat";

interface RestaurantCardProps {
  id: string;
  name: string;
  image: string;
  cuisine: string;
  rating: number;
  reviewCount: number;
  priceLevel: number;
  distance: string;
  openTime: string;
  specialty: string[];
  googleMapsUrl?: string;
  onClick: () => void;
}

export function RestaurantCard({
  name,
  image,
  cuisine,
  rating,
  reviewCount,
  priceLevel,
  distance,
  openTime,
  specialty,
  googleMapsUrl,
  onClick,
}: RestaurantCardProps) {
  return (
    <Card
      onClick={onClick}
      className="group relative cursor-pointer overflow-hidden rounded-xl border bg-card shadow-sm hover:shadow-md transition-shadow"
    >
      <div className="relative h-48 overflow-hidden">
        <ImageWithFallback
          src={image}
          alt={name}
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
          loading="lazy"
          decoding="async"
        />
        <div className="absolute top-3 right-3 flex items-center gap-1 rounded-full border bg-background/90 px-3 py-1 text-sm shadow-sm backdrop-blur">
          <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
          <span className="text-foreground">{rating}</span>
          <span className="text-muted-foreground">({reviewCount})</span>
        </div>
      </div>

      <div className={`p-5 space-y-4 ${googleMapsUrl ? "pb-16" : ""}`}>
        <div className="space-y-1">
          <h3 className="font-semibold leading-tight group-hover:text-primary transition-colors">{name}</h3>
          <p className="text-sm text-muted-foreground">{cuisine}</p>
        </div>
        
        <div className="flex flex-wrap gap-2">
          {specialty.slice(0, 3).map((item, idx) => (
            <Badge
              key={idx}
              variant="secondary"
              className="rounded-full"
            >
              {item}
            </Badge>
          ))}
        </div>

        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-sm text-muted-foreground">
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 flex items-center justify-center flex-shrink-0">
              <DollarSign className="h-4 w-4" />
            </div>
            <span>{formatPriceLevelLabel(priceLevel)}</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 flex items-center justify-center flex-shrink-0">
              <MapPin className="h-4 w-4" />
            </div>
            <span>{distance}</span>
          </div>
          <div className="flex items-center gap-1">
            <div className="w-4 h-4 flex items-center justify-center flex-shrink-0">
              <Clock className="h-4 w-4" />
            </div>
            <span>{openTime}</span>
          </div>
        </div>

      </div>

      {googleMapsUrl && (
        <div
          className="absolute bottom-4 right-4 z-10"
          onClick={(e) => e.stopPropagation()}
        >
          <Button
            variant="outline"
            size="sm"
            asChild
            className="rounded-lg bg-background/90 backdrop-blur shadow-sm"
          >
            <a
              href={googleMapsUrl}
              target="_blank"
              rel="noreferrer"
              title="Mở Google Maps"
            >
              <MapPin className="h-4 w-4" />
              Xem bản đồ
            </a>
          </Button>
        </div>
      )}
    </Card>
  );
}
