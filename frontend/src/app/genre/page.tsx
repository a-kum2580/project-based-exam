"use client";

import GenreGrid from "@/components/GenreGrid";
import { Clapperboard } from "lucide-react";

export default function GenresPage() {
  return (
    <div className="pt-24 pb-20 px-6 md:px-12 lg:px-20 max-w-[1400px] mx-auto">
      <div className="flex items-center gap-3 mb-8">
        <Clapperboard className="w-6 h-6 text-gold" />
        <h1 className="text-3xl font-bold font-display">Browse by Genre</h1>
      </div>
      <p className="text-white/50 mb-10 max-w-xl">
        Explore movies by genre. Find your next favorite film from action blockbusters
        to indie dramas and everything in between.
      </p>
      <GenreGrid />
    </div>
  );
}
