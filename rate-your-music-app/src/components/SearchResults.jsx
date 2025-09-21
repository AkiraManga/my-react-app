import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";

function SearchResults() {
  const { query } = useParams();
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchResults() {
      try {
        const configResp = await fetch("/config.json");
        const config = await configResp.json();

        // Prova ricerca diretta per titolo
        const resp = await fetch(
          `${config.apiBaseUrl}albums/by-title/${encodeURIComponent(query)}`
        );

        if (resp.ok) {
          const data = await resp.json();
          if (data.length > 0) {
            setResults(data);
          } else {
            // Se non trova niente → fallback: prendi tutti e filtra
            const allResp = await fetch(`${config.apiBaseUrl}albums`);
            const allData = await allResp.json();
            const q = query.toLowerCase();
            const filtered = allData.filter(
              (album) =>
                album.title.toLowerCase().includes(q) ||
                album.artist.toLowerCase().includes(q)
            );
            setResults(filtered);
          }
        }
      } catch (err) {
        console.error("Errore ricerca:", err);
        setResults([]);
      } finally {
        setLoading(false);
      }
    }

    fetchResults();
  }, [query]);

  if (loading) return <p>Caricamento...</p>;
  if (!results.length) return <p>Nessun risultato trovato per "{query}"</p>;

  return (
    <div className="results p-6">
      <h2 className="text-2xl font-bold mb-4">Risultati per: {query}</h2>
      <ul className="space-y-2">
        {results.map((album) => (
          <li key={album.album_id}>
            <Link
              to={`/album/${album.album_id}`}
              className="text-blue-400 hover:underline"
            >
              {album.title} – {album.artist} ({album.year})
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default SearchResults;
