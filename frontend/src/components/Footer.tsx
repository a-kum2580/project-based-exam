import { Film, ExternalLink } from "lucide-react";
import Link from "next/link";

export default function Footer() {
  return (
    <footer className="relative border-t border-white/[0.04] bg-surface-1/50">
      {/* Top shine */}
      <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-gold/10 to-transparent" />

      <div className="max-w-[1440px] mx-auto px-6 md:px-10 py-14">
        <div className="flex flex-col md:flex-row justify-between gap-10">
          {/* Brand */}
          <div className="max-w-xs">
            <Link href="/" className="flex items-center gap-2.5 mb-4">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-gold to-gold-dim flex items-center justify-center">
                <Film className="w-4 h-4 text-surface-0" />
              </div>
              <span className="text-lg font-bold font-display">
                Cine<span className="text-gold">Quest</span>
              </span>
            </Link>
            <p className="text-sm text-white/25 leading-relaxed">
              Your personal cinema discovery engine.
              Explore genres, directors, and find hidden gems tailored to your taste.
            </p>
          </div>

          {/* Links */}
          <div className="flex gap-16">
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-gold/40 mb-4">
                Explore
              </h4>
              <div className="space-y-2.5">
                {[
                  { href: "/search", label: "Discover" },
                  { href: "/genre", label: "Genres" },
                  { href: "/search?sort=trending", label: "Trending" },
                  { href: "/search?sort=top_rated", label: "Top Rated" },
                ].map(({ href, label }) => (
                  <Link
                    key={href}
                    href={href}
                    className="block text-sm text-white/30 hover:text-white/60 transition-colors"
                  >
                    {label}
                  </Link>
                ))}
              </div>
            </div>
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wider text-gold/40 mb-4">
                Powered By
              </h4>
              <div className="space-y-2.5">
                {[
                  { href: "https://www.themoviedb.org/", label: "TMDB API" },
                  { href: "https://en.wikipedia.org/", label: "Wikipedia" },
                  { href: "https://www.justwatch.com/", label: "JustWatch" },
                ].map(({ href, label }) => (
                  <a
                    key={href}
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-sm text-white/30 hover:text-white/60 transition-colors"
                  >
                    {label}
                    <ExternalLink className="w-3 h-3 opacity-50" />
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom */}
        <div className="section-divider mt-10 mb-6" />
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-[11px] text-white/15">
            This product uses the TMDB API but is not endorsed or certified by TMDB.
          </p>
          <p className="text-[11px] text-white/15">
            © {new Date().getFullYear()} CineQuest. Built with care.
          </p>
        </div>
      </div>
    </footer>
  );
}
