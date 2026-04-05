"use client";

import Link from "next/link";
import {
  Swords,
  Mountain,
  Palette,
  Laugh,
  SearchSlash,
  FileVideo,
  Drama,
  Wand2,
  Ghost,
  Heart,
  Rocket,
  AlertTriangle,
  Music,
  History,
  Bomb,
  Users,
} from "lucide-react";

const GENRES = [
  { id: 28, name: "Action", slug: "action", icon: Swords, gradient: "from-red-500/10 to-orange-500/10", iconColor: "text-red-400" },
  { id: 12, name: "Adventure", slug: "adventure", icon: Mountain, gradient: "from-emerald-500/10 to-teal-500/10", iconColor: "text-emerald-400" },
  { id: 16, name: "Animation", slug: "animation", icon: Palette, gradient: "from-violet-500/10 to-pink-500/10", iconColor: "text-violet-400" },
  { id: 35, name: "Comedy", slug: "comedy", icon: Laugh, gradient: "from-yellow-500/10 to-amber-500/10", iconColor: "text-yellow-400" },
  { id: 80, name: "Crime", slug: "crime", icon: SearchSlash, gradient: "from-slate-400/10 to-zinc-500/10", iconColor: "text-slate-400" },
  { id: 99, name: "Documentary", slug: "documentary", icon: FileVideo, gradient: "from-sky-500/10 to-cyan-500/10", iconColor: "text-sky-400" },
  { id: 18, name: "Drama", slug: "drama", icon: Drama, gradient: "from-indigo-500/10 to-blue-500/10", iconColor: "text-indigo-400" },
  { id: 14, name: "Fantasy", slug: "fantasy", icon: Wand2, gradient: "from-fuchsia-500/10 to-purple-500/10", iconColor: "text-fuchsia-400" },
  { id: 27, name: "Horror", slug: "horror", icon: Ghost, gradient: "from-neutral-500/10 to-red-900/10", iconColor: "text-neutral-400" },
  { id: 10749, name: "Romance", slug: "romance", icon: Heart, gradient: "from-rose-500/10 to-pink-500/10", iconColor: "text-rose-400" },
  { id: 878, name: "Sci-Fi", slug: "science-fiction", icon: Rocket, gradient: "from-cyan-500/10 to-blue-500/10", iconColor: "text-cyan-400" },
  { id: 53, name: "Thriller", slug: "thriller", icon: AlertTriangle, gradient: "from-amber-500/10 to-red-500/10", iconColor: "text-amber-400" },
  { id: 10402, name: "Music", slug: "music", icon: Music, gradient: "from-pink-500/10 to-orange-500/10", iconColor: "text-pink-400" },
  { id: 36, name: "History", slug: "history", icon: History, gradient: "from-amber-600/10 to-yellow-600/10", iconColor: "text-amber-300" },
  { id: 10752, name: "War", slug: "war", icon: Bomb, gradient: "from-stone-500/10 to-neutral-600/10", iconColor: "text-stone-400" },
  { id: 10751, name: "Family", slug: "family", icon: Users, gradient: "from-green-500/10 to-lime-500/10", iconColor: "text-green-400" },
];

export default function GenreGrid() {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-8 gap-3">
      {GENRES.map((genre, i) => {
        const Icon = genre.icon;
        return (
          <Link
            key={genre.id}
            href={`/genre/${genre.slug}?id=${genre.id}`}
            className={`genre-card glass-card group relative overflow-hidden rounded-xl p-4 flex flex-col items-center text-center gap-3 animate-slide-up stagger-${Math.min(i % 6 + 1, 6)}`}
          >
            <div className={`absolute inset-0 bg-gradient-to-br ${genre.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`} />

            <div className="relative z-10">
              <div className={`w-10 h-10 rounded-xl bg-white/[0.04] border border-white/[0.06] flex items-center justify-center group-hover:border-transparent transition-all duration-300`}>
                <Icon className={`genre-icon w-5 h-5 text-white/40 group-hover:${genre.iconColor} transition-all duration-300`} />
              </div>
            </div>

            <span className="relative z-10 text-xs font-semibold text-white/60 group-hover:text-white transition-colors duration-300">
              {genre.name}
            </span>

            <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
          </Link>
        );
      })}
    </div>
  );
}
