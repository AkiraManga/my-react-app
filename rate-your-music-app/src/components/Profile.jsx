import { useEffect, useState } from "react";

function Profile() {
  const [user, setUser] = useState({ email: "test@example.com" }); // mock
  const [favourites, setFavourites] = useState([]);

  useEffect(() => {
    async function fetchFavourites() {
      try {
        const configResp = await fetch("/config.json");
        const config = await configResp.json();

        // 🔹 Chiamata API a DynamoDB (da fare lato Lambda, qui è mock)
        // const resp = await fetch(`${config.apiBaseUrl}favourites/${user.email}`);
        // const data = await resp.json();
        // setFavourites(data);

        // mock temporaneo
        setFavourites([
          { id: "a001", title: "Random Access Memories" },
          { id: "a002", title: "OK Computer" },
        ]);
      } catch (err) {
        console.error("Errore caricamento favourites:", err);
      }
    }
    fetchFavourites();
  }, [user.email]);

  return (
    <div className="min-h-screen bg-black text-white px-6 pt-28">
      <h1 className="text-3xl font-bold mb-4">Profilo Utente</h1>
      <p className="text-lg mb-6">Email: {user.email}</p>

      <h2 className="text-2xl font-semibold mb-2">Album preferiti</h2>
      {favourites.length > 0 ? (
        <ul className="list-disc list-inside">
          {favourites.map((album) => (
            <li key={album.id}>{album.title}</li>
          ))}
        </ul>
      ) : (
        <p>Nessun album nei preferiti.</p>
      )}
    </div>
  );
}

export default Profile;
