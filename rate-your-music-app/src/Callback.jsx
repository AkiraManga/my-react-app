import { useEffect } from "react";
import { useLocation } from "react-router-dom";

function Callback() {
  const { search } = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(search);
    const code = params.get("code");

    if (code) {
      fetch(`https://twkdj82lu1.execute-api.eu-west-3.amazonaws.com/prod/auth/callback?code=${code}`)
        .then(res => res.json())
        .then(tokens => {
          console.log("Tokens ricevuti:", tokens);
          if (tokens.access_token) {
            localStorage.setItem("access_token", tokens.access_token);
          } else {
            console.error("Errore: Nessun access_token ricevuto", tokens);
          }
        })
        .catch(err => console.error("Errore fetch:", err));
    }
  }, [search]);

  return <div>Login in corso...</div>;
}

export default Callback;
