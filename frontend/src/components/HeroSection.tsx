"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import Image from "next/image";
import { Play, Info, Star, ChevronLeft, ChevronRight } from "lucide-react";
import { backdropUrl, posterUrl } from "@/lib/utils";
import type { MovieCompact } from "@/types/movie";

interface HeroSectionProps {
  movies: MovieCompact[];
}

const SLIDE_DURATION = 3000; 

export default function HeroSection({ movies }: HeroSectionProps) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [progressKey, setProgressKey] = useState(0);

  const heroMovies = movies.slice(0, 6);

  const goTo = useCallback(
    (index: number) => {
      setActiveIndex(index);
      setProgressKey((k) => k + 1);
    },
    []
  );

  const goNext = useCallback(() => {
    goTo((activeIndex + 1) % heroMovies.length);
  }, [activeIndex, heroMovies.length, goTo]);

  const goPrev = useCallback(() => {
    goTo((activeIndex - 1 + heroMovies.length) % heroMovies.length);
  }, [activeIndex, heroMovies.length, goTo]);

  // Auto-advance
  useEffect(() => {
    if (isPaused || heroMovies.length <= 1) return;
    const timer = setInterval(goNext, SLIDE_DURATION);
    return () => clearInterval(timer);
  }, [goNext, isPaused, heroMovies.length]);

  if (!heroMovies.length) {
    return (
      <div className="h-[90vh] flex items-center justify-center relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-surface-1 to-surface-0" />
        <div className="relative text-center space-y-5 animate-slide-up">
          <h1 className="text-6xl md:text-8xl font-bold font-display">
            Cine<span className="text-gold">Quest</span>
          </h1>
          <p className="text-white/35 text-lg font-body max-w-md mx-auto">
            Your cinematic discovery engine
          </p>
        </div>
      </div>
    );
  }

  const movie = heroMovies[activeIndex];
  const bgUrl = backdropUrl((movie as any).backdrop_url || movie.poster_url);

  return (
    <div
      className="relative h-[92vh] overflow-hidden"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      {heroMovies.map((m, i) => {
        const bg = backdropUrl((m as any).backdrop_url || m.poster_url);
        return (
          <div
            key={m.id || m.tmdb_id}
            className="absolute inset-0 transition-opacity duration-[1200ms] ease-in-out"
            style={{ opacity: i === activeIndex ? 1 : 0 }}
          >
            {bg && (
              <Image
                src={bg}
                alt={m.title}
                fill
                className="object-cover object-top"
                priority={i === 0}
                unoptimized
              />
            )}
          </div>
        );
      })}

      {/* Gradient overlays */}
      <div className="hero-gradient absolute inset-0" />
      <div className="hero-side-gradient absolute inset-0" />

      <div className="absolute bottom-0 left-0 right-0 px-6 md:px-10 lg:px-20 pb-36 z-10">
        <div key={activeIndex} className="max-w-2xl animate-slide-up">
          {/* Top line */}
          <div className="flex items-center gap-3 mb-4">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gold/10 border border-gold/20 text-[11px] font-semibold uppercase tracking-widest text-gold">
              <span className="w-1.5 h-1.5 rounded-full bg-gold animate-pulse" />
              Trending Now
            </span>
            {movie.vote_average > 0 && (
              <span className="flex items-center gap-1 text-sm">
                <Star className="w-4 h-4 text-gold fill-gold" />
                <span className="font-semibold text-gold">{movie.vote_average.toFixed(1)}</span>
              </span>
            )}
            {movie.year && (
              <span className="text-sm text-white/30">{movie.year}</span>
            )}
          </div>

          {/* Title */}
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold font-display leading-[1.05] mb-5 text-white drop-shadow-2xl">
            {movie.title}
          </h1>

          {/* Overview */}
          <p className="text-base md:text-lg text-white/50 line-clamp-2 mb-6 max-w-xl leading-relaxed">
            {movie.overview}
          </p>

          {/* Genres */}
          {movie.genres && movie.genres.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-7">
              {movie.genres.slice(0, 4).map((g: any) => (
                <span
                  key={g.id || g.tmdb_id || g.name}
                  className="px-3 py-1 rounded-full bg-white/[0.06] border border-white/[0.08] text-[11px] font-medium text-white/60 uppercase tracking-wider"
                >
                  {g.name}
                </span>
              ))}
            </div>
          )}

          {/* CTA buttons */}
          <div className="flex items-center gap-3">
            <Link
              href={`/movie/${movie.tmdb_id || movie.id}`}
              className="group flex items-center gap-2.5 px-7 py-3.5 rounded-xl bg-gradient-to-r from-gold to-gold-dim text-surface-0 font-semibold text-sm transition-all duration-300 hover:shadow-lg hover:shadow-gold/20 hover:scale-[1.03] active:scale-[0.98]"
            >
              <Info className="w-[18px] h-[18px]" />
              View Details
            </Link>
            <Link
              href={`/movie/${movie.tmdb_id || movie.id}`}
              className="flex items-center gap-2 px-6 py-3.5 rounded-xl glass-card text-sm font-medium text-white/80 hover:text-white transition-all duration-300 hover:scale-[1.02]"
            >
              <Play className="w-4 h-4" fill="currentColor" />
              Trailer
            </Link>
          </div>
        </div>
      </div>

      {/* Navigation arrows  */}
      <button
        onClick={goPrev}
        className="absolute left-4 md:left-8 top-1/2 -translate-y-1/2 z-20 w-11 h-11 rounded-full glass flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity duration-300 group"
      >
        <ChevronLeft className="w-5 h-5 text-white/60 group-hover:text-gold transition-colors" />
      </button>
      <button
        onClick={goNext}
        className="absolute right-4 md:right-8 top-1/2 -translate-y-1/2 z-20 w-11 h-11 rounded-full glass flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity duration-300 group"
      >
        <ChevronRight className="w-5 h-5 text-white/60 group-hover:text-gold transition-colors" />
      </button>

      {/* Slide indicators */}
      <div className="absolute bottom-20 left-6 md:left-10 lg:left-20 z-20 flex items-center gap-2">
        {heroMovies.map((m, i) => (
          <button
            key={m.id || m.tmdb_id}
            onClick={() => goTo(i)}
            className="group relative"
          >
            <div className={`h-[3px] rounded-full transition-all duration-300 ${
              i === activeIndex ? "w-10 bg-gold" : "w-5 bg-white/15 hover:bg-white/25"
            }`}>
              {i === activeIndex && (
                <div
                  key={progressKey}
                  className="hero-progress-fill"
                  style={{
                    animationDuration: `${SLIDE_DURATION}ms`,
                    animationPlayState: isPaused ? "paused" : "running",
                  }}
                />
              )}
            </div>
          </button>
        ))}
        <span className="ml-3 text-[11px] text-white/20 font-mono tabular-nums">
          {String(activeIndex + 1).padStart(2, "0")} / {String(heroMovies.length).padStart(2, "0")}
        </span>
      </div>

      
      <div className="hidden xl:flex absolute right-10 bottom-32 z-20 gap-3">
        {heroMovies.slice(0, 5).map((m, i) => {
          const pUrl = posterUrl(m.poster_url || (m as any).poster_path, "w185");
          return (
            <button
              key={m.id || m.tmdb_id}
              onClick={() => goTo(i)}
              className={`relative w-[60px] h-[90px] rounded-lg overflow-hidden transition-all duration-400 ${
                i === activeIndex
                  ? "ring-2 ring-gold/60 scale-110 shadow-lg shadow-gold/10"
                  : "opacity-40 hover:opacity-70 scale-100"
              }`}
            >
              <Image
                src={pUrl}
                alt={m.title}
                fill
                className="object-cover"
                unoptimized
              />
            </button>
          );
        })}
      </div>
    </div>
  );
}
