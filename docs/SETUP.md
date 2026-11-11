# Configurazione — Fase 0

Guida per preparare credenziali e ambiente cloud. Alla fine lo script di verifica deve dare 3 OK.

**Dove farlo.** I passaggi segnati **[computer]** conviene farli da computer: la console di Google Cloud e le impostazioni dell'ambiente cloud sono scomode dal telefono, e la chiave JSON va aperta e copiata per intero. Quelli segnati **[telefono]** vanno bene anche dal telefono.

| Passo | Cosa | Dove |
| --- | --- | --- |
| 1 | Progetto Google Cloud, API e fatturazione | computer |
| 2 | Foglio Google e account di servizio | telefono + computer |
| 3 | Chiave Places API (New) con limiti | computer |
| 4 | Token Meta, copiato dal sistema creator | telefono |
| 5 | Ambiente cloud: segreti, domini, script di avvio | computer |
| 6 | Verifica | telefono |

I cinque segreti che servono alla fine:

| Variabile | Cosa contiene | Da dove |
| --- | --- | --- |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Tutto il file JSON della chiave dell'account di servizio | Passo 2 |
| `SHEET_ID` | Link del foglio (o solo il suo ID) | Passo 2 |
| `PLACES_API_KEY` | Chiave API limitata a Places API (New) | Passo 3 |
| `IG_ACCESS_TOKEN` | Token Meta del sistema creator | Passo 4 |
| `IG_USER_ID` | ID numerico dell'account Instagram professionale (inizia di solito con 1784) | Passo 4 |

Si usa il tuo account Google attuale. Progetto, foglio e account di servizio sono nuovi e separati da quelli del sistema creator.

---

## 1. Progetto Google Cloud [computer]

1. Apri <https://console.cloud.google.com> con il tuo account Google.
2. In alto, selettore dei progetti → **Nuovo progetto** → nome `consulenza-pmi` → **Crea**. Controlla che in alto sia selezionato il nuovo progetto.
3. Menu → **API e servizi** → **Libreria**. Cerca e attiva:
   - **Google Sheets API**;
   - **Places API (New)**. Attenzione: quella con "(New)", non "Places API".
4. Menu → **Fatturazione** → collega un account di fatturazione al progetto. Places la richiede anche se resti nella quota gratuita. Puoi usare un account di fatturazione che hai già.

## 2. Foglio Google e account di servizio

### 2a. Crea il foglio [telefono]

1. Nell'app Fogli Google crea un foglio vuoto, per esempio `Consulenza PMI - Dati`.
2. Copia il link del foglio (Condividi → Copia link): è il valore di `SHEET_ID`. Va bene il link intero; il codice ne estrae l'ID.
3. Non creare le schede: le crea lo script di verifica (Attività, Contatti e Verifica).

### 2b. Crea l'account di servizio e la chiave [computer]

1. Nella console, progetto `consulenza-pmi` → Menu → **IAM e amministrazione** → **Account di servizio** → **Crea account di servizio**.
2. Nome `consulenza-foglio` → **Crea e continua**. Ruoli e accessi: salta, non servono → **Fine**.
3. Apri l'account appena creato → scheda **Chiavi** → **Aggiungi chiave** → **Crea nuova chiave** → **JSON** → **Crea**. Si scarica un file `.json`.
4. Quel file è una password: non metterlo nel repository e non mandarlo in chat. Dopo il passo 5 cancellalo dai download (o tienilo solo in un gestore di password).
5. Copia l'indirizzo email dell'account di servizio, del tipo `consulenza-foglio@consulenza-pmi.iam.gserviceaccount.com` (è anche la voce `client_email` nel file).

Se la creazione della chiave è bloccata da un criterio dell'organizzazione, il progetto è dentro un Workspace: con un account Gmail personale non succede.

### 2c. Condividi il foglio con l'account di servizio [telefono]

1. Apri il foglio → **Condividi** → incolla l'email dell'account di servizio.
2. Ruolo **Editor**, togli la spunta a "Invia notifica" → **Condividi**.

## 3. Chiave Places API (New) con limiti [computer]

### 3a. Crea e limita la chiave

1. Menu → **API e servizi** → **Credenziali** → **Crea credenziali** → **Chiave API**.
2. Apri la chiave (Modifica):
   - nome: `places-consulenza`;
   - **Restrizioni delle applicazioni**: Nessuna. Le sessioni cloud non hanno un indirizzo IP fisso, quindi una restrizione per IP bloccherebbe le chiamate;
   - **Restrizioni API**: Limita chiave → scegli solo **Places API (New)**;
   - **Salva**.
3. Copia la chiave: è il valore di `PLACES_API_KEY`.

### 3b. Limiti di spesa

Il budget manda solo avvisi; il blocco vero sono le quote.

1. **Quote.** Menu → **API e servizi** → **Places API (New)** → **Quote e limiti di sistema**. Per le richieste di **Text Search** e di **Place Details** imposta un limite basso: se c'è la quota al giorno, 100 richieste al giorno; se ci sono solo quote al minuto, 10 al minuto. Spunta la quota → **Modifica** → nuovo valore → **Invia**.
2. **Budget.** Menu → **Fatturazione** → **Budget e avvisi** → **Crea budget**: progetto `consulenza-pmi`, importo 5 €, avvisi al 50%, 90% e 100% per email.

### Costi

Places fa pagare ogni richiesta in base al campo più costoso tra quelli chiesti. Il sistema chiede sito, telefono, valutazione e numero di recensioni, che sono campi "Enterprise":

- **Text Search Enterprise**: 1.000 richieste gratuite al mese, poi circa 35 $ ogni 1.000;
- **Place Details Enterprise**: 1.000 richieste gratuite al mese, poi circa 20 $ ogni 1.000.

Ogni ricerca restituisce fino a 20 attività. Per le 30-100 attività della Fase 2 servono qualche decina di richieste al mese, dentro la quota gratuita. Le quote gratuite valgono per tipo di richiesta e si azzerano ogni mese. I prezzi vengono da fonti di novembre 2026: confermali su <https://developers.google.com/maps/billing-and-pricing/pricing>.

## 4. Token Meta dal sistema creator [telefono]

Non serve una nuova app Meta: si riusa quella del sistema creator e si copiano solo i due valori.

1. Apri le impostazioni dell'ambiente cloud del sistema creator e copia i valori di:
   - il token di accesso → diventa `IG_ACCESS_TOKEN`;
   - l'ID dell'account Instagram professionale → diventa `IG_USER_ID`. È un numero (di solito inizia con 1784), non il nome utente.

   Se lì le variabili hanno nomi diversi, copia i valori corrispondenti.
2. Controlla la scadenza del token su <https://developers.facebook.com/tools/debug/accesstoken>: incolla il token → **Debug** → riga **Expires**.
   - **Never**: non scade;
   - una data: è un token di lunga durata (circa 60 giorni). Quando lo rinnovi per il sistema creator, aggiornalo anche qui. Mettiti un promemoria una settimana prima della data.
3. I limiti di chiamate dell'app Meta sono condivisi tra i due sistemi. Con i volumi previsti (decine di account al giorno) non è un problema.

## 5. Ambiente cloud [computer]

Un ambiente nuovo, solo per questo repository, con segreti e domini propri.

1. Su <https://claude.ai/code>: selettore dell'ambiente (sotto la casella del messaggio) → **Nuovo ambiente** (*New environment*). Nome `sistema-consulenza`, ambiente personale (non condiviso).
2. **Accesso alla rete** (*Network access*): **Limitato** (*Limited*), con la spunta su "Consenti gestori di pacchetti" (*Allow package managers*) (copre pypi.org e files.pythonhosted.org; github.com è già consentito). In **Domini consentiti** (*Allowed domains*), uno per riga:

   ```
   places.googleapis.com
   graph.facebook.com
   oauth2.googleapis.com
   sheets.googleapis.com
   ```

   Nella Fase 2 Claude legge i siti delle attività: se la lettura viene bloccata dalla rete limitata, passa ad accesso completo per questo ambiente.
3. **Variabili d'ambiente** (*Environment variables*), formato `.env`, una per riga. La chiave JSON va tra apici singoli perché contiene virgolette doppie e va a capo: apri il file del passo 2b con un editor di testo, copia tutto e incollalo tra i due apici.

   ```
   SHEET_ID=https://docs.google.com/spreadsheets/d/.../edit
   PLACES_API_KEY=la-chiave-del-passo-3
   IG_ACCESS_TOKEN=il-token-del-passo-4
   IG_USER_ID=17841...
   GOOGLE_SERVICE_ACCOUNT_JSON='{
     "type": "service_account",
     ...tutto il resto del file...
   }'
   ```

4. **Script di avvio** (*Setup script*; installa i pacchetti di `requirements.txt` quando parte una sessione):

   ```bash
   pip install "requests>=2.31" "PyYAML>=6.0" "google-auth>=2.30" "pytest>=8.0"
   ```

5. Salva. Da qui in poi scegli l'ambiente `sistema-consulenza` per le sessioni e per le attività programmate di questo repository.

**Nota sulla sicurezza.** Le variabili d'ambiente sono salvate in chiaro nelle impostazioni dell'ambiente e ogni sessione che usa l'ambiente le può leggere: per questo l'ambiente deve restare personale e usato solo per questo repository. Il codice non stampa mai i valori dei segreti.

## 6. Verifica [telefono]

1. Apri una nuova sessione su questo repository, nell'ambiente `sistema-consulenza`.
2. Chiedi a Claude di eseguire, con il nome utente di un account Instagram **professionale** (aziendale o creator):

   ```bash
   python scripts/verifica.py nome_utente_instagram
   ```

   Opzioni: `--settore` (predefinito `officina`) e `--zona` (predefinita `San Giovanni in Persiceto`, deve essere in `config/zone.yaml`).
3. Risultato atteso: `OK Foglio Google`, `OK Places`, `OK Instagram`, e `Passi riusciti: 3 su 3`.
4. Nel foglio trovi le schede **Attività** e **Contatti** con le intestazioni e la scheda **Verifica** con una riga di prova. La scheda Verifica puoi cancellarla.

### Se qualcosa non va

| Messaggio | Causa probabile | Cosa fare |
| --- | --- | --- |
| `<VARIABILE>: MANCANTE` | Variabile non salvata o sessione aperta prima di salvarla | Controlla il passo 5 e apri una sessione nuova |
| `GOOGLE_SERVICE_ACCOUNT_JSON non contiene un JSON valido` | JSON copiato a metà o senza apici | Ricopia tutto il file tra apici singoli |
| Foglio: errore 403 o 404 | Foglio non condiviso o `SHEET_ID` sbagliato | Passo 2c; ricopia il link del foglio |
| `... API has not been used in project ...` | API non attivata | Passo 1, punto 3 |
| Places: `API key not valid` | Chiave copiata male | Ricopia la chiave del passo 3 |
| Places: errore 403 con `PERMISSION_DENIED` | Fatturazione non collegata o chiave limitata a un'altra API | Passo 1 punto 4, passo 3a |
| Instagram: token scaduto o non valido | Token rinnovato nel sistema creator | Ricopia il token (passo 4) |
| Instagram: account inesistente o non professionale | Il nome utente è un account personale | Prova con un account aziendale |
| `ConnectionError` o `ProxyError` | Dominio non consentito | Passo 5, punto 2 |
