import React, { useState } from 'react';

/* ---------------- immagini ---------------- */
const imgs = [
  'https://www.lafeltrinelli.it/images/0888837168618_0_0_0_0_0.jpg',
  'https://i.scdn.co/image/ab67616d00001e022a64ebd96553453a516892ba',
  'https://upload.wikimedia.org/wikipedia/commons/6/60/Charli_XCX_-_Brat_%28album_cover%29.png',
  'https://m.media-amazon.com/images/I/71FM257lYjL._UF894,1000_QL80_.jpg',
  'https://m.media-amazon.com/images/I/71EYmWxcmdL._UF894,1000_QL80_.jpg',
  'https://www.musictraks.com/wp-content/uploads/2025/04/i-cani.jpg',
  'https://m.media-amazon.com/images/I/618nkXxBxsL.jpg',
  'https://www.lafeltrinelli.it/images/0602577230936_0_0_0_0_0.jpg',
];

/* ---------------- componente ---------------- */
export default function Gallery3D() {
  const [locked, setLocked] = useState(false);

  /* clic sul cilindro → toggle blocco */
  const handleToggleLock = () => setLocked((prev) => !prev);

  return (
    <>
      {/* ---------- stile incorporato ---------- */}
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
          width: 300px;
          height: 200px;
          transform-style: preserve-3d;
          animation: gallery-rotate 35s linear infinite;
          cursor: pointer;               /* indica che si può cliccare */
        }

        /* pausa quando passo il mouse */
        .gallery3d:hover { animation-play-state: paused; }

        /* pausa permanente se bloccato */
        .gallery3d.locked {
          animation-play-state: paused;
          cursor: grab;                  /* feedback “bloccato” */
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
          transform: rotateY(calc(var(--i) * 45deg)) translateZ(380px);
        }

        .gallery3d span img {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
          object-fit: cover;
        }
      `}</style>

      {/* ---------- markup ---------- */}
      <section className="gallery3d-wrapper">
        <div
          className={`gallery3d${locked ? ' locked' : ''}`}
          onClick={handleToggleLock}
          title={locked ? 'Clicca per sbloccare' : 'Clicca per bloccare'}
        >
          {imgs.map((url, idx) => (
            <span key={idx} style={{ '--i': idx + 1 }}>
              <img src={url} alt={`slide-${idx + 1}`} />
            </span>
          ))}
        </div>
      </section>
    </>
  );
}
