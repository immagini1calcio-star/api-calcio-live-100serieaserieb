import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

# Mappa corretta dei campionati con i codici del feed di ESPN
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
    lega_scelta = request.args.get('lega', 'serie-a')
    codice_espn = LEGHES_ESPN.get(lega_scelta, "ita.1")
    
    url = f"https://espn.com{codice_espn}/scoreboard"
    
    try:
        response = requests.get(url)
        dati = response.json()
        
        partite_elaborate = []
        
        for event in dati.get("events", []):
            competition_info = event["competitions"][0]
            competitors = competition_info["competitors"]
            
            casa = next(t for t in competitors if t["homeAway"] == "home")
            ospiti = next(t for t in competitors if t["homeAway"] == "away")
            
            dettagli_eventi = competition_info.get("details", [])
            
            formazione_casa = [p["player"]["displayName"] for p in casa.get("lineup", [])]
            formazione_ospiti = [p["player"]["displayName"] for p in ospiti.get("lineup", [])]
            
            info = {
                "id_partita": event.get("id"),
                "campionato": lega_scelta.upper(),
                "data_orario_utc": event.get("date"),
                "stato_testo": event["status"]["type"]["shortDetail"],
                "fase_partita": event["status"]["type"]["name"],
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

app = app

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
