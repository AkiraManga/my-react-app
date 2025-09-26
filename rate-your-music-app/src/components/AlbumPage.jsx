import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import "../styles/AlbumPage.css";

/** ⭐ Slider a stelle (range mascherato) — visibile solo se loggato */
function StarRating({ value, onChange }) {
  const max = 5;
  const filled = (value || 0) / max; // 0..1

  return (
    <div className="star-range">
      <input
        type="range"
        min={1}
        max={max}
        step={1}
        value={value || 0}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label="Valutazione in stelle"
        style={{ "--p": filled }}   // ⬅️ questa riga riempie fino alla stella scelta
      />
      <span className="ml-2 text-sm">{value || 0}/{max}</span>
    </div>
  );
}


export default function AlbumPage() {
  const { id } = useParams();
  const [album, setAlbum] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errMsg, setErrMsg] = useState("");
  const [review, setReview] = useState("");
  const [rating, setRating] = useState(0);
  const [reviews, setReviews] = useState([]);
  const [token, setToken] = useState(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("id_token");
    if (saved) setToken(saved);
  }, []);

  const getConfig = useMemo(() => {
    let cache = null;
    return async () => {
      if (cache) return cache;
      const resp = await fetch("/config.json");
      cache = await resp.json();
      return cache;
    };
  }, []);

  async function fetchAlbumAndRatings({ showSpinner = true } = {}) {
    try {
      if (showSpinner) setLoading(true);
      setErrMsg("");
      const config = await getConfig();

      const albumResp = await fetch(`${config.apiBaseUrl}albums/by-slug/${encodeURIComponent(id)}`);
      if (!albumResp.ok) {
        if (albumResp.status === 404) throw new Error("Album non trovato");
        throw new Error("Errore API album: " + albumResp.status);
      }
      const albumData = await albumResp.json();
      const albumObj = Array.isArray(albumData) ? albumData[0] : albumData;
      if (!albumObj) throw new Error("Album non trovato");
      setAlbum(albumObj);

      if (albumObj.album_id) {
        const r = await fetch(`${config.apiBaseUrl}ratings/${albumObj.album_id}`);
        if (!r.ok) throw new Error("Errore API ratings: " + r.status);
        const data = await r.json();
        setReviews(data.reviews || []);
        setAlbum((prev) =>
          prev
            ? {
                ...prev,
                ratings_count: data.ratings_count ?? prev.ratings_count ?? 0,
                average_rating: data.average_rating ?? prev.average_rating ?? 0,
                ranks: data.ranks ?? prev.ranks ?? [],
              }
            : prev
        );
      }
    } catch (e) {
      setErrMsg(e.message || "Errore di caricamento");
    } finally {
      if (showSpinner) setLoading(false);
    }
  }

  useEffect(() => {
    fetchAlbumAndRatings({ showSpinner: true });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  async function handleSubmitReview(e) {
    e?.preventDefault();
    if (!token) return alert("Devi effettuare il login per recensire");
    if (!album?.album_id) return;
    try {
      setBusy(true);
      const config = await getConfig();
      const resp = await fetch(`${config.apiBaseUrl}ratings/${album.album_id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ rating, comment: review }),
      });
      if (!resp.ok) throw new Error("Errore invio recensione");
      setReview("");
      setRating(0);
      await fetchAlbumAndRatings({ showSpinner: false });
    } catch (e) {
      alert(e.message || "Errore invio recensione");
    } finally {
      setBusy(false);
    }
  }

  async function handleLike(reviewUserId) {
    if (!token) return alert("Devi effettuare il login per mettere like");
    if (!album?.album_id) return;
    try {
      const config = await getConfig();
      const resp = await fetch(`${config.apiBaseUrl}ratings/${album.album_id}/${reviewUserId}/like`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (resp.status === 409) return alert("Hai già messo like");
      if (!resp.ok) throw new Error("Errore like");
      setReviews((prev) =>
        prev.map((r) => (r.user_id === reviewUserId ? { ...r, likes: (r.likes || 0) + 1 } : r))
      );
    } catch (e) {
      alert(e.message || "Errore like");
    }
  }

  async function handleAddFavorite(e) {
    e?.preventDefault();
    if (!token) return alert("Devi effettuare il login per aggiungere ai preferiti");
    if (!album?.album_id) return;
    try {
      const config = await getConfig();
      const resp = await fetch(`${config.apiBaseUrl}users/favorites/${album.album_id}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) throw new Error("Errore aggiunta ai preferiti");
      alert("Aggiunto ai preferiti ✅");
    } catch (e) {
      alert(e.message || "Errore preferiti");
    }
  }

  if (loading) return <p className="rym-album">Caricamento…</p>;
  if (errMsg) return <p className="rym-album" style={{ color: "#f87171" }}>{errMsg}</p>;
  if (!album) return <p className="rym-album">Nessun album trovato</p>;

  const coverUrl =
    album.cover && album.cover.startsWith("http")
      ? album.cover
      : `https://rate-your-music101.s3.eu-west-3.amazonaws.com/${album.cover}`;

  return (
    <div className="rym-album">
      <div className="album-header">
        {/* Sinistra */}
        <div className="left-col">
          <img src={coverUrl} alt={album.title} className="album-cover" />
          {token && (
            <div className="album-actions">
              <button type="button" onClick={handleAddFavorite} className="btn-fav">
                ❤️ Aggiungi ai preferiti
              </button>
            </div>
          )}
          <div className="tracklist">
            <h3>Tracklist</h3>
            {album.songs?.length ? (
              <ol>{album.songs.map((s, i) => <li key={i}>{s}</li>)}</ol>
            ) : (
              <p className="muted">Nessuna traccia disponibile.</p>
            )}
          </div>
        </div>

        {/* Destra */}
        <div className="album-info">
          <h1>{album.title}</h1>
          <p className="artist">{album.artist}</p>
          <p>Anno: {album.year}</p>
          <p className="rating">⭐ {(album.average_rating ?? 0).toFixed(1)} su {album.ratings_count ?? 0} voti</p>
          {album.ranks?.length > 0 && (
            <p className="rank">
              Classifica: {album.ranks.map((r) => `#${r.rank} nel ${r.year}`).join(", ")}
            </p>
          )}

          {/* Form recensione SOLO se loggato */}
          {token && (
            <div className="review-box">
              <h3>Lascia una recensione</h3>
              <StarRating value={rating} onChange={setRating} />
              <textarea
                value={review}
                onChange={(e) => setReview(e.target.value)}
                placeholder="Scrivi qui la tua recensione…"
                rows={4}
                style={{ width: "100%", marginTop: 8 }}
              />
              <button
                type="button"
                onClick={handleSubmitReview}
                disabled={busy || rating === 0}
                className={`btn-send ${busy || rating === 0 ? "disabled" : ""}`}
              >
                {busy ? "Invio…" : "Invia"}
              </button>
            </div>
          )}

          <div className="reviews">
            <h3>Commenti degli utenti</h3>
            {reviews?.length ? (
              <ul>
                {reviews.map((rev, idx) => (
                  <li key={`${rev.user_id}-${rev.timestamp}-${idx}`}>
                    <p><strong>⭐ {rev.rating}</strong> – <span>{rev.user_id}</span></p>
                    {rev.comment && <p>{rev.comment}</p>}
                    <p className="meta">{rev.timestamp ? new Date(rev.timestamp).toLocaleString() : ""}</p>
                    {/* Il like si vede sempre, ma richiede login al click */}
                    <button type="button" onClick={() => handleLike(rev.user_id)}>👍 {rev.likes || 0}</button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="muted">Nessun commento disponibile.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
