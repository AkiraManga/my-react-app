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
    if (code && config?.apiBaseUrl) {
      console.log("✅ Codice ricevuto:", code);

      fetch(`${config.apiBaseUrl}auth/callback?code=${code}`)
        .then(async (res) => {
          console.log("📡 Status risposta:", res.status);
          const text = await res.text();
          console.log("📦 Risposta raw:", text);

          try {
            const data = JSON.parse(text);
            sessionStorage.setItem("id_token", data.id_token);
            sessionStorage.setItem("access_token", data.access_token);
            sessionStorage.setItem("refresh_token", data.refresh_token);

            console.log("✅ Token salvati in sessionStorage");

            // 🔔 avvisa Header.jsx che lo stato è cambiato
            window.dispatchEvent(new Event("storage"));

            navigate("/");
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
