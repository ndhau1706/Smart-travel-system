import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "./ui/dialog";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Calendar } from "./ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "./ui/popover";
import { CalendarIcon, Users, Clock } from "lucide-react";
import { format } from "date-fns@4";
import { toast } from "sonner@2.0.3";

interface BookingDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  restaurantName: string;
}

export function BookingDialog({ open, onOpenChange, restaurantName }: BookingDialogProps) {
  const [date, setDate] = useState<Date>();
  const [time, setTime] = useState("");
  const [guests, setGuests] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!date || !time || !guests || !name || !phone) {
      toast.error("Vui lòng điền đầy đủ thông tin đặt bàn");
      return;
    }

    toast.success("Đặt bàn thành công! 🎉", {
      description: `Đã đặt bàn cho ${guests} người tại ${restaurantName} vào ${format(date, "dd/MM/yyyy")} lúc ${time}`,
    });

    // Reset form
    setDate(undefined);
    setTime("");
    setGuests("");
    setName("");
    setPhone("");
    onOpenChange(false);
  };

  const timeSlots = [
    "11:00", "11:30", "12:00", "12:30", "13:00", "13:30",
    "17:00", "17:30", "18:00", "18:30", "19:00", "19:30", "20:00", "20:30"
  ];

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent 
        className="sm:max-w-md bg-gradient-to-br from-pink-50/95 via-rose-50/95 to-fuchsia-50/95 backdrop-blur-xl border-2 border-pink-200 rounded-3xl shadow-2xl"
        style={{ boxShadow: "0 0 40px rgba(255,182,193,0.4)" }}
      >
        <DialogHeader>
          <DialogTitle className="text-pink-800">Đặt bàn tại {restaurantName}</DialogTitle>
          <DialogDescription className="text-pink-600">
            Điền thông tin để đặt bàn. Chúng tôi sẽ xác nhận trong vòng 15 phút.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          <div className="space-y-2">
            <Label htmlFor="name" className="text-gray-700">Họ và tên</Label>
            <Input
              id="name"
              placeholder="Nguyễn Văn A"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="bg-white/80 border-pink-200 focus:border-pink-400 rounded-xl"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="phone" className="text-gray-700">Số điện thoại</Label>
            <Input
              id="phone"
              type="tel"
              placeholder="0912345678"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="bg-white/80 border-pink-200 focus:border-pink-400 rounded-xl"
            />
          </div>

          <div className="space-y-2">
            <Label className="text-gray-700">Ngày đặt bàn</Label>
            <Popover>
              <PopoverTrigger asChild>
                <Button
                  variant="outline"
                  className="w-full justify-start text-left bg-white/80 border-pink-200 hover:border-pink-300 rounded-xl"
                >
                  <CalendarIcon className="mr-2 h-4 w-4 text-pink-500" />
                  {date ? format(date, "dd/MM/yyyy") : <span className="text-gray-500">Chọn ngày</span>}
                </Button>
              </PopoverTrigger>
              <PopoverContent 
                className="w-auto p-0 bg-white/95 backdrop-blur-xl border-2 border-pink-200 rounded-2xl" 
                align="start"
              >
                <Calendar
                  mode="single"
                  selected={date}
                  onSelect={setDate}
                  disabled={(date) => date < new Date()}
                  initialFocus
                />
              </PopoverContent>
            </Popover>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label className="text-gray-700">Giờ</Label>
              <Select value={time} onValueChange={setTime}>
                <SelectTrigger className="bg-white/80 border-pink-200 rounded-xl">
                  <Clock className="mr-2 h-4 w-4 text-pink-500" />
                  <SelectValue placeholder="Chọn giờ" />
                </SelectTrigger>
                <SelectContent className="bg-white/95 backdrop-blur-xl border-2 border-pink-200 rounded-2xl">
                  {timeSlots.map((slot) => (
                    <SelectItem key={slot} value={slot}>{slot}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label className="text-gray-700">Số khách</Label>
              <Select value={guests} onValueChange={setGuests}>
                <SelectTrigger className="bg-white/80 border-pink-200 rounded-xl">
                  <Users className="mr-2 h-4 w-4 text-pink-500" />
                  <SelectValue placeholder="Chọn số khách" />
                </SelectTrigger>
                <SelectContent className="bg-white/95 backdrop-blur-xl border-2 border-pink-200 rounded-2xl">
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((num) => (
                    <SelectItem key={num} value={num.toString()}>
                      {num} người
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button
            type="submit"
            className="w-full bg-gradient-to-r from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500 text-white rounded-xl shadow-lg"
            style={{ boxShadow: "0 0 20px rgba(255,182,193,0.5)" }}
          >
            Xác nhận đặt bàn
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}
