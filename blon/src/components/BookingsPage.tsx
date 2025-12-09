import { useState } from "react";
import { Card } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import { ScrollArea } from "./ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Calendar, Clock, Users, MapPin, Phone, X, CheckCircle } from "lucide-react";
import { format } from 'date-fns';
import { vi } from 'date-fns/locale/vi';
import { formatWithOptions } from 'date-fns/fp';

interface Booking {
  id: string;
  restaurantName: string;
  date: Date;
  time: string;
  guests: number;
  status: "confirmed" | "pending" | "cancelled";
  name: string;
  phone: string;
  address: string;
}

const mockBookings: Booking[] = [
  {
    id: "1",
    restaurantName: "Phở Hà Nội",
    date: new Date(2025, 10, 8, 12, 0),
    time: "12:00",
    guests: 4,
    status: "confirmed",
    name: "Nguyễn Văn A",
    phone: "0912345678",
    address: "123 Nguyễn Huệ, Quận 1, TP.HCM",
  },
  {
    id: "2",
    restaurantName: "Nhà Hàng Hải Sản Biển Xanh",
    date: new Date(2025, 10, 10, 19, 0),
    time: "19:00",
    guests: 6,
    status: "pending",
    name: "Nguyễn Văn A",
    phone: "0912345678",
    address: "789 Võ Văn Tần, Quận 3, TP.HCM",
  },
  {
    id: "3",
    restaurantName: "Bánh Mì Sài Gòn",
    date: new Date(2025, 10, 5, 8, 0),
    time: "08:00",
    guests: 2,
    status: "cancelled",
    name: "Nguyễn Văn A",
    phone: "0912345678",
    address: "45 Pasteur, Quận 1, TP.HCM",
  },
];

export function BookingsPage() {
  const [bookings, setBookings] = useState<Booking[]>(mockBookings);

  const handleCancelBooking = (id: string) => {
    setBookings((prev) =>
      prev.map((booking) =>
        booking.id === id ? { ...booking, status: "cancelled" as const } : booking
      )
    );
  };

  const upcomingBookings = bookings.filter(
    (b) => b.status !== "cancelled" && b.date >= new Date()
  );
  const pastBookings = bookings.filter(
    (b) => b.status === "cancelled" || b.date < new Date()
  );

  const getStatusBadge = (status: Booking["status"]) => {
    switch (status) {
      case "confirmed":
        return (
          <Badge className="bg-green-100 text-green-700 border-green-300 rounded-full">
            <CheckCircle className="h-3 w-3 mr-1" />
            Đã xác nhận
          </Badge>
        );
      case "pending":
        return (
          <Badge className="bg-yellow-100 text-yellow-700 border-yellow-300 rounded-full">
            <Clock className="h-3 w-3 mr-1" />
            Chờ xác nhận
          </Badge>
        );
      case "cancelled":
        return (
          <Badge className="bg-gray-100 text-gray-700 border-gray-300 rounded-full">
            <X className="h-3 w-3 mr-1" />
            Đã hủy
          </Badge>
        );
    }
  };

  const BookingCard = ({ booking }: { booking: Booking }) => (
    <Card
      className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-6 shadow-lg"
      style={{ boxShadow: "0 0 25px rgba(255,182,193,0.3)" }}
    >
      <div className="space-y-4">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-pink-800 mb-2">{booking.restaurantName}</h3>
            {getStatusBadge(booking.status)}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-gray-700">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-pink-500" />
            <span>{formatWithOptions({ locale: vi }, "dd MMMM yyyy")(booking.date)}</span>
          </div>
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-pink-500" />
            <span>{booking.time}</span>
          </div>
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-pink-500" />
            <span>{booking.guests} người</span>
          </div>
          <div className="flex items-center gap-2">
            <Phone className="h-4 w-4 text-pink-500" />
            <span>{booking.phone}</span>
          </div>
        </div>

        <div className="flex items-start gap-2 text-gray-700">
          <MapPin className="h-4 w-4 text-pink-500 mt-1" />
          <span className="text-sm">{booking.address}</span>
        </div>

        {booking.status !== "cancelled" && (
          <Button
            onClick={() => handleCancelBooking(booking.id)}
            variant="outline"
            className="w-full border-pink-300 text-pink-700 hover:bg-pink-100 rounded-xl"
          >
            <X className="h-4 w-4 mr-2" />
            Hủy đặt chỗ
          </Button>
        )}
      </div>
    </Card>
  );

  return (
    <div className="min-h-screen relative">
      <ScrollArea className="h-screen">
        <div className="max-w-5xl mx-auto p-4 md:p-6 pt-20 space-y-6">
          {/* Header */}
          <div className="text-center space-y-3">
            <h1 className="bg-gradient-to-r from-pink-600 via-rose-600 to-fuchsia-600 bg-clip-text text-transparent drop-shadow-[0_2px_8px_rgba(255,182,193,0.4)]">
              📅 Quản lý đặt chỗ
            </h1>
            <p className="text-pink-700">Xem và quản lý các đặt chỗ của bạn</p>
          </div>

          {/* Tabs */}
          <Tabs defaultValue="upcoming" className="w-full">
            <TabsList className="bg-pink-200/50 backdrop-blur-md rounded-2xl p-1 mb-6 w-full max-w-md mx-auto grid grid-cols-2">
              <TabsTrigger
                value="upcoming"
                className="data-[state=active]:bg-white data-[state=active]:text-pink-700 rounded-xl"
              >
                Sắp tới ({upcomingBookings.length})
              </TabsTrigger>
              <TabsTrigger
                value="past"
                className="data-[state=active]:bg-white data-[state=active]:text-pink-700 rounded-xl"
              >
                Lịch sử ({pastBookings.length})
              </TabsTrigger>
            </TabsList>

            <TabsContent value="upcoming" className="space-y-4">
              {upcomingBookings.length > 0 ? (
                upcomingBookings.map((booking) => (
                  <BookingCard key={booking.id} booking={booking} />
                ))
              ) : (
                <Card
                  className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-12 text-center shadow-lg"
                  style={{ boxShadow: "0 0 25px rgba(255,182,193,0.3)" }}
                >
                  <Calendar className="h-16 w-16 text-pink-300 mx-auto mb-4" />
                  <h3 className="text-pink-700 mb-2">Chưa có đặt chỗ nào</h3>
                  <p className="text-pink-600">
                    Hãy khám phá các nhà hàng và đặt bàn ngay!
                  </p>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="past" className="space-y-4">
              {pastBookings.length > 0 ? (
                pastBookings.map((booking) => (
                  <BookingCard key={booking.id} booking={booking} />
                ))
              ) : (
                <Card
                  className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-12 text-center shadow-lg"
                  style={{ boxShadow: "0 0 25px rgba(255,182,193,0.3)" }}
                >
                  <Calendar className="h-16 w-16 text-pink-300 mx-auto mb-4" />
                  <h3 className="text-pink-700 mb-2">Chưa có lịch sử</h3>
                  <p className="text-pink-600">
                    Lịch sử đặt chỗ của bạn sẽ hiển thị ở đây
                  </p>
                </Card>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </ScrollArea>
    </div>
  );
}
