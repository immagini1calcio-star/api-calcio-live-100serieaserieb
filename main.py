import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Dizionario dei campionati richiesti mappati con i codici ufficiali del feed di ESPN
LEGHES_ESPN = {
    "serie-a": "ita.1",
    "serie-b": "ita.2",
    "coppa-italia": "ita.coppa",
    "premier-league": "eng.1",
    "la-liga": "esp.1",
    "ligue-1": "fra.1",
    "bundesliga": "ger.1",
    "champions-league": "uefa.champions",
    "europa-league": "uefa.europa",
    "conference-league": "uefa.conf",
    "nazionale-italiana": "fifa.friendly",
    "amichevoli": "club.friendly"
}

@app.route('/risultati', methods=['GET'])
def get_soccer_scores():
    # Legge la lega dall'URL (es: /risultati?lega=serie-b). Se omesso mostra la Serie A.
    lega_scelta = request.args.get('lega', 'serie-a')
    codice_espn = LEGHES_ESPN.get(lega_scelta, "ita.1")
    
    # Endpoint pubblico globale di ESPN: senza scadenze, token o blocchi
    url = f"https://espn.com{codice_espn}/scoreboard"
    
    try:
        response = requests.get(url)
        dati = response.json()
        
        partite_elaborate = []
        
        # ESPN organizza i match della giornata dentro la lista "events"
        for event in dati.get("events", []):
            competition_info = event["competitions"]
            competitors = competition_info["competitors"]
            
            # Identifichiamo la squadra in casa e quella ospite
            casa = next(t for t in competitors if t["homeAway"] == "home")
            ospiti = next(t for t in competitors if t["homeAway"] == "away")
            
            # Estraiamo gli eventi live del match (gol, ammoniti, espulsi, rigori)
            dettagli_eventi = competition_info.get("details", [])
            
            # Estraiamo le formazioni ufficiali se già caricate nel sistema
            formazione_casa = [p["player"]["displayName"] for p in casa.get("lineup", [])]
            formazione_ospiti = [p["player"]["displayName"] for p in ospiti.get("lineup", [])]
            
            info = {
                "id_partita": event.get("id"),
                "campionato": lega_scelta.upper(),
                "data_orario_utc": event.get("date"), # Orario di inizio del match
                "stato_testo": event["status"]["type"]["shortDetail"], # Es: "1H 25'" o "Finale"
                "fase_partita": event["status"]["type"]["name"], # STATUS_SCHEDULED, STATUS_IN_PROGRESS, STATUS_FINAL
                "casa": {
                    "nome": casa["team"]["displayName"],
                    "logo": casa["team"].get("logo"),
                    "gol": casa.get("score", "0"),
                    "formazione": formazione_casa if len(formazione_casa) > 0 else "Non ancora disponibile"
                },
                "ospiti": {
                    "nome": ospiti["team"]["displayName"],
                    "logo": ospiti["team"].get("logo"),
                    "gol": ospiti.get("score", "0"),
                    "formazione": formazione_ospiti if len(formazione_ospiti) > 0 else "Non ancora disponibile"
                },
                # In questo elenco ESPN inserisce i marcatori con minuto ed espulsioni
                "cronologia_live": dettagli_eventi
            }
            partite_elaborate.append(info)
            
        return jsonify({
            "lega_richiesta": lega_scelta,
            "totale_partite_trovate": len(partite_elaborate),
            "risultati": partite_elaborate
        })
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Assicura compatibilità con Vercel Serverless
app = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

