# Configurazione — Fase 0

Guida per preparare credenziali e ambiente cloud. Alla fine lo script di verifica deve dare 3 OK.

**Dove farlo.** I passaggi segnati **[computer]** conviene farli da computer: la console di Google Cloud e le impostazioni dell'ambiente cloud sono scomode dal telefono, e la chiave JSON va aperta e copiata per intero. Quelli segnati **[telefono]** vanno bene anche dal telefono.

| Passo | Cosa | Dove |
| --- | --- | --- |
| 1 | Progetto Google Cloud, API e fatturazione | computer |
| 2 | Foglio Google e account di servizio | telefono + computer |
| 3 | Chiave Places API (New) con limiti | computer |
| 4 | App Meta, token Instagram e ID dell'account | telefono + computer |
| 5 | Ambiente cloud: aggiungere i segreti (domini e script già impostati) | computer |
| 6 | Verifica | telefono |

I cinque segreti che servono alla fine:

| Variabile | Cosa contiene | Da dove |
| --- | --- | --- |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Tutto il file JSON della chiave dell'account di servizio | Passo 2 |
| `SHEET_ID` | Link del foglio (o solo il suo ID) | Passo 2 |
| `PLACES_API_KEY` | Chiave API limitata a Places API (New) | Passo 3 |
| `IG_ACCESS_TOKEN` | Token Meta di lunga durata (circa 60 giorni) | Passo 4 |
| `IG_USER_ID` | ID numerico dell'account Instagram professionale (inizia di solito con 1784) | Passo 4 |

Si usa il tuo account Google attuale. Progetto, foglio e account di servizio sono nuovi e separati da quelli del sistema creator; l'app Meta invece sarà condivisa.

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

### Se la creazione della chiave è bloccata [computer]

Il messaggio "Creazione di chiavi del service account disabilitata" (`iam.disableServiceAccountKeyCreation`) vuol dire che l'account con cui sei nella console fa parte di un'organizzazione (un Workspace) che blocca queste chiavi. Si sblocca solo per questo progetto:

1. Selettore in alto → scegli l'**organizzazione**, non il progetto → **IAM e amministrazione** → **IAM** → **Concedi l'accesso**: il tuo account, ruolo **Amministratore policy dell'organizzazione** (*Organization Policy Administrator*) → **Salva**. Puoi farlo solo se sei amministratore dell'organizzazione.
2. Selettore in alto → progetto `consulenza-pmi` → **IAM e amministrazione** → **Policy dell'organizzazione** → filtra per `disableServiceAccountKeyCreation`. Possono esserci due voci, `iam.disableServiceAccountKeyCreation` e `iam.managed.disableServiceAccountKeyCreation`. Per ognuna: **Gestisci policy** → **Sostituisci la policy dell'elemento padre** (*Override parent's policy*) → applicazione **Off** → **Imposta policy**.
3. Aspetta qualche minuto e ricrea la chiave (punto 3 qui sopra).
4. Creata la chiave, rimetti il blocco: stesse voci → **Gestisci policy** → **Eredita la policy dell'elemento padre** (*Inherit parent's policy*) → **Imposta policy**. La chiave già creata continua a funzionare; il blocco vale solo per le chiavi nuove.

Se non sei amministratore dell'organizzazione, o al punto 2 non puoi sostituire la policy: rifai i passi 1, 2b e 3 con il tuo account Gmail personale, che non ha organizzazione e quindi non ha questo blocco.

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

## 4. App Meta e token Instagram

Il sistema creator non è ancora attivo, quindi l'app Meta si crea adesso, con un nome generico. Quando attiverai il sistema creator userà la stessa app: basterà copiare lì gli stessi due valori, `IG_ACCESS_TOKEN` e `IG_USER_ID`.

Cosa serve:

- un tuo account Instagram **professionale** (aziendale o creator). È l'account da cui il sistema legge i profili delle attività; le attività non vedono niente;
- una **Pagina Facebook** collegata a quell'account;
- il tuo profilo Facebook personale, che diventa il tuo account sviluppatore.

L'app resta in modalità sviluppo e la usi solo tu, che ne sei amministratore: non servono la verifica dell'azienda né la revisione dell'app da parte di Meta.

### 4a. Account Instagram professionale e Pagina Facebook [telefono]

1. App Instagram → profilo → menu ☰ → **Impostazioni e privacy** → **Tipo di account e strumenti** → **Passa a un account professionale** → Azienda o Creator. Se l'account è già professionale, salta.
2. Profilo → **Modifica profilo** → **Pagina** → collega una Pagina Facebook esistente o creane una. Va bene una Pagina semplice con il nome della consulenza. La voce **Pagina** c'è solo nell'app per telefono e solo per gli account professionali: su instagram.com dal computer non compare.

   Da computer si collega dal lato Facebook:
   - se non hai una Pagina, creala su <https://www.facebook.com/pages/create>;
   - su facebook.com passa al profilo della Pagina (foto in alto a destra → nome della Pagina);
   - **Impostazioni e privacy** → **Impostazioni** → **Account collegati** → **Instagram** → **Collega account** e accedi con il tuo Instagram.

   Se la voce non c'è, usa Meta Business Suite: <https://business.facebook.com> → **Impostazioni** → **Account Instagram** → **Collega**.

   Attenzione: aggiungere Instagram al **Centro gestione account** (*Accounts Center*) non basta. Serve il collegamento con la Pagina.

   La Pagina deve essere gestita, con controllo completo, dallo stesso profilo Facebook con cui crei l'app e il token (passi 4b e 4c). Chi visita la Pagina non vede il tuo profilo personale.

### 4b. Account sviluppatore e app [computer]

1. Apri <https://developers.facebook.com> con il tuo profilo Facebook → **Inizia** (*Get started*) e completa la registrazione. Se sei già registrato, salta.
2. Vai su <https://developers.facebook.com/apps> → **Crea app**. La procedura chiede queste cose, non sempre in quest'ordine:
   - **nome dell'app**: generico e senza le parole Instagram, Facebook o Meta, che Meta rifiuta. Per esempio `Analisi Social MC`. Email di contatto: la tua;
   - **caso d'uso**: **Altro** (*Other*);
   - **tipo di app**: **Business**;
   - **portfolio business**: salta (*Non collegare ora*). Serve solo per pubblicare l'app, e qui non si pubblica.

   Poi **Crea app**; può chiederti la password di Facebook.
3. Nella dashboard dell'app:
   - **Aggiungi prodotto** → **Instagram** → **Configura** (*Set up*) → scegli **Configurazione dell'API con accesso tramite Facebook** (*API setup with Facebook login*);
   - **Aggiungi prodotto** → **Facebook Login for Business** → **Configura**, lasciando le impostazioni predefinite.
4. Lascia l'app **In sviluppo** (*Development*): non pubblicarla.

### 4c. Token e ID dell'account [computer]

1. Apri il **Graph API Explorer**: <https://developers.facebook.com/tools/explorer>.
2. Nel pannello a destra: **Meta App** → la tua app; **User or Page** → **Get User Access Token**.
3. In **Permissions** aggiungi questi permessi:
   - `pages_show_list`
   - `pages_read_engagement`
   - `instagram_basic`
   - `instagram_manage_insights`
   - `business_management` e `ads_read`: servono se la Pagina è gestita da Meta Business Suite. Nel dubbio aggiungili.
4. **Generate Access Token**. Nella finestra di Facebook continua con il tuo profilo; quando ti chiede a cosa dare accesso, seleziona **la tua Pagina** e **il tuo account Instagram** → **Salva**.
5. **ID dell'account.** Nel campo della richiesta scrivi `me/accounts?fields=name,instagram_business_account` → **Submit**. Nella risposta, sotto la tua Pagina, il numero in `instagram_business_account` → `id` è `IG_USER_ID` (di solito inizia con 1784).
   - Risposta vuota (`"data": []`): rigenera il token (punto 4) selezionando la Pagina, con `business_management` tra i permessi.
   - Manca `instagram_business_account`: Instagram non è collegato a quella Pagina (passo 4a).
6. **Prova.** Nel campo della richiesta scrivi `IG_USER_ID?fields=business_discovery.username(NOME){followers_count,media_count}`. Al posto di `IG_USER_ID` metti il numero del punto 5; al posto di `NOME`, il nome utente di un'attività con profilo aziendale. Poi **Submit**: se compaiono follower e numero di post, funziona.
7. **Token di lunga durata.** Il token nel campo **Access Token** dura poche ore:
   - copialo e apri <https://developers.facebook.com/tools/debug/accesstoken>;
   - incollalo → **Debug** → in fondo alla pagina **Estendi token d'accesso** (*Extend Access Token*);
   - copia il nuovo token che compare: è `IG_ACCESS_TOKEN`;
   - controlla con **Debug** sul nuovo token che **Expires** sia tra circa 60 giorni.
8. **Promemoria.** Mettiti un promemoria tra 50 giorni. Per rinnovare il token rifai i punti 1-4 e 7, poi aggiorna `IG_ACCESS_TOKEN` nell'ambiente (passo 5), e anche nell'ambiente del sistema creator quando ci sarà. Se il token scade, la verifica e le attività programmate danno l'errore "token scaduto o non valido".

Il token dà accesso in lettura alla tua Pagina e al tuo Instagram: trattalo come una password e non incollarlo in chat. I limiti di chiamate dell'app saranno condivisi con il sistema creator; con i volumi previsti (decine di account al giorno) non è un problema.

## 5. Ambiente cloud [computer]

L'ambiente personale `sistema-consulenza` è già creato, solo per questo repository, con rete e script di avvio impostati (punti 2 e 4). Resta da aggiungere le variabili (punto 3).

1. Su <https://claude.ai/code>: selettore dell'ambiente (sotto la casella del messaggio) → ambiente `sistema-consulenza` → icona delle impostazioni.
2. **Accesso alla rete** (*Network access*), già impostato: **Limitato** (*Limited*), con la spunta su "Consenti gestori di pacchetti" (*Allow package managers*) (copre pypi.org e files.pythonhosted.org; github.com è già consentito). In **Domini consentiti** (*Allowed domains*):

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

4. **Script di avvio** (*Setup script*), già impostato; installa i pacchetti di `requirements.txt` quando parte una sessione:

   ```bash
   pip install "requests>=2.31" "PyYAML>=6.0" "google-auth>=2.30" "pytest>=8.0"
   ```

5. Salva le variabili. Da qui in poi scegli l'ambiente `sistema-consulenza` per le sessioni e per le attività programmate di questo repository.

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
| Instagram: token scaduto o non valido | Token di 60 giorni scaduto o copiato male | Rinnova il token (passo 4c, punti 7-8) |
| Instagram: account inesistente o non professionale | Il nome utente è un account personale | Prova con un account aziendale |
| `ConnectionError` o `ProxyError` | Dominio non consentito | Passo 5, punto 2 |
