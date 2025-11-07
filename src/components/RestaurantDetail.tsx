import { useState } from "react";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { Card } from "./ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { ScrollArea } from "./ui/scroll-area";
import { BookingDialog } from "./BookingDialog";
import { ArrowLeft, Star, MapPin, Clock, Phone, DollarSign, Calendar } from "lucide-react";
import { ImageWithFallback } from "./figma/ImageWithFallback";

interface MenuItem {
  id: string;
  name: string;
  description: string;
  price: number;
  image: string;
  category: string;
}

interface Restaurant {
  id: string;
  name: string;
  image: string;
  cuisine: string;
  rating: number;
  reviewCount: number;
  priceLevel: number;
  address: string;
  phone: string;
  openTime: string;
  specialty: string[];
  description: string;
  menu: MenuItem[];
}

interface RestaurantDetailProps {
  restaurant: Restaurant;
  onBack: () => void;
}

export function RestaurantDetail({ restaurant, onBack }: RestaurantDetailProps) {
  const [bookingOpen, setBookingOpen] = useState(false);

  const categories = Array.from(new Set(restaurant.menu.map((item) => item.category)));

  return (
    <div className="min-h-screen relative">
      <ScrollArea className="h-screen">
        <div className="max-w-5xl mx-auto p-4 md:p-6 space-y-6">
          {/* Back Button */}
          <Button
            onClick={onBack}
            variant="outline"
            className="bg-white/80 backdrop-blur-lg border-2 border-pink-200 hover:border-pink-300 rounded-2xl shadow-lg"
            style={{ boxShadow: "0 0 15px rgba(255,182,193,0.3)" }}
          >
            <ArrowLeft className="mr-2 h-4 w-4" />
            Quay lại
          </Button>

          {/* Restaurant Header */}
          <Card
            className="overflow-hidden bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl shadow-xl"
            style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
          >
            <div className="relative h-64 md:h-80 overflow-hidden">
              <ImageWithFallback
                src={restaurant.image}
                alt={restaurant.name}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
              <div className="absolute bottom-6 left-6 right-6 text-white">
                <h1 className="text-white mb-2">{restaurant.name}</h1>
                <div className="flex items-center gap-4 flex-wrap">
                  <div className="flex items-center gap-1 bg-white/20 backdrop-blur-md px-3 py-1 rounded-full">
                    <Star className="h-4 w-4 fill-yellow-400 text-yellow-400" />
                    <span>{restaurant.rating}</span>
                    <span className="text-sm">({restaurant.reviewCount} đánh giá)</span>
                  </div>
                  <span className="text-sm">{restaurant.cuisine}</span>
                </div>
              </div>
            </div>

            <div className="p-6 space-y-4">
              <p className="text-gray-700">{restaurant.description}</p>

              <div className="flex flex-wrap gap-2">
                {restaurant.specialty.map((item, idx) => (
                  <Badge
                    key={idx}
                    variant="secondary"
                    className="bg-gradient-to-r from-pink-200 to-rose-200 text-pink-700 border-pink-300 rounded-full"
                  >
                    {item}
                  </Badge>
                ))}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-gray-700">
                <div className="flex items-center gap-2">
                  <MapPin className="h-5 w-5 text-pink-500" />
                  <span>{restaurant.address}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Phone className="h-5 w-5 text-pink-500" />
                  <span>{restaurant.phone}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock className="h-5 w-5 text-pink-500" />
                  <span>{restaurant.openTime}</span>
                </div>
                <div className="flex items-center gap-2">
                  <DollarSign className="h-5 w-5 text-pink-500" />
                  <span>{"$".repeat(restaurant.priceLevel)} - Giá trung bình</span>
                </div>
              </div>

              <Button
                onClick={() => setBookingOpen(true)}
                className="w-full bg-gradient-to-r from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500 text-white rounded-2xl shadow-lg py-6"
                style={{ boxShadow: "0 0 25px rgba(255,182,193,0.5)" }}
              >
                <Calendar className="mr-2 h-5 w-5" />
                Đặt bàn ngay
              </Button>
            </div>
          </Card>

          {/* Menu */}
          <Card
            className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl shadow-xl p-6"
            style={{ boxShadow: "0 0 30px rgba(255,182,193,0.4)" }}
          >
            <h2 className="text-pink-800 mb-6">Thực đơn</h2>
            <Tabs defaultValue={categories[0]} className="w-full">
              <TabsList className="bg-pink-200/50 backdrop-blur-md rounded-2xl p-1 mb-6 flex-wrap h-auto">
                {categories.map((category) => (
                  <TabsTrigger
                    key={category}
                    value={category}
                    className="data-[state=active]:bg-white data-[state=active]:text-pink-700 rounded-xl"
                  >
                    {category}
                  </TabsTrigger>
                ))}
              </TabsList>

              {categories.map((category) => (
                <TabsContent key={category} value={category} className="space-y-4">
                  {restaurant.menu
                    .filter((item) => item.category === category)
                    .map((item) => (
                      <Card
                        key={item.id}
                        className="flex gap-4 overflow-hidden bg-white/80 backdrop-blur-md border border-pink-200 rounded-2xl shadow-md hover:shadow-lg transition-shadow"
                      >
                        <ImageWithFallback
                          src={item.image}
                          alt={item.name}
                          className="w-24 h-24 object-cover rounded-l-2xl"
                        />
                        <div className="flex-1 p-4">
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="text-gray-900">{item.name}</h4>
                            <span className="text-pink-600">{item.price.toLocaleString("vi-VN")}đ</span>
                          </div>
                          <p className="text-sm text-gray-600">{item.description}</p>
                        </div>
                      </Card>
                    ))}
                </TabsContent>
              ))}
            </Tabs>
          </Card>
        </div>
      </ScrollArea>

      <BookingDialog
        open={bookingOpen}
        onOpenChange={setBookingOpen}
        restaurantName={restaurant.name}
      />
    </div>
  );
}
