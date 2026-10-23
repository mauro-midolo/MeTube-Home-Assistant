# MeTube per Home Assistant

Scarica musica (e video) con [yt-dlp](https://github.com/yt-dlp/yt-dlp) direttamente da Home Assistant, e ascoltala con Music Assistant.

Il repository contiene due pezzi, utilizzabili insieme o separatamente:

- **App MeTube** (`metube/`): fa girare [MeTube](https://github.com/alexta69/metube) dentro Home Assistant OS, con il pannello nella barra laterale. I download "solo audio" finiscono in `/media/musica`, dove Music Assistant li legge come file locali.
- **Integrazione MeTube** (`custom_components/metube/`): collega Home Assistant a MeTube (l'app qui sopra o un MeTube in Docker su un altro server) e aggiunge:
  - l'azione **`metube.download`**, da usare in automazioni, script e dashboard;
  - il campo **Link da scaricare** (`text.metube_link_da_scaricare`): incolli il link, premi Invio e parte il download con le opzioni predefinite;
  - i sensori **Coda**, **Completati**, **Falliti** e **Ultimo download**;
  - il pulsante **Svuota completati** (toglie le voci dall'elenco, non cancella i file);
  - gli eventi **`metube_download_finished`** e **`metube_download_failed`**, uno per ogni download che finisce, con `url`, `title`, `filename`, `folder`, `format` ed `error`.

## 1. Installare l'app

1. **Impostazioni → App → Store delle app** → menu ⋮ → **Repository**.
2. Aggiungi `https://github.com/mauro-midolo/metube-home-assistant` e chiudi.
3. Cerca **MeTube**, installa (la prima volta Home Assistant costruisce l'immagine: qualche minuto) e avvia.
4. Attiva **Mostra nella barra laterale**.

Opzioni e dettagli: [metube/DOCS.md](metube/DOCS.md).

## 2. Collegare Music Assistant

In Music Assistant: **Impostazioni → Provider → Aggiungi → Filesystem (disco locale)**, percorso `/media/musica`.

## 3. Installare l'integrazione

**Con HACS:** HACS → menu ⋮ → **Repository personalizzati** → aggiungi `https://github.com/mauro-midolo/metube-home-assistant`, categoria **Integrazione** → scarica **MeTube** → riavvia Home Assistant.

**A mano:** copia `custom_components/metube` in `/config/custom_components/metube` (es. con Studio Code Server) e riavvia.

Poi **Impostazioni → Dispositivi e servizi → Aggiungi integrazione → MeTube**. Se l'app è installata, l'indirizzo viene proposto da solo (es. `http://xxxxxxxx-metube:8081`); per un MeTube in Docker su un'altra macchina usa `http://IP:8081`.

In **Configura** scegli le opzioni predefinite: tipo (audio/video), formato (mp3, m4a, opus, flac…), qualità e sottocartella.

## Esempi

Scaricare un brano in FLAC in una sottocartella:

```yaml
action: metube.download
data:
  url: https://www.youtube.com/watch?v=XXXXXXXXXXX
  format: flac
  folder: Jazz
```

Scheda per la dashboard:

```yaml
type: entities
title: Scarica musica
entities:
  - entity: text.metube_link_da_scaricare
  - entity: sensor.metube_coda
  - entity: sensor.metube_ultimo_download
  - entity: sensor.metube_falliti
  - entity: button.metube_svuota_completati
```

Notifica sul telefono quando un brano è pronto:

```yaml
alias: Brano scaricato
triggers:
  - trigger: state
    entity_id: sensor.metube_ultimo_download
conditions:
  - condition: template
    value_template: "{{ trigger.to_state.state not in ['unknown', 'unavailable', ''] }}"
actions:
  - action: notify.mobile_app_IL_TUO_TELEFONO
    data:
      message: "Pronto in Music Assistant: {{ trigger.to_state.state }}"
```

Avvisare su Telegram quando un download finisce:

```yaml
triggers:
  - trigger: event
    event_type: metube_download_finished
actions:
  - action: telegram_bot.send_message
    data:
      entity_id: notify.telegram_bot_XXXXXXXX
      message: "Pronta in Music Assistant: {{ trigger.event.data.title }}"
```

L'`url` negli eventi è quello canonico registrato da MeTube (es. `https://www.youtube.com/watch?v=...` anche se avevi mandato un link `youtu.be`).

I nomi delle entità dipendono dalla lingua di Home Assistant al momento della configurazione; controllali in **Dispositivi e servizi → MeTube**.

## Note

- Scarica solo contenuti che hai il diritto di scaricare (brani liberi, Creative Commons, materiale tuo).
- Quando YouTube cambia qualcosa, di solito basta aggiornare yt-dlp: imposta `nightly_update_time` nell'app oppure attendi la versione successiva dell'app.

## Sviluppo

```bash
pip install pytest-homeassistant-custom-component
pytest
```
