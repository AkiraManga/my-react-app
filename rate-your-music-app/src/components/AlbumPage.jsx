import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

function AlbumPage() {
  const { id } = useParams();
  const [album, setAlbum] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [review, setReview] = useState("");

  useEffect(() => {
    async function fetchAlbum() {
      try {
        const configResp = await fetch("/config.json");
        const config = await configResp.json();
        const resp = await fetch(`${config.apiBaseUrl}albums/${id}`);
        if (!resp.ok) throw new Error("Errore API: " + resp.status);
        const data = await resp.json();
        setAlbum(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    fetchAlbum();
  }, [id]);

  if (loading) return <p>Caricamento...</p>;
  if (error) return <p style={{ color: "red" }}>{error}</p>;
  if (!album) return <p>Nessun album trovato</p>;

  // Gestione cover (se URL esterno o file S3)
  const coverUrl = album.cover.startsWith("http")
    ? album.cover
    : `https://rate-your-music101.s3.eu-west-3.amazonaws.com/${album.cover}`;

  return (
    <div className="album-page flex gap-8 p-6 items-start">
      {/* Colonna sinistra: copertina + tracklist */}
      <div className="w-1/3 space-y-6">
        <img
          src={coverUrl}
          alt={album.title}
          className="rounded-lg shadow-lg w-full object-cover"
        />

        {/* Tracklist */}
        <div>
          <h3 className="text-lg font-semibold">Tracklist</h3>
          {album.songs && album.songs.length > 0 ? (
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

      {/* Colonna destra: dettagli + recensioni */}
      <div className="w-2/3 space-y-4">
        <h1 className="text-3xl font-bold">{album.title}</h1>
        <p className="text-xl text-gray-300">{album.artist}</p>
        <p className="text-gray-400">Anno: {album.year}</p>

        {/* Media recensioni */}
        <p>
          ⭐ {album.average_rating.toFixed(1)} su {album.ratings_count} voti
        </p>

        <p className="italic text-gray-400">Genere: {album.genre}</p>

        {/* Form recensione */}
        <div className="mt-6">
          <h3 className="text-lg font-semibold">Lascia una recensione</h3>
          <textarea
            value={review}
            onChange={(e) => setReview(e.target.value)}
            placeholder="Scrivi qui la tua recensione..."
            className="w-full border rounded p-2 text-black"
          />
          <button
            onClick={() => alert("TODO: invio recensione via API")}
            className="mt-2 px-4 py-2 bg-blue-600 text-white rounded"
          >
            Invia
          </button>
        </div>

        {/* Recensioni altri utenti (placeholder) */}
        <div className="mt-6">
          <h3 className="text-lg font-semibold">Recensioni degli utenti</h3>
          <p className="text-gray-400">⚠️ Qui verranno mostrate da API.</p>
        </div>
      </div>
    </div>
  );
}

export default AlbumPage;
