import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import "../styles/AlbumPage.css";

function AlbumPage() {
  const { id } = useParams();
  const [album, setAlbum] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [review, setReview] = useState("");
  const [rating, setRating] = useState(0);
  const [reviews, setReviews] = useState([]);
  const [token, setToken] = useState(null);

  useEffect(() => {
    const savedToken = localStorage.getItem("id_token");
    if (savedToken) {
      console.log("✅ Token trovato:", savedToken);   // stampa in console
      setToken(savedToken);
    } else {
      console.log("⚠️ Nessun token trovato in localStorage");
    }
  }, []);

  useEffect(() => {
    async function fetchAlbumAndRatings() {
      try {
        const configResp = await fetch("/config.json");
        const config = await configResp.json();

        let albumResp;
        if (id.startsWith("a")) {
          albumResp = await fetch(`${config.apiBaseUrl}albums/${id}`);
        } else {
          const titleFromSlug = decodeURIComponent(id).replace(/-/g, " ").trim();
          albumResp = await fetch(
            `${config.apiBaseUrl}albums/by-title/${encodeURIComponent(titleFromSlug)}`
          );
        }

        if (!albumResp.ok) throw new Error("Errore API album: " + albumResp.status);
        const albumData = await albumResp.json();
        const albumObj = Array.isArray(albumData) ? albumData[0] : albumData;
        setAlbum(albumObj);

        if (albumObj?.album_id) {
          const ratingsResp = await fetch(`${config.apiBaseUrl}ratings/${albumObj.album_id}`);
          if (ratingsResp.ok) {
            const ratingsData = await ratingsResp.json();
            setReviews(ratingsData);
          } else {
            setReviews([]);
          }
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchAlbumAndRatings();
  }, [id]);

  if (loading) return <p>Caricamento...</p>;
  if (error) return <p style={{ color: "red" }}>{error}</p>;
  if (!album) return <p>Nessun album trovato</p>;

  const coverUrl = album.cover?.startsWith("http")
    ? album.cover
    : `https://rate-your-music101.s3.eu-west-3.amazonaws.com/${album.cover}`;

  async function handleAddFavorite() {
    try {
      const configResp = await fetch("/config.json");
      const config = await configResp.json();

      const resp = await fetch(`${config.apiBaseUrl}users/favorites/${album.album_id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({}),
      });

      if (!resp.ok) throw new Error("Errore API favorites");
      alert("Album aggiunto ai preferiti!");
    } catch (err) {
      alert("Errore: " + err.message);
    }
  }

  async function handleSubmitReview() {
    try {
      if (rating === 0) {
        alert("Seleziona un voto prima di inviare!");
        return;
      }

      const configResp = await fetch("/config.json");
      const config = await configResp.json();

      const resp = await fetch(`${config.apiBaseUrl}ratings/${album.album_id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ rating, comment: review }),
      });

      if (!resp.ok) throw new Error("Errore API recensione");
      setReview("");
      setRating(0);

      // refresh recensioni
      const updatedResp = await fetch(`${config.apiBaseUrl}ratings/${album.album_id}`);
      if (updatedResp.ok) {
        const updatedData = await updatedResp.json();
        setReviews(updatedData);
      }

      alert("Recensione inviata!");
    } catch (err) {
      alert("Errore: " + err.message);
    }
  }

  return (
    <div className="album-page-container min-h-screen bg-black text-white px-6 pt-32">
      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 items-start">
        {/* Colonna sinistra */}
        <div className="space-y-6 w-full md:w-[280px]">
          <img
            src={coverUrl}
            alt={album.title}
            className="mx-auto rounded-lg shadow-lg max-w-[250px] max-h-[350px] object-contain"
          />
          <div className="tracklist">
            <h3 className="text-xl font-semibold mb-2">Tracklist</h3>
            {album.songs?.length > 0 ? (
              <ol className="list-decimal list-inside space-y-1">
                {album.songs.map((song, idx) => (
                  <li key={idx}>{song}</li>
                ))}
              </ol>
            ) : (
              <p className="text-gray-400">Nessuna traccia disponibile.</p>
            )}
          </div>
        </div>

        {/* Colonna destra */}
        <div className="space-y-4 album-info">
          <h1 className="text-3xl font-bold">{album.title}</h1>
          <p className="text-xl text-gray-300">{album.artist}</p>
          <p className="text-gray-400">Anno: {album.year}</p>
          <p>
            ⭐ {(album.average_rating ?? 0).toFixed(1)} su {album.ratings_count ?? 0} voti
          </p>
          <p className="italic text-gray-400">Genere: {album.genre}</p>

          {token && (
            <>
              <button onClick={handleAddFavorite} className="login-btn">
                ⭐ Aggiungi ai preferiti
              </button>

              <div className="mt-6">
                <h3 className="text-lg font-semibold">Lascia una recensione</h3>
                <label className="block mb-2">Il tuo voto:</label>
                <select
                  value={rating}
                  onChange={(e) => setRating(Number(e.target.value))}
                  className="border rounded p-2 text-black mb-4"
                >
                  <option value={0}>Seleziona...</option>
                  <option value={1}>1 ⭐</option>
                  <option value={2}>2 ⭐⭐</option>
                  <option value={3}>3 ⭐⭐⭐</option>
                  <option value={4}>4 ⭐⭐⭐⭐</option>
                  <option value={5}>5 ⭐⭐⭐⭐⭐</option>
                </select>

                <textarea
                  value={review}
                  onChange={(e) => setReview(e.target.value)}
                  placeholder="Scrivi qui la tua recensione..."
                  className="w-full border rounded p-2 text-black"
                />
                <button onClick={handleSubmitReview} className="login-btn mt-2">
                  Invia
                </button>
              </div>
            </>
          )}

          <div className="mt-6">
            <h3 className="text-lg font-semibold">Commenti degli utenti</h3>
            {reviews.length > 0 ? (
              <ul className="space-y-4 mt-2">
                {reviews.map((rev, idx) => (
                  <li key={idx} className="border-b border-gray-700 pb-2">
                    <p className="font-semibold">
                      ⭐ {rev.rating} – {rev.user_id}
                    </p>
                    <p>{rev.comment}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(rev.timestamp).toLocaleString()}
                    </p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-400">Nessun commento disponibile.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default AlbumPage;
