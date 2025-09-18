import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";

function Callback() {
  const { search } = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const params = new URLSearchParams(search);
    const code = params.get("code");

    if (code) {
      console.log("✅ Codice ricevuto:", code);

      fetch(
        `https://jyqw4r3nck.execute-api.eu-west-3.amazonaws.com/prod/auth/callback?code=${code}`
      )
        .then(async (res) => {
          console.log("📡 Status risposta:", res.status);

          const text = await res.text();
          console.log("📦 Risposta raw:", text);

          try {
            const json = JSON.parse(text);
            return json;
          } catch (e) {
            console.error("❌ Errore parse JSON:", e);
            return {};
          }
        })
        .then((tokens) => {
          console.log("🔑 Tokens ricevuti:", tokens);

          if (tokens.access_token) {
            sessionStorage.setItem("access_token", tokens.access_token);
            if (tokens.id_token) {
              sessionStorage.setItem("id_token", tokens.id_token);
            }
            if (tokens.refresh_token) {
              sessionStorage.setItem("refresh_token", tokens.refresh_token);
            }

            window.dispatchEvent(new Event("storage"));
            //navigate("/");
          } else {
            console.error("⚠️ Errore: Nessun access_token ricevuto", tokens);
          }
        })
        .catch((err) => console.error("🔥 Errore fetch:", err));
    } else {
      console.warn("⚠️ Nessun codice trovato nell'URL");
    }
  }, [search, navigate]);

  return <div>Login in corso...</div>;
}

export default Callback;
