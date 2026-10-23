# MeTube

[MeTube](https://github.com/alexta69/metube) è un'interfaccia web per yt-dlp: incolli un link (YouTube o uno degli altri siti supportati da yt-dlp), scegli "Audio" e il file finisce nella cartella che indichi.

L'app salva i file in `/media`, la stessa cartella che legge l'app Music Assistant: i brani compaiono nella libreria senza SMB né altri server.

## Configurazione

| Opzione | Predefinito | A cosa serve |
|---|---|---|
| `audio_dir` | `/media/musica` | Download "solo audio". Deve stare sotto `/media` o `/share`. |
| `video_dir` | `/media/video` | Download video. |
| `output_template` | `%(title)s.%(ext)s` | Nome del file. Con `%(artist,uploader)s/%(title)s.%(ext)s` ottieni una cartella per artista. |
| `output_template_playlist` | `%(playlist_title)s/%(title)s.%(ext)s` | Nome dei file scaricati da una playlist. |
| `max_concurrent_downloads` | `3` | Download in parallelo. |
| `theme` | `auto` | Tema dell'interfaccia. |
| `ytdl_options` | (vuoto) | Opzioni extra di yt-dlp in JSON. |
| `nightly_update_time` | (vuoto) | Ora `HH:MM` in cui aggiornare yt-dlp alla nightly. Attivalo se YouTube smette di funzionare tra un aggiornamento e l'altro. |

La porta `8081` è chiusa di default: l'interfaccia si usa dal pannello "MeTube" nella barra laterale. Assegnale un numero solo se vuoi raggiungere MeTube dall'esterno di Home Assistant (es. dall'estensione del browser); in quel caso MeTube non ha login, quindi tienila solo in rete locale.

## Music Assistant

1. Apri Music Assistant → **Impostazioni** → **Provider** → **Aggiungi**.
2. Scegli **Filesystem (disco locale)**.
3. Come percorso inserisci `/media/musica` (o il valore di `audio_dir`).

Music Assistant rilegge la cartella periodicamente; per vedere subito un brano appena scaricato usa **Sincronizza** sul provider.

## Integrazione

Nello stesso repository c'è l'integrazione **MeTube** (cartella `custom_components/metube`): aggiunge un'azione `metube.download`, una casella "Link da scaricare" e i sensori della coda. Le istruzioni sono nel README del repository.

## Dati e backup

La coda e la cronologia stanno nella cartella dell'app e finiscono nei backup di Home Assistant. I file scaricati stanno in `/media` e seguono le impostazioni di backup della cartella Media.
