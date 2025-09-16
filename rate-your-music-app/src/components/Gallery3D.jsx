import React, { useState } from 'react';

/* ---------------- immagini ---------------- */
const imgs = [
  'https://images4.alphacoders.com/678/thumb-1920-678317.jpg',
  'https://images5.alphacoders.com/653/653698.jpg',
  'https://images6.alphacoders.com/803/thumb-1920-803643.png',
  'https://images.alphacoders.com/785/thumb-1920-785833.png',
  'https://images6.alphacoders.com/749/thumb-1920-749966.png',
  'https://images4.alphacoders.com/761/thumb-1920-761076.png',
  'https://images.alphacoders.com/682/thumb-1920-682570.png',
  'https://images4.alphacoders.com/866/thumb-1920-866812.png',
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
