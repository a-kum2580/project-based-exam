"use client";

import Link from "next/link";
import Image from "next/image";
import { Star, Clock, Play, Heart, Bookmark, TrendingUp, ArrowRight } from "lucide-react";
import { posterUrl, formatRuntime, ratingColor, cn, formatCurrency } from "@/lib/utils";
import type { MovieCompact } from "@/types/movie";

interface MovieCardProps {
  movie: MovieCompact;
  size?: "sm" | "md" | "lg";
  showOverview?: boolean;
  index?: number;
}

export default function MovieCard({
  movie,
  size = "md",
  showOverview = false,
  index = 0,
}: MovieCardProps) {
  const tmdbId = movie.tmdb_id || movie.id;
  const imgUrl = posterUrl(
    movie.poster_url || (movie as any).poster_path,
    size === "sm" ? "w185" : "w500"
  );

  const sizeClasses = { sm: "w-[140px]", md: "w-[175px]", lg: "w-[220px]" };
  const imgHeight = { sm: "h-[210px]", md: "h-[262px]", lg: "h-[330px]" };

  return (
    <Link
      href={`/movie/${tmdbId}`}
      className={`movie-card group flex-shrink-0 ${sizeClasses[size]}`}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      {/* Poster */}
      <div className={`relative ${imgHeight[size]} rounded-xl overflow-hidden bg-surface-2 mb-3`}>
        <Image
          src={imgUrl}
          alt={movie.title}
          fill
          className="object-cover transition-transform duration-700 group-hover:scale-110"
          sizes={size === "sm" ? "140px" : size === "md" ? "175px" : "220px"}
          unoptimized
        />

        {/* Shine overlay */}
        <div className="movie-card-shine" />

        {/* Hover overlay */}
        <div className="movie-card-overlay absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent opacity-0 flex flex-col items-center justify-end pb-4 transition-opacity duration-400">
          <div className="w-11 h-11 rounded-full bg-gold/90 flex items-center justify-center mb-2 shadow-lg shadow-gold/30 transition-transform group-hover:scale-110">
            <Play className="w-4 h-4 text-surface-0 ml-0.5" fill="currentColor" />
          </div>
          <span className="text-[11px] text-white/70 font-medium">View Details</span>
        </div>

        {/* Rating badge */}
        {movie.vote_average > 0 && (
          <div className="absolute top-2 right-2 flex items-center gap-1 px-2 py-0.5 rounded-md bg-black/60 backdrop-blur-md border border-white/5">
            <Star className="w-3 h-3 text-gold fill-gold" />
            <span className={`text-[11px] font-bold ${ratingColor(movie.vote_average)}`}>
              {movie.vote_average.toFixed(1)}
            </span>
          </div>
        )}

        {/* Bottom gradient (always visible, subtle) */}
        <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-surface-0/50 to-transparent pointer-events-none" />
      </div>

      {/* Info */}
      <div className="space-y-1 px-0.5">
        <h3 className="text-[13px] font-semibold line-clamp-2 text-white/90 group-hover:text-gold transition-colors duration-300 leading-snug">
          {movie.title}
        </h3>
        <div className="flex items-center gap-2 text-[11px] text-white/30">
          {movie.year && <span>{movie.year}</span>}
          {movie.runtime && movie.runtime > 0 && (
            <>
              <span className="text-white/10">•</span>
              <span className="flex items-center gap-0.5">
                <Clock className="w-3 h-3" />
                {formatRuntime(movie.runtime)}
              </span>
            </>
          )}
        </div>
        {showOverview && movie.overview && (
          <p className="text-[11px] text-white/25 line-clamp-2 mt-1 leading-relaxed">
            {movie.overview}
          </p>
        )}
      </div>
    </Link>
  );
}

// Skeleton 
export function MovieCardSkeleton({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sizeClasses = { sm: "w-[140px]", md: "w-[175px]", lg: "w-[220px]" };
  const imgHeight = { sm: "h-[210px]", md: "h-[262px]", lg: "h-[330px]" };

  return (
    <div className={`flex-shrink-0 ${sizeClasses[size]}`}>
      <div className={`${imgHeight[size]} skeleton rounded-xl mb-3`} />
      <div className="skeleton h-4 w-3/4 rounded mb-2" />
      <div className="skeleton h-3 w-1/2 rounded" />
    </div>
  );
}
