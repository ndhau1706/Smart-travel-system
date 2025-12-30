import { Star, MapPin, Clock, DollarSign } from "lucide-react";
import { Card } from "./ui/card";
import { Badge } from "./ui/badge";
import { ImageWithFallback } from "./figma/ImageWithFallback";

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
  onClick,
}: RestaurantCardProps) {
  return (
    <Card
      onClick={onClick}
      className="group cursor-pointer overflow-hidden bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 hover:border-pink-300 transition-all duration-300 rounded-3xl shadow-lg hover:shadow-2xl"
      style={{
        boxShadow: "0 0 25px rgba(255,182,193,0.3)",
      }}
    >
      <div className="relative h-48 overflow-hidden">
        <ImageWithFallback
          src={image}
          alt={name}
          className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
        />
        <div className="absolute top-3 right-3 flex items-center gap-1 bg-white/95 backdrop-blur-sm px-3 py-1 rounded-full shadow-lg border border-pink-200">
          <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
          <span className="text-gray-800">{rating}</span>
          <span className="text-gray-500 text-sm">({reviewCount})</span>
        </div>
      </div>

      <div className="p-5 space-y-3">
        <div>
          <h3 className="text-gray-900 mb-1 group-hover:text-pink-600 transition-colors">
            {name}
          </h3>
          <p className="text-pink-600 text-sm">{cuisine}</p>
        </div>

        <div className="flex flex-wrap gap-2">
          {specialty.slice(0, 3).map((item, idx) => (
            <Badge
              key={idx}
              variant="secondary"
              className="bg-gradient-to-r from-pink-200 to-rose-200 text-pink-700 border-pink-300 rounded-full"
            >
              {item}
            </Badge>
          ))}
        </div>

        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <DollarSign className="h-4 w-4 text-pink-500" />
            <span>{"$".repeat(priceLevel)}</span>
          </div>
          <div className="flex items-center gap-1">
            <MapPin className="h-4 w-4 text-pink-500" />
            <span>{distance}</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-4 w-4 text-pink-500" />
            <span>{openTime}</span>
          </div>
        </div>
      </div>
    </Card>
  );
}
