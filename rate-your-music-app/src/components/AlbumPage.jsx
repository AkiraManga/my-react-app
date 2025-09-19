import React from "react";
import { useParams } from "react-router-dom";
import "../styles/AlbumPage.css";

const albums = {
  "ok-computer": {
    title: "OK Computer",
    artist: "Radiohead",
    year: 1997,
    cover: "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQtWGSIvVyEH5txLOSUeWDmU69a4x7H4AYXjA&s",
    genres: ["Alternative Rock", "Art Rock"],
    description:
      "OK Computer è il terzo album in studio dei Radiohead, pubblicato nel 1997. Considerato uno degli album più influenti degli anni '90.",
    tracks: [
      "Airbag",
      "Paranoid Android",
      "Subterranean Homesick Alien",
      "Exit Music (For a Film)",
      "Let Down",
      "Karma Police",
      "Electioneering",
      "Climbing Up the Walls",
      "No Surprises",
      "Lucky",
      "The Tourist"
    ]
  },
  // aggiungi altri album qui...
};

const AlbumPage = () => {
  const { id } = useParams();
  const album = albums[id];

  if (!album) {
    return <h2 className="not-found">Album non trovato 😢</h2>;
  }

  return (
    <div className="album-page">
      <div className="album-header">
        <img src={album.cover} alt={album.title} className="album-cover" />
        <div className="album-info">
          <h1>{album.title}</h1>
          <h2>{album.artist} ({album.year})</h2>
          <p><strong>Genere:</strong> {album.genres.join(", ")}</p>
          <p className="album-desc">{album.description}</p>
        </div>
      </div>

      <div className="tracklist">
        <h3>Tracklist</h3>
        <ol>
          {album.tracks.map((track, i) => (
            <li key={i}>{track}</li>
          ))}
        </ol>
      </div>
    </div>
  );
};

export default AlbumPage;
