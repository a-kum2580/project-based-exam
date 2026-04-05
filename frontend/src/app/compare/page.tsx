"use client";

import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import {
  Search, Star, Clock, Calendar, DollarSign, ArrowLeftRight,
  Loader2, X, Users, TrendingUp,
} from "lucide-react";
import { moviesAPI } from "@/lib/api";
import { posterUrl, formatRuntime, formatCurrency, ratingColor } from "@/lib/utils";
import type { MovieCompact } from "@/types/movie";

export default function ComparePage() {
  const [searchA, setSearchA] = useState("");
  const [searchB, setSearchB] = useState("");
  const [resultsA, setResultsA] = useState<MovieCompact[]>([]);
  const [resultsB, setResultsB] = useState<MovieCompact[]>([]);
  const [movieA, setMovieA] = useState<any>(null);
  const [movieB, setMovieB] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [searchingA, setSearchingA] = useState(false);
  const [searchingB, setSearchingB] = useState(false);

  async function searchMovies(query: string, side: "A" | "B") {
    if (query.length < 2) {
      side === "A" ? setResultsA([]) : setResultsB([]);
      return;
    }
    side === "A" ? setSearchingA(true) : setSearchingB(true);
    try {
      const data = await moviesAPI.search(query);
      side === "A" ? setResultsA(data.results.slice(0, 5)) : setResultsB(data.results.slice(0, 5));
    } catch { }
    finally {
      side === "A" ? setSearchingA(false) : setSearchingB(false);
    }
  }

  async function selectMovie(tmdbId: number, side: "A" | "B") {
    setLoading(true);
    try {
      const data = await moviesAPI.getDetail(tmdbId);
      if (side === "A") {
        setMovieA(data);
        setResultsA([]);
        setSearchA("");
      } else {
        setMovieB(data);
        setResultsB([]);
        setSearchB("");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  function CompareBar({ label, valueA, valueB, higher }: { label: string; valueA: number; valueB: number; higher: "higher" | "lower" }) {
    const max = Math.max(valueA, valueB, 1);
    const pctA = (valueA / max) * 100;
    const pctB = (valueB / max) * 100;
    const aWins = higher === "higher" ? valueA > valueB : valueA < valueB;
    const bWins = higher === "higher" ? valueB > valueA : valueB < valueA;

    return (
      <div className="py-3">
        <p className="text-[11px] uppercase tracking-wider text-white/25 font-semibold text-center mb-2">{label}</p>
        <div className="flex items-center gap-3">
          <span className={`text-sm font-bold w-20 text-right font-mono ${aWins ? "text-emerald-400" : "text-white/50"}`}>
            {typeof valueA === "number" && valueA > 1000 ? formatCurrency(valueA) : valueA || "—"}
          </span>
          <div className="flex-1 flex gap-1 h-4">
            <div className="flex-1 flex justify-end">
              <div
                className={`h-full rounded-l transition-all duration-700 ${aWins ? "bg-emerald-500/50" : "bg-white/10"}`}
                style={{ width: `${pctA}%` }}
              />
            </div>
            <div className="flex-1">
              <div
                className={`h-full rounded-r transition-all duration-700 ${bWins ? "bg-emerald-500/50" : "bg-white/10"}`}
                style={{ width: `${pctB}%` }}
              />
            </div>
          </div>
          <span className={`text-sm font-bold w-20 font-mono ${bWins ? "text-emerald-400" : "text-white/50"}`}>
            {typeof valueB === "number" && valueB > 1000 ? formatCurrency(valueB) : valueB || "—"}
          </span>
        </div>
      </div>
    );
  }

  function MovieSelector({ side, search, setSearch, results, searching, movie, clear }: any) {
    return (
      <div className="flex-1 min-w-0">
        {movie ? (
          <div className="text-center animate-fade-in">
            <div className="relative inline-block">
              <div className="w-40 h-60 rounded-xl overflow-hidden mx-auto mb-3 shadow-xl border border-white/[0.06]">
                <Image
                  src={posterUrl(movie.poster_path)}
                  alt={movie.title}
                  fill
                  className="object-cover"
                  unoptimized
                />
              </div>
              <button
                onClick={clear}
                className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-surface-3 border border-white/10 flex items-center justify-center text-white/40 hover:text-white hover:bg-red-500/20 transition-colors"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
            <h3 className="text-lg font-bold font-display">{movie.title}</h3>
            <p className="text-xs text-white/30 mt-1">
              {movie.release_date ? new Date(movie.release_date).getFullYear() : "N/A"}
              {movie.runtime ? ` • ${formatRuntime(movie.runtime)}` : ""}
            </p>
          </div>
        ) : (
          <div className="relative">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/25" />
              <input
                type="text"
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  searchMovies(e.target.value, side);
                }}
                placeholder={`Search movie ${side}...`}
                className="w-full h-12 pl-11 pr-4 rounded-xl bg-surface-2 border border-white/[0.08] text-white placeholder:text-white/20 outline-none focus:border-gold/40 transition-all text-sm font-body"
              />
              {searching && <Loader2 className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-gold/40 animate-spin" />}
            </div>

            {results.length > 0 && (
              <div className="absolute top-14 left-0 right-0 glass-card rounded-xl p-1.5 z-20 shadow-xl animate-fade-in">
                {results.map((m: any) => (
                  <button
                    key={m.id || m.tmdb_id}
                    onClick={() => selectMovie(m.tmdb_id || m.id, side)}
                    className="w-full flex items-center gap-3 p-2.5 rounded-lg hover:bg-white/5 text-left transition-colors"
                  >
                    <div className="w-8 h-12 rounded bg-surface-3 overflow-hidden flex-shrink-0">
                      <Image
                        src={posterUrl(m.poster_url || m.poster_path, "w185")}
                        alt={m.title}
                        width={32}
                        height={48}
                        className="w-full h-full object-cover"
                        unoptimized
                      />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{m.title}</p>
                      <p className="text-[11px] text-white/30">{m.year}</p>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {!search && (
              <div className="mt-6 text-center">
                <div className="w-14 h-20 rounded-lg border-2 border-dashed border-white/10 flex items-center justify-center mx-auto mb-3">
                  <Search className="w-5 h-5 text-white/10" />
                </div>
                <p className="text-xs text-white/20">Search for a movie</p>
              </div>
            )}
          </div>
        )}
      </div>
    );
  }

  const bothSelected = movieA && movieB;

  return (
    <div className="pt-24 pb-20 px-6 md:px-10 lg:px-20 max-w-[1200px] mx-auto">
      {/* Header */}
      <div className="text-center mb-10">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gold/10 border border-gold/15 mb-5">
          <ArrowLeftRight className="w-3.5 h-3.5 text-gold" />
          <span className="text-[11px] font-semibold uppercase tracking-widest text-gold">Compare</span>
        </div>
        <h1 className="text-4xl md:text-5xl font-bold font-display mb-3">
          Movie <span className="text-gold italic">Showdown</span>
        </h1>
        <p className="text-white/35 max-w-md mx-auto">
          Pick two movies and compare them head to head, ratings, budget, cast, and more.
        </p>
      </div>

      {/* Movie Selectors */}
      <div className="flex items-start gap-6 mb-12">
        <MovieSelector
          side="A"
          search={searchA}
          setSearch={setSearchA}
          results={resultsA}
          searching={searchingA}
          movie={movieA}
          clear={() => setMovieA(null)}
        />

        <div className="flex-shrink-0 pt-8">
          <div className="w-12 h-12 rounded-full glass-card flex items-center justify-center">
            <ArrowLeftRight className="w-5 h-5 text-gold/50" />
          </div>
        </div>

        <MovieSelector
          side="B"
          search={searchB}
          setSearch={setSearchB}
          results={resultsB}
          searching={searchingB}
          movie={movieB}
          clear={() => setMovieB(null)}
        />
      </div>

      {/* Comparison results */}
      {bothSelected && (
        <div className="glass-card rounded-2xl p-6 md:p-8 animate-slide-up">
          <div className="h-px bg-gradient-to-r from-transparent via-gold/15 to-transparent mb-6" />

          <h2 className="text-xl font-bold font-display text-center mb-6">Head to Head</h2>

          <CompareBar label="Rating" valueA={movieA.vote_average} valueB={movieB.vote_average} higher="higher" />
          <CompareBar label="Vote Count" valueA={movieA.vote_count} valueB={movieB.vote_count} higher="higher" />
          <CompareBar label="Popularity" valueA={Math.round(movieA.popularity)} valueB={Math.round(movieB.popularity)} higher="higher" />
          <CompareBar label="Runtime (min)" valueA={movieA.runtime || 0} valueB={movieB.runtime || 0} higher="higher" />
          <CompareBar label="Budget" valueA={movieA.budget || 0} valueB={movieB.budget || 0} higher="higher" />
          <CompareBar label="Revenue" valueA={movieA.revenue || 0} valueB={movieB.revenue || 0} higher="higher" />

          {/* Genres comparison */}
          <div className="mt-6 pt-6 border-t border-white/[0.04]">
            <p className="text-[11px] uppercase tracking-wider text-white/25 font-semibold text-center mb-4">Genres</p>
            <div className="flex gap-6">
              <div className="flex-1 text-right">
                <div className="flex flex-wrap gap-1.5 justify-end">
                  {(movieA.genres || []).map((g: any) => (
                    <span key={g.id} className="px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.06] text-[11px] text-white/50">
                      {g.name}
                    </span>
                  ))}
                </div>
              </div>
              <div className="flex-shrink-0 w-px bg-white/[0.06]" />
              <div className="flex-1">
                <div className="flex flex-wrap gap-1.5">
                  {(movieB.genres || []).map((g: any) => (
                    <span key={g.id} className="px-2.5 py-1 rounded-full bg-white/[0.04] border border-white/[0.06] text-[11px] text-white/50">
                      {g.name}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Cast comparison */}
          <div className="mt-6 pt-6 border-t border-white/[0.04]">
            <p className="text-[11px] uppercase tracking-wider text-white/25 font-semibold text-center mb-4">Top Cast</p>
            <div className="flex gap-6">
              <div className="flex-1 space-y-1.5">
                {(movieA.credits?.cast || []).slice(0, 5).map((c: any) => (
                  <div key={c.id} className="flex items-center gap-2 justify-end">
                    <div className="text-right">
                      <p className="text-[12px] text-white/60">{c.name}</p>
                      <p className="text-[10px] text-white/25">{c.character}</p>
                    </div>
                    <div className="w-7 h-7 rounded-full overflow-hidden bg-surface-3 flex-shrink-0">
                      {c.profile_path ? (
                        <Image
                          src={`https://image.tmdb.org/t/p/w185${c.profile_path}`}
                          alt={c.name} width={28} height={28}
                          className="w-full h-full object-cover" unoptimized
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-[9px] text-white/15">{c.name?.[0]}</div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <div className="flex-shrink-0 w-px bg-white/[0.06]" />
              <div className="flex-1 space-y-1.5">
                {(movieB.credits?.cast || []).slice(0, 5).map((c: any) => (
                  <div key={c.id} className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full overflow-hidden bg-surface-3 flex-shrink-0">
                      {c.profile_path ? (
                        <Image
                          src={`https://image.tmdb.org/t/p/w185${c.profile_path}`}
                          alt={c.name} width={28} height={28}
                          className="w-full h-full object-cover" unoptimized
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-[9px] text-white/15">{c.name?.[0]}</div>
                      )}
                    </div>
                    <div>
                      <p className="text-[12px] text-white/60">{c.name}</p>
                      <p className="text-[10px] text-white/25">{c.character}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
