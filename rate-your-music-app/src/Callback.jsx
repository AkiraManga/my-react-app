import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

function Callback() {
  const { search } = useLocation();
  const navigate = useNavigate();
  const [config, setConfig] = useState(null);

  // 1. Carica config.json all'avvio
  useEffect(() => {
    fetch("/config.json")
      .then((res) => res.json())
      .then((data) => {
        console.log("✅ Config caricata:", data);
        setConfig(data);
      })
      .catch((err) => console.error("❌ Errore caricando config.json:", err));
  }, []);

  // 2. Quando config è disponibile, processa il codice
  useEffect(() => {
    const code = new URLSearchParams(search).get("code");
    if (code && config) {
      console.log("✅ Codice ricevuto:", code);

      // Chiama la tua Lambda auth/callback
      fetch(`${config.apiBaseUrl}auth/callback?code=${code}`)
        .then(async (res) => {
          console.log("📡 Status risposta:", res.status);
          const text = await res.text();
          console.log("📦 Risposta raw:", text);

          try {
            const data = JSON.parse(text);

            // 🔑 Salva i token in localStorage
            localStorage.setItem("id_token", data.id_token);
            localStorage.setItem("access_token", data.access_token);
            localStorage.setItem("refresh_token", data.refresh_token);

            console.log("✅ Token salvati in localStorage");

            // 🔄 redirect forzato → rimonta Header e mostra Logout
            window.location.href = "/";
            // se preferisci SPA senza full reload, usa navigate("/")
          } catch (err) {
            console.error("❌ Errore parse JSON:", err);
          }
        })
        .catch((err) => console.error("❌ Errore fetch:", err));
    }
  }, [config, search, navigate]);

  return <div>Login in corso...</div>;
}

export default Callback;
