"use client";

import { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  BarChart3, Heart, ThumbsDown, Eye, Bookmark, Star,
  TrendingUp, Clock, LogIn, Sparkles, Film
} from "lucide-react";
import { useAuth } from "@/lib/AuthContext";
import { recommendationsAPI } from "@/lib/api";

export default function DashboardPage() {
  const { user, isAuthenticated, loading: authLoading } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeList, setActiveList] = useState<"liked" | "disliked" | "watched" | "watchlist" | null>(null);
  const listPanelRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      setLoading(false);
      return;
    }
    fetchDashboard();
  }, [isAuthenticated]);

  async function fetchDashboard() {
    try {
      const data = await recommendationsAPI.getDashboard();
      setStats(data);
    } catch (err) {
      console.error("Dashboard error:", err);
    } finally {
      setLoading(false);
    }
  }

  // Not logged in
  if (!authLoading && !isAuthenticated) {
    return (
      <div className="pt-24 pb-20 px-6 md:px-10 lg:px-20 max-w-[1440px] mx-auto">
        <div className="max-w-md mx-auto text-center py-20">
          <div className="w-16 h-16 rounded-2xl glass-card flex items-center justify-center mx-auto mb-6">
            <BarChart3 className="w-8 h-8 text-gold/30" />
          </div>
          <h1 className="text-3xl font-bold font-display mb-3">Your Dashboard</h1>
          <p className="text-white/30 mb-6">
            Sign in to track your movie preferences, view genre analytics, and get personalized insights.
          </p>
          <Link
            href="/"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-gold to-gold-dim text-surface-0 font-semibold text-sm"
          >
            <LogIn className="w-4 h-4" />
            Sign in to continue
          </Link>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="pt-24 pb-20 px-6 md:px-10 lg:px-20 max-w-[1440px] mx-auto">
        <div className="space-y-6">
          <div className="skeleton h-12 w-64 rounded-xl" />
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="skeleton h-28 rounded-xl" />
            ))}
          </div>
          <div className="skeleton h-64 rounded-xl" />
        </div>
      </div>
    );
  }

  const summary = stats?.summary || {};
  const genreDistData = stats?.genre_distribution || { genres: [], total_genres: 0 };
  const genreDist = genreDistData.genres || [];
  const totalGenreCount = genreDistData.total_genres || 0;
  const prefScores = stats?.preference_scores || [];
  const timeline = stats?.activity_timeline || [];
  const recent = stats?.recent_activity || [];
  const likedMovies = stats?.liked_movies || [];
  const dislikedMovies = stats?.disliked_movies || [];
  const watchedMovies = stats?.watched_movies || [];
  const watchlistMovies = stats?.watchlist_movies || [];
  const maxGenreCount = Math.max(...genreDist.map((g: any) => g.count), 1);
  const maxPrefWeight = Math.max(...prefScores.map((p: any) => p.weight), 1);
  const totalInteractions = summary.total_interactions || 0;

  const interactionWeightKey = [
    { type: "Like", weight: "+5.0", color: "text-emerald-400" },
    { type: "Watched", weight: "+3.0", color: "text-blue-400" },
    { type: "Watchlist", weight: "+2.5", color: "text-gold" },
    { type: "View", weight: "+1.0", color: "text-cyan-400" },
    { type: "Search", weight: "+0.5", color: "text-fuchsia-400" },
    { type: "Dislike", weight: "-3.0", color: "text-red-400" },
  ];

  const statCards = [
    { key: "liked", label: "Liked", value: summary.likes || 0, icon: Heart, color: "text-emerald-400", bg: "from-emerald-500/10 to-emerald-600/5" },
    { key: "disliked", label: "Disliked", value: summary.dislikes || 0, icon: ThumbsDown, color: "text-red-400", bg: "from-red-500/10 to-red-600/5" },
    { key: "watched", label: "Watched", value: summary.watched || 0, icon: Eye, color: "text-blue-400", bg: "from-blue-500/10 to-blue-600/5" },
    { key: "watchlist", label: "Watchlist", value: summary.watchlist_total || 0, icon: Bookmark, color: "text-gold", bg: "from-gold/10 to-amber-600/5" },
  ];

  const listMeta: Record<string, { title: string; emptyText: string; colorClass: string }> = {
    liked: { title: "Liked Movies", emptyText: "You have not liked any movies yet.", colorClass: "text-emerald-400" },
    disliked: { title: "Disliked Movies", emptyText: "You have not disliked any movies yet.", colorClass: "text-red-400" },
    watched: { title: "Watched Movies", emptyText: "No watched movie activity yet.", colorClass: "text-blue-400" },
    watchlist: { title: "Watchlist Movies", emptyText: "Your watchlist is empty.", colorClass: "text-gold" },
  };

  function getActiveListItems() {
    if (activeList === "liked") return likedMovies;
    if (activeList === "disliked") return dislikedMovies;
    if (activeList === "watched") return watchedMovies;
    if (activeList === "watchlist") return watchlistMovies;
    return [];
  }

  function getItemDate(item: any) {
    const raw = item.liked_at || item.disliked_at || item.watched_at || item.added_at;
    return raw ? new Date(raw).toLocaleDateString() : "";
  }

  function handleStatCardClick(cardKey?: "liked" | "disliked" | "watched" | "watchlist") {
    if (!cardKey) return;
    setActiveList(cardKey);
    requestAnimationFrame(() => {
      listPanelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  return (
    <div className="pt-24 pb-20 px-6 md:px-10 lg:px-20 max-w-[1440px] mx-auto">
      {/* Header */}
      <div className="flex items-center gap-4 mb-10">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-gold to-gold-dim flex items-center justify-center shadow-lg shadow-gold/10">
          <BarChart3 className="w-5 h-5 text-surface-0" />
        </div>
        <div>
          <h1 className="text-3xl font-bold font-display">
            Your <span className="text-gold italic">Dashboard</span>
          </h1>
          <p className="text-sm text-white/30">
            Welcome back, {user?.username}. Here&apos;s your movie journey.
          </p>
        </div>
      </div>

      {/* Statistics cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
        {statCards.map(({ key, label, value, icon: Icon, color, bg }) => (
          <div
            key={label}
            className="glass-card rounded-xl p-5 relative overflow-hidden cursor-pointer hover:border-gold/30 transition-colors"
            onClick={() => handleStatCardClick(key as "liked" | "disliked" | "watched" | "watchlist")}
            {...(key
              ? {
                  role: "button",
                  tabIndex: 0,
                  onKeyDown: (e: React.KeyboardEvent<HTMLDivElement>) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      handleStatCardClick(key as "liked" | "disliked" | "watched" | "watchlist");
                    }
                  },
                  title: `Click to view ${label.toLowerCase()} list`,
                }
              : {})}
          >
            <div className={`absolute inset-0 bg-gradient-to-br ${bg}`} />
            <div className="relative z-10">
              <Icon className={`w-5 h-5 ${color} mb-3`} />
              <p className="text-3xl font-bold font-display">{value}</p>
              <p className="text-[11px] text-white/30 uppercase tracking-wider mt-1">{label}</p>
              <p className="text-[10px] text-white/35 mt-0.5">out of {totalInteractions} tracked events</p>
              <p className="text-[10px] text-gold/70 mt-1">View list</p>
            </div>
          </div>
        ))}
      </div>

      {activeList && (
        <div ref={listPanelRef} className="glass-card rounded-xl p-6 mb-10">
          <div className="flex items-center justify-between gap-4 mb-5">
            <div className="flex items-center gap-2">
              {activeList === "liked" && <Heart className="w-4 h-4 text-emerald-400" />}
              {activeList === "disliked" && <ThumbsDown className="w-4 h-4 text-red-400" />}
              {activeList === "watched" && <Eye className="w-4 h-4 text-blue-400" />}
              {activeList === "watchlist" && <Bookmark className="w-4 h-4 text-gold" />}
              <h2 className="text-lg font-bold font-display">{listMeta[activeList].title}</h2>
            </div>
            {getActiveListItems().length > 0 && (
              <button
                onClick={() => setActiveList(null)}
                className="text-xs px-3 py-1.5 rounded-lg bg-gradient-to-r from-gold to-gold-dim text-surface-0 font-semibold hover:shadow-md hover:shadow-gold/20 transition-all"
              >
                Hide
              </button>
            )}
          </div>
          {getActiveListItems().length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {getActiveListItems().map((item: any, idx: number) => (
                <Link
                  key={`${item.movie_tmdb_id}-${idx}`}
                  href={`/movie/${item.movie_tmdb_id}`}
                  className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.04] hover:border-emerald-500/30 transition-colors"
                >
                  <span className="text-sm text-white/80 truncate pr-3">{item.movie_title || `Movie #${item.movie_tmdb_id}`}</span>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {item.source_interaction && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        item.source_interaction === "like"
                          ? "bg-emerald-500/15 text-emerald-400"
                          : item.source_interaction === "dislike"
                            ? "bg-red-500/15 text-red-400"
                            : "bg-blue-500/15 text-blue-400"
                      }`}>
                        {item.source_interaction}
                      </span>
                    )}
                    <span className="text-[11px] text-white/25">{getItemDate(item)}</span>
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <p className="text-sm text-white/30">{listMeta[activeList].emptyText}</p>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-10">
        {/* Genre distribution */}
        <div className="glass-card rounded-xl p-6">
          <div className="flex items-center gap-2 mb-5">
            <Film className="w-4 h-4 text-gold" />
            <h2 className="text-lg font-bold font-display">Genre Distribution</h2>
            {totalGenreCount > 0 && (
              <span className="text-xs text-white/30 ml-auto">
                out of {totalGenreCount} total genre occurrences
              </span>
            )}
          </div>
          <p className="text-xs text-white/35 mb-4">
            Each genre count is based on all genre tags seen in your tracked interactions.
          </p>
          {genreDist.length > 0 ? (
            <div className="space-y-3">
              {genreDist.slice(0, 8).map((genre: any) => (
                <div key={genre.name} className="flex items-center gap-3">
                  <span className="text-[12px] text-white/50 w-24 text-right flex-shrink-0 truncate">
                    {genre.name}
                  </span>
                  <div className="flex-1 h-6 bg-surface-3 rounded-lg overflow-hidden">
                    <div
                      className="h-full rounded-lg bg-gradient-to-r from-gold/60 to-gold/30 transition-all duration-700"
                      style={{ width: `${(genre.count / maxGenreCount) * 100}%` }}
                    />
                  </div>
                  <span className="text-[12px] text-white/30 w-12 font-mono text-right">{genre.count} ({genre.percentage}%)</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-white/20 text-center py-8">
              Like some movies to see your genre breakdown
            </p>
          )}
        </div>

        {/* Preference scores */}
        <div className="glass-card rounded-xl p-6">
          <div className="flex items-center gap-2 mb-5">
            <TrendingUp className="w-4 h-4 text-gold" />
            <h2 className="text-lg font-bold font-display">Preference Scores</h2>
            <span className="text-xs text-white/30 ml-auto">out of 100</span>
          </div>
          <p className="text-xs text-white/35 mb-4">
            Weighted by interaction type, then normalized so your strongest genre is 100.
          </p>
          {prefScores.length > 0 ? (
            <div className="space-y-3">
              {prefScores.slice(0, 8).map((pref: any) => (
                <div key={pref.name} className="flex items-center gap-3">
                  <span className="text-[12px] text-white/50 w-24 text-right flex-shrink-0 truncate">
                    {pref.name}
                  </span>
                  <div className="flex-1 h-6 bg-surface-3 rounded-lg overflow-hidden">
                    <div
                      className="h-full rounded-lg bg-gradient-to-r from-emerald-500/60 to-emerald-500/30 transition-all duration-700"
                      style={{ width: `${(pref.weight / maxPrefWeight) * 100}%` }}
                    />
                  </div>
                  <span className="text-[12px] text-white/30 w-10 font-mono">{pref.weight}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-white/20 text-center py-8">
              Interact with movies to build your preference profile
            </p>
          )}
          <div className="mt-5 rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
            <div className="flex items-center justify-between gap-3 mb-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-white/55">How Scoring Works</h3>
              <span className="text-[11px] text-white/35">weight per interaction</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
              {interactionWeightKey.map((item) => (
                <div key={item.type} className="rounded-lg border border-white/[0.06] bg-surface-2 px-3 py-2">
                  <p className="text-[10px] uppercase tracking-wide text-white/40">{item.type}</p>
                  <p className={`text-sm font-semibold ${item.color}`}>{item.weight}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Activity timeline */}
      {timeline.length > 0 && (
        <div className="glass-card rounded-xl p-6 mb-10">
          <div className="flex items-center gap-2 mb-5">
            <Clock className="w-4 h-4 text-gold" />
            <h2 className="text-lg font-bold font-display">Activity (Last 30 Days)</h2>
          </div>
          <div className="flex items-end gap-1 h-32">
            {timeline.map((day: any) => {
              const maxCount = Math.max(...timeline.map((d: any) => d.count), 1);
              const height = (day.count / maxCount) * 100;
              return (
                <div
                  key={day.date}
                  className="flex-1 group relative"
                  title={`${day.date}: ${day.count} interactions`}
                >
                  <div
                    className="w-full bg-gradient-to-t from-gold/50 to-gold/20 rounded-t transition-all hover:from-gold/70 hover:to-gold/40"
                    style={{ height: `${Math.max(height, 4)}%` }}
                  />
                </div>
              );
            })}
          </div>
          <div className="flex justify-between text-[10px] text-white/15 mt-2">
            <span>{timeline[0]?.date}</span>
            <span>{timeline[timeline.length - 1]?.date}</span>
          </div>
        </div>
      )}

      {/* Recent activity */}
      {recent.length > 0 && (
        <div className="glass-card rounded-xl p-6">
          <div className="flex items-center gap-2 mb-5">
            <Sparkles className="w-4 h-4 text-gold" />
            <h2 className="text-lg font-bold font-display">Recent Activity</h2>
          </div>
          <div className="space-y-2">
            {recent.map((item: any, i: number) => (
              <div
                key={i}
                className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.04]"
              >
                <div className="flex items-center gap-3">
                  <span className={`text-xs font-semibold px-2 py-0.5 rounded-md ${
                    item.interaction_type === "like" ? "bg-emerald-500/15 text-emerald-400" :
                    item.interaction_type === "dislike" ? "bg-red-500/15 text-red-400" :
                    item.interaction_type === "watched" ? "bg-blue-500/15 text-blue-400" :
                    "bg-white/5 text-white/40"
                  }`}>
                    {item.interaction_type}
                  </span>
                  <span className="text-sm text-white/70">{item.movie_title}</span>
                </div>
                <span className="text-[11px] text-white/20">
                  {new Date(item.created_at).toLocaleDateString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {summary.total_interactions === 0 && (
        <div className="text-center py-16 glass-card rounded-2xl">
          <BarChart3 className="w-10 h-10 text-gold/20 mx-auto mb-4" />
          <h3 className="text-xl font-bold font-display mb-2">No activity yet</h3>
          <p className="text-sm text-white/30 mb-6 max-w-sm mx-auto">
            Start exploring movies, liking your favorites, and building your watchlist to see your stats here.
          </p>
          <Link
            href="/mood"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-gold to-gold-dim text-surface-0 font-semibold text-sm"
          >
            <Sparkles className="w-4 h-4" /> Pick a Mood
          </Link>
        </div>
      )}
    </div>
  );
}
