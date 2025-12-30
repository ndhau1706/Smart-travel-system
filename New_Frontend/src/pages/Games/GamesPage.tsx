import { useState } from "react";
import { ScrollArea } from "../../components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { Card } from "../../components/ui/card";
import { Gamepad2, Bird, Blocks, Grid2X2 } from "lucide-react";
import { FlappyBirdGame } from "./FlappyBirdGame";
import { TetrisGame } from "./TetrisGame";
import { CaroGame } from "./CaroGame";

export function GamesPage() {
  const [tab, setTab] = useState("caro");

  return (
    <div className="min-h-dvh">
      <ScrollArea className="h-dvh">
        <div className="max-w-7xl mx-auto p-4 md:p-8 space-y-8 pb-24">
          <div className="text-center space-y-3 pt-6">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
              <Gamepad2 className="h-7 w-7" />
            </div>
            <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight">Trò chơi</h1>
            <p className="text-muted-foreground text-base sm:text-lg max-w-3xl mx-auto">
              Giải trí nhẹ nhàng ngay trong Smart Travel: Cờ caro, Flappy Bird và Tetris.
            </p>
          </div>

          <Card className="rounded-xl border bg-card p-4 shadow-sm">
            <Tabs value={tab} onValueChange={setTab} className="w-full">
              <TabsList className="w-full flex-wrap justify-start h-auto">
                <TabsTrigger value="caro" className="gap-2 px-3">
                  <Grid2X2 className="h-4 w-4" />
                  Cờ caro
                </TabsTrigger>
                <TabsTrigger value="flappy" className="gap-2 px-3">
                  <Bird className="h-4 w-4" />
                  Flappy Bird
                </TabsTrigger>
                <TabsTrigger value="tetris" className="gap-2 px-3">
                  <Blocks className="h-4 w-4" />
                  Tetris
                </TabsTrigger>
              </TabsList>

              <TabsContent value="caro" className="mt-4">
                <CaroGame />
              </TabsContent>
              <TabsContent value="flappy" className="mt-4">
                <FlappyBirdGame />
              </TabsContent>
              <TabsContent value="tetris" className="mt-4">
                <TetrisGame />
              </TabsContent>
            </Tabs>
          </Card>
        </div>
      </ScrollArea>
    </div>
  );
}
