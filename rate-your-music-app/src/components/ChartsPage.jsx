import { useEffect, useMemo, useRef, useState } from "react";
import "../styles/ChartsPage.css";

/** piccola key per persistere l’anno scelto */
const LS_KEY = "charts_year";

export default function ChartsPage() {
  const [config, setConfig] = useState(null);
  const [year, setYear] = useState(
    () => Number(localStorage.getItem(LS_KEY)) || new Date().getFullYear()
  );
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");
  const scrollRef = useRef(null);

  // cache config
  const getConfig = useMemo(() => {
    let cache = null;
    return async () => {
      if (cache) return cache;
      const r = await fetch("/config.json");
      cache = await r.json();
      return cache;
    };
  }, []);

  useEffect(() => {
    (async () => {
      const c = await getConfig();
      setConfig(c);
    })();
  }, [getConfig]);

  // fetch classifica + arricchimento con ratings
  useEffect(() => {
    if (!config) return;
    (async () => {
      try {
        setLoading(true);
        setErr("");
        localStorage.setItem(LS_KEY, String(year));

        // 1) classifica per anno
        const res = await fetch(`${config.apiBaseUrl}charts/${year}`);
        if (!res.ok) throw new Error(`(${res.status}) ${await res.text()}`);
        const data = await res.json();
        const baseItems = data.items || [];

        // 2) arricchisco con media/voti/recensioni
        const enriched = await Promise.all(
          baseItems.map(async (it) => {
            if (!it.album_id) {
              return { ...it, average_rating: 0, ratings_count: 0, reviews_count: 0 };
            }
            try {
              const r = await fetch(`${config.apiBaseUrl}ratings/${it.album_id}`);
              if (!r.ok) throw new Error();
              const rd = await r.json();
              return {
                ...it,
                average_rating: rd.average_rating ?? 0,
                ratings_count: rd.ratings_count ?? 0,
                reviews_count:
                  (Array.isArray(rd.reviews) ? rd.reviews.length : rd.reviews_count) ?? 0,
              };
            } catch {
              return { ...it, average_rating: 0, ratings_count: 0, reviews_count: 0 };
            }
          })
        );

        setItems(enriched);
      } catch (e) {
        setItems([]);
        setErr(e.message || "Errore");
      } finally {
        setLoading(false);
      }
    })();
  }, [config, year]);

  // anni (1970 → oggi)
  const years = [];
  for (let y = new Date().getFullYear(); y >= 1970; y--) years.push(y);

  // scroll year-bar
  const scroll = (dir) => {
    if (!scrollRef.current) return;
    const w = scrollRef.current.clientWidth;
    scrollRef.current.scrollBy({ left: dir === "left" ? -w : w, behavior: "smooth" });
  };

  return (
    <div className="charts-page">
      <div className="charts-container">
        <div className="charts-header">
          <h1>Classifica album</h1>
        </div>

        {/* Year bar */}
        <div className="year-bar-wrapper">
          <button className="year-arrow" onClick={() => scroll("left")} aria-label="precedenti">‹</button>
          <div className="year-bar" ref={scrollRef}>
            {years.map((y) => (
              <button
                key={y}
                className={`year-btn ${year === y ? "active" : ""}`}
                onClick={() => setYear(y)}
              >
                {y}
              </button>
            ))}
          </div>
          <button className="year-arrow" onClick={() => scroll("right")} aria-label="successivi">›</button>
        </div>

        {loading && <p>Caricamento…</p>}
        {err && <p style={{ color: "#f87171" }}>{err}</p>}
        {!loading && !err && items.length === 0 && (
          <p style={{ color: "#9ca3af" }}>Nessun dato per questo anno.</p>
        )}

        <ul className="chart-list">
          {items.map((it, idx) => (
            <li key={it.album_id || idx} className="chart-item">
              {/* Rank */}
              <div className="chart-rank">{it.rank && it.rank > 0 ? it.rank : idx + 1}</div>

              {/* Cover */}
              {it.cover && <img src={it.cover} alt={it.title} className="chart-cover" />}

              {/* Info */}
              <div className="chart-info">
                <p className="title">{it.title}</p>
                <p className="artist">{it.artist}</p>
                <p className="year">{it.release_date || it.year || ""}</p>
              </div>

              {/* Stats: media / 5, voti, recensioni */}
              <div className="chart-stats">
                <p className="score">
                  ⭐ {Number(it.average_rating ?? 0).toFixed(2)} <span className="outof">/ 5</span>
                </p>
                <p className="votes">{it.ratings_count ?? 0} voti</p>
                <p className="reviews">{it.reviews_count ?? 0} recensioni</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
