import React, { useState, useEffect } from "react";

export default function Gallery3D() {
  const [locked, setLocked] = useState(false);
  const [imgs, setImgs] = useState([]);

  // toggle blocco rotazione
  const handleToggleLock = () => setLocked((prev) => !prev);

  // carico cover random da DynamoDB
  useEffect(() => {
    async function fetchCovers() {
      try {
        const configResp = await fetch("/config.json");
        const config = await configResp.json();

        // prendo tutti gli album
        const resp = await fetch(`${config.apiBaseUrl}albums`);
        if (!resp.ok) throw new Error("Errore API albums");

        const data = await resp.json();

        // mischiare gli album e prenderne 8
        const shuffled = data.sort(() => 0.5 - Math.random());
        const selected = shuffled.slice(0, 8);

        // costruire lista URL cover
        const covers = selected.map((album) =>
          album.cover.startsWith("http")
            ? album.cover
            : `https://rate-your-music101.s3.eu-west-3.amazonaws.com/${album.cover}`
        );

        setImgs(covers);
      } catch (err) {
        console.error("Errore caricamento cover:", err);
      }
    }

    fetchCovers();
  }, []);

  return (
    <>
      <style>{`
        .gallery3d-wrapper {
          margin: 0;
          height: 100vh;
          display: grid;
          place-items: center;
          background: #010101;
          overflow: hidden;
        }

        .gallery3d {
          position: relative;
          width: 250px;   /* dimensione lato pannelli */
          height: 250px;
          transform-style: preserve-3d;
          animation: gallery-rotate 35s linear infinite;
          cursor: pointer;
        }

        .gallery3d:hover { animation-play-state: paused; }

        .gallery3d.locked {
          animation-play-state: paused;
          cursor: grab;
        }

        @keyframes gallery-rotate {
          from { transform: perspective(1200px) rotateY(0deg); }
          to   { transform: perspective(1200px) rotateY(360deg); }
        }

        .gallery3d span {
          position: absolute;
          inset: 0;
          transform-origin: center;
          transform-style: preserve-3d;
          transform: rotateY(calc(var(--i) * 45deg)) translateZ(500px);
        }

        .gallery3d span img {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          object-fit: contain;     /* non taglia le immagini */
          background: #000;        /* riempie lo sfondo */
          border-radius: 8px;      /* opzionale */
          box-shadow: 0 0 15px rgba(0,0,0,0.6); /* opzionale */
        }
      `}</style>

      <section className="gallery3d-wrapper">
        <div
          className={`gallery3d${locked ? " locked" : ""}`}
          onClick={handleToggleLock}
          title={locked ? "Clicca per sbloccare" : "Clicca per bloccare"}
        >
          {imgs.map((url, idx) => (
            <span key={idx} style={{ "--i": idx + 1 }}>
              <img src={url} alt={`cover-${idx + 1}`} />
            </span>
          ))}
        </div>
      </section>
    </>
  );
}
