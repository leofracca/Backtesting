## Progetto di Fondamenti di intelligenza artificiale

### Introduzione

Il progetto è un programma che esegue backtesting di una strategia di trading (applicata alla coppia Bitcoin/Dollaro). Per questo progetto viene usato Bitcoin (ma è facilmente adattabile anche alle altre criptovalute) in quanto il mercato delle criptovalute è sempre aperto e in generale è più semplice rispetto a quello tradizionale, permettendo così di evitare delle complessità che non hanno a che fare con l'obiettivo del progetto. Tuttavia, con qualche piccola modifica, questo programma funziona anche con le azioni del mercato tradizionale.



### Strategia

La strategia utilizzata viene spiegata [in questo video](https://www.youtube.com/watch?v=sbKTRVWppZY).
Riassumendolo utilizza tre indicatori:

- [MACD](https://en.wikipedia.org/wiki/MACD)
  - Calcolato usando 3 EMA rispettivamente di periodi 12, 26 e 9
  - La 12EMA e la 26EMA vengono sottratte tra di loro per calcolare la *MACD Line*
    - Molto sensibile al cambiamento del prezzo
  - Viene calcolata la *Signal Line*, cioè una 9EMA della MACD Line
    - Poco sensibile al cambiamento del prezzo
  - Quando la MACD Line e la Signal Line incrociano a rialzo (ovvero la MACD Line passa da sotto a sopra la Signal Line) è un segnale di acquisto, viceversa se incrociano a ribasso (la MACD Line passa da sopra a sotto la Signal Line) si genera un segnale di vendita
  - Opzionalmente è possibile introdurre anche un istogramma che rappresenta la differenza tra la MACD Line e la Signal Line, ma non è obbligatorio
  
  ![MACD](Docs/MACD.png)
  
- [Parabolic SAR (o PSAR)](https://en.wikipedia.org/wiki/Parabolic_SAR)
  - Rappresentato come una serie di punti
  - Se i punti sono sotto le candele, indicano un trend rialzista
  - Se i punti sono sopra le candele, indicano un trend ribassista
  
  ![PSAR](Docs/ParabolicSAR.png)
  
- [200EMA (Exponential Moving Average)](https://en.wikipedia.org/wiki/Moving_average)
  - Rappresenta una media mobile esponenziale con periodo 200
  - Se è sotto le candele, indica un trend rialzista
  - Se è sopra le candele, indica un trend ribassista
  
  ![200EMA](Docs/200EMA.png)

Osservando tutti i segnali dati da questi indicatori si aprono o chiudono le posizioni. In particolare si effettua un acquisto (si apre una posizione **long**) se 

1. il prezzo è sopra la 200EMA
2. c'è un crossover rialzista tra la MACD Line e la Signal Line
3. i valori di PSAR sono sotto le candele.

Viceversa si apre una posizione **short** se

1. il prezzo è sotto la 200EMA
2. c'è un crossover ribassista tra la MACD Line e la Signal Line
3. i valori di PSAR sono sopra le candele.

Inoltre, una volta creato l'ordine (sia esso long o short), vengono calcolati *stop loss* e *take profit*, ovvero dei prezzi target che, una volta raggiunti innescano degli ordini che chiudono la posizione.
Se il prezzo raggiunge il valore di take profit, allora significa che la posizione viene chiusa in profitto, se invece colpisce lo stop loss, allora significa che la posizione viene chiusa in perdita (lo stop loss viene messo per evitare di avere perdite troppo elevate).
Lo stop loss viene posto al valore attuale di PSAR, mentre il take profit viene posto facendo in modo che il rapporto del rischio guadagno-perdita sia 1:1. In formule:

<img src="https://render.githubusercontent.com/render/math?math=\large{take\_profit = price * 2 - PSAR}#gh-light-mode-only" />
<img src="https://render.githubusercontent.com/render/math?math=\large{stop\_loss = PSAR}#gh-light-mode-only" />
<img src="https://render.githubusercontent.com/render/math?math=\large{\color{white}take\_profit = price * 2 - PSAR}#gh-dark-mode-only" />
<img src="https://render.githubusercontent.com/render/math?math=\large{\color{white}stop\_loss = PSAR}#gh-dark-mode-only" />

In codice:

```python
def calculate_stop_loss_and_take_profit(self):
    # Calculate take profit and stop loss
    self.take_profit = self.dataclose[0] * 2 - self.psar[0]
    self.stop_loss = self.psar[0]
```

In `dataclose[0]` è presente il prezzo di chiusura dell'ultima candela, mentre in `psar[0]` l'ultimo valore calcolato di PSAR.

Il calcolo è lo stesso sia per posizioni long che posizioni short.

Una volta calcolati stop loss e take profit viene creato un ordine di tipo OCO (One Cancels the Other): è un insieme di ordini, dove il primo che viene eseguito cancella tutti gli altri. In questo caso gli ordini saranno 2: uno per chiudere la posizione allo stop loss e uno al take profit. Quando il prezzo raggiunge uno dei due valori, viene eseguito l'ordine corrispondente, chiusa la posizione e cancellato l'altro ordine.



### Osservazioni

Rispetto alla strategia mostrata nel video, è stato scelto di aggiungere un ulteriore check sulle oscillazioni del prezzo quando c'è una posizione aperta. Nella fase di testing si è notato che quando il prezzo supera (al ribasso se la posizione è long, al rialzo se è short) la 200EMA, poi la maggior parte delle volte raggiunge lo stop loss. Dunque nel caso in cui si verifichi questa situazione, conviene chiudere la posizione al prezzo corrente (cioè la 200EMA), invece di aspettare di raggiungere lo stop loss. In codice:

```python
# We have an open position
if not self.is_short_position:
    # Check if the price touches the 200EMA
    # If so, immediately close the position and delete the pending orders
    if self.data[0] < self.ema200[0]:
        # Long position LOSS
        self.sell(size=self.reward_long)
        self.cancel(self.oco_profit)
        self.cancel(self.oco_loss)
else:
    # Then check if the price touches the 200EMA
    # If so, immediately close the position and delete the pending orders
    if self.data[0] > self.ema200[0]:
        # Short position LOSS
        self.buy(size=self.reward_short)
        self.cancel(self.oco_profit)
        self.cancel(self.oco_loss)
```

Innanzitutto viene controllato se la posizione attuale è di tipo short o long. Se è long viene fatto un check sul prezzo: se è minore della 200EMA allora chiude la posizione (`self.sell(size=self.reward_long)`) e vengono cancellati gli ordini pendenti (quelli posti ai valori di stop loss e take profit, cioè gli ordini OCO). Se invece la posizione è short, si controlla se il prezzo diventa maggiore della 200EMA e, se lo è, viene chiusa la posizione e vengono cancellati gli ordini pendenti.

Questo controllo, sul lungo termine e in periodi di lateralizzazione del prezzo in cui non c'è né una spinta rialzista né ribassista, e si generano molti falsi segnali, si rivela abbastanza utile. Per esempio le seguenti immagini rappresentano rispettivamente una simulazione senza questo controllo e una con il controllo (data di inizio simulazione: 01-03-2022, data di fine simulazione: 17-03-2022):

![without_200EMA_stop](Docs/without_200EMA_stop.png)

![with_200EMA_stop](Docs/with_200EMA_stop.png)

Si noti come le perdite vengono contenute nel secondo caso (nel primo caso si termina con 94543.69\$, nel secondo con 99541.02\$, partendo in entrambi i casi da 100000\$).



### AIStrategy e Reward

Rispetto al video, viene fatta un'altra modifica. Infatti la strategia [AIStrategy](Strategies/AIStrategy.py) (si veda il paragrafo "Architettura del progetto") implementa un meccanismo basato su reward, utile per massimizzare il profitto e/o limitare le perdite. Il reward viene aggiornato ogni volta che viene chiusa una posizione e può aumentare o diminuire in base al fatto che la posizione sia stata chiusa con profitto o perdita. Il suo valore rappresenta anche l'amount da investire per il prossimo trade, che quindi sarà influenzato dalla storia dei trade passati (perché avranno modificato il reward, che rappresenta anche l'amount per questo trade).
Ogni trade produce un **reward**. *Più il reward è alto, più soldi verranno investiti nei futuri trade.*
*Se il trade produce un profitto, il reward complessivo cresce, altrimenti diminuisce.* L'idea che c'è dietro è che se tanti trade consecutivi producono profitto, allora la tendenza è generalmente rialzista (per posizioni long; ribassista se si parla di posizioni short), quindi conviene aumentare il carico per massimizzare il guadagno. Se invece tanti trade producono una perdita, potrebbe essere durante un periodo di lateralizzazione del prezzo, con molti falsi segnali e quindi conviene ridurre l'ammontare di soldi per trade per minimizzare il valore di altre possibili perdite.

Vengono usate due variabili per mantenere il valore dei reward: una per i trade long (`reward_long`) e una per quelli short (`reward_short`), entrambe inizializzate a 1. Queste vengono passate come parametro alla funzione per aprire una posizione (`self.buy(size=self.reward_long)` per posizioni long e `self.sell(size=self.reward_short)` per posizioni short) e rappresentano l'amount da investire (1 significa 1 Bitcoin).
`reward_long` viene modificata ad ogni trade di tipo long (cioè sopra la 200EMA): come spiegato precedentemente se la posizione viene aperta a un prezzo e chiusa a un prezzo più alto, `reward_long` cresce, altrimenti diminuisce.
`reward_short` viene modificata ad ogni trade di tipo short (cioè sotto la 200EMA): se la posizione viene aperta a un prezzo e chiusa a un prezzo più basso, `reward_short` cresce, altrimenti diminuisce.

Per esempio, supponendo che n trade passati (n >= 1) abbiano generato profitto (quindi il valore di reward sarà maggiore di 1, cioè il valore di default), probabilmente il periodo in considerazione ha una spinta rialzista abbastanza marcata, quindi potrebbe essere conveniente investire di più nel prossimo trade (cioè invece di comprare 1 Bitcoin, ne compra valore_reward, con valore_reward > 1), perché è probabile che anch'esso chiuderà in profitto. Viceversa se n trade passati (n >= 1) hanno generato delle perdite, probabilmente il periodo in considerazione non ha un momentum ben definito, quindi la probabilità di generare ulteriori perdite non è così bassa e conviene investire di meno nel prossimo trade (cioè invece di comprare 1 Bitcoin, ne compra valore_reward, con valore_reward < 1) per essere più cauti e nel peggiore dei casi contenere ulteriori perdite.

Il calcolo del reward è il seguente: per ogni posizione che viene chiusa, viene calcolata la differenza tra il prezzo di vendita e quello di acquisto e il risultato moltiplicato per un fattore per normalizzare il valore in base al prezzo della valuta su cui si stanno eseguendo i trade e a quanti soldi complessivi si possono investire (in questo caso è stato scelto 0.0001 come fattore). Poi si somma questo valore al valore attuale di `reward_long` se la posizione appena chiusa è di tipo long, altrimenti si somma al valore attuale di `reward_short` nel caso di posizioni short.
Di seguito il codice (per motivi di chiarezza non vengono riportate tutte le istruzioni di log o non strettamente necessarie al calcolo del reward, anche se sono presenti nel codice completo):

```python
# Check if an order has been completed
if order.status in [order.Completed]:
    if order.isbuy():
        self.buy_price = order.executed.price

        if self.is_short_position:
            # Update the reward for short positions
            self.reward_short += (self.sell_price - self.buy_price) * 0.0001

    elif order.issell():
        self.sell_price = order.executed.price

        if not self.is_short_position:
            # Update the reward for long positions
            self.reward_long += (self.sell_price - self.buy_price) * 0.0001
```

Inoltre se il prezzo scende sotto la 200EMA, `reward_long` viene resettata a 1, in quanto il momentum rialzista è terminato, quindi la prossima volta che il prezzo risalirà sopra la 200EMA, si riparte come se fosse il primo trade long. Lo stesso discorso vale in maniera speculare per `reward_short`.



### Strumenti utilizzati

Per questo progetto sono stati utilizzati i seguenti strumenti:

- [Backtrader](https://www.backtrader.com/) (con modulo Matplotlib per la visualizzazione dei grafici)
  - Libreria python che permette di fare backtesting applicando delle strategie di trading sui dati dell'asset su cui si intende fare trading
- [Binance API](https://binance-docs.github.io/apidocs/spot/en/#change-log)
  - API fornite dall'exchange Binance
  - Permettono di interagire col sistema per ricavare informazioni sui mercati o sull'account personale
  - Usate attraverso il wrapper per python [python-binance](https://github.com/sammchardy/python-binance) per ricavare i dati sui prezzi e generare il file [15min_BTC-USDT.csv](datas/15min_BTC-USDT.csv), che contiene tutti i prezzi della coppia BTC/USDT dal 01/01/2022 al 30/03/2022 con un timeframe di 15 minuti
    - Il formato del file è il seguente: `Datetime,Open,High,Low,Close,Volume`
  - Il codice per generare il file è [generate_data.py](Utils/generate_data.py)
    - Ovviamente è possibile modificare tutti i parametri come la coppia scelta, il periodo, il timeframe, ...



### Architettura del progetto

Il progetto è stato organizzato come segue:

- Lo script [backtest.py](backtest.py) è lo script da eseguire per far partire la simulazione
  - Si occupa di fare un parsing degli argomenti in input (attualmente possono essere solo la data di inizio e quella di fine, entrambe opzionali), di fare un setup iniziale, di eseguire la simulazione con la strategia selezionata e infine stampare i risultati e aprire una finestra con il grafico
- Nella cartella [Strategies](Strategies) sono presenti tutte le strategie implementate. Attualmente ce ne sono due: [AIStrategy](Strategies/AIStrategy.py), che rappresenta quella di questo progetto e testStrategy, che può essere visto semplicemente come un test iniziale per controllare che tutto funzioni correttamente (presa dalla documentazione di Backtrader)
  - *Si noti come, combinando questi primi due punti è possibile eseguire backtest.py usando strategie diverse, per esempio passando quella che si vuole testare come parametro, e compararle tra di loro*
  - La classe AIStrategy implementa i seguenti metodi (vengono riportati solo quelli derivati dalla superclasse Strategy di Backtrader):
    - log(): utile per vedere quando viene fatto un ordine, con prezzo, tipo, timestamp e profitto
    - \__init__(): viene eseguito all'inizio e serve per inizializzare i vari indicatori e variabili
    - next(): è il cuore della strategia. Viene eseguito a ogni candela e si occupa di effettuare i vari calcoli per capire cosa bisogna fare. Ad esempio calcola se c'è stato un crossover nel MACD, controlla se c'è una posizione aperta o meno e in base a ciò controlla se bisogna aprirne o chiuderne
- Lo script [generate_data.py](Utils/generate_data.py) all'interno della cartella Utils, serve per generare i dataset, come spiegato nel capitolo precedente
- In [datas](datas) sono contenuti i dataset, come spiegato nel capitolo precedente

***In questo modo il sistema è molto flessibile ed è potenzialmente possibile testarlo con strategie diverse, dataset diversi (anche con timeframe diversi), intervalli diversi, ...***



### Risultati

Di seguito vengono riportati alcuni grafici derivati dalle simulazioni di periodi diversi (e viene fatto un confronto tra la strategia che implementa il calcolo del reward e la stessa strategia senza reward).

- Dal 01-01-2022 al 08-01-2022 (1 settimana, parametri di default)![one week from 01-01-2022](Docs/one_week_from_01-01-2022.png)
- Dal 01-01-2022 al 08-01-2022 (1 settimana, parametri di default, no reward)![one week from 01-01-2022](Docs/one_week_from_01-01-2022_no_reward.png)
- Dal 01-01-2022 al 15-01-2022 (2 settimane)![two weeks from 01-01-2022](Docs/two_weeks_from_01-01-2022.png)
- Dal 01-01-2022 al 15-01-2022 (2 settimane, no reward)![two weeks from 01-01-2022](Docs/two_weeks_from_01-01-2022_no_reward.png)
- Dal 01-01-2022 al 01-02-2022 (1 mese)![one_month_from_01-01-2022](Docs/one_month_from_01-01-2022.png)
- Dal 01-01-2022 al 01-02-2022 (1 mese, no reward)![one_month_from_01-01-2022](Docs/one_month_from_01-01-2022_no_reward.png)
- Dal 01-01-2022 al 01-03-2022 (2 mesi)![two_months_from_01-01-2022](Docs/two_months_from_01-01-2022.png)
- Dal 01-01-2022 al 01-03-2022 (2 mesi, no reward)![two_months_from_01-01-2022](Docs/two_months_from_01-01-2022_no_reward.png)
- Dal 01-02-2022 al 08-02-2022 (1 settimana)![one_week_from_01-02-2022](Docs/one_week_from_01-02-2022.png)
- Dal 01-02-2022 al 08-02-2022 (1 settimana, no reward)![one_week_from_01-02-2022](Docs/one_week_from_01-02-2022_no_reward.png)
- Dal 01-03-2022 al 08-03-2022 (1 settimana)![one_week_from_01-03-2022](Docs/one_week_from_01-03-2022.png)
- Dal 01-03-2022 al 08-03-2022 (1 settimana, no reward)![one_week_from_01-03-2022](Docs/one_week_from_01-03-2022_no_reward.png)

Si può notare come questa strategia funzioni meglio nei periodi in cui il prezzo ha una direzione ben precisa rialzista o ribassista, ma meno quando è in lateralizzazione. Questo perché in quel caso gli indicatori generano molti più falsi segnali, e quindi i profitti sono molto bassi o peggio, si hanno delle perdite. Per esempio lo si vede molto bene nella prima immagine, dove la maggior parte delle giornate il prezzo rimane stabile (circa 48000\$) e passa molto spesso da sopra a sotto la 200EMA. L'equilibrio viene rotto molto bruscamente al quinto giorno al ribasso (si passa a 43000\$, generando infatti un profitto chiudendo una posizione short), ma poi ricomincia un nuovo equilibrio (tra i 43000\$ e i 41000\$). Tuttavia le potenziali perdite vengono minimizzate dall'osservazione fatta in precedenza, cioè di chiudere le posizioni se il prezzo tocca la 200EMA, che si è rivelata molto buona.
In generale il discorso appena fatto vale per tutti gli altri grafici e si noti quindi come, quando il prezzo rimane stabile in un certo range, le perdite sono molte di più rispetto a quando non lo è. Questo pattern si vede molto bene soprattutto nei grafici di più lungo periodo, come quello di 1 mese o quello di 2 mesi.

Per quello che riguarda il discorso sul reward, invece, si nota come in generale abbia funzionato relativamente bene. Infatti, tranne nei primi due esempi (dal 01-01-2022 al 08-01-2022 e dal 01-01-2022 al 15-01-2022), in cui c'è una perdita minima (in generale per periodi brevi la differenza è poca), la versione che implementa il calcolo del reward ha generato più profitto rispetto a quella che non lo tiene in considerazione. Le posizioni vengono aperte con investimenti maggiori, quindi sia i profitti sia le perdite hanno un valore maggiore rispetto alla versione senza reward se il reward precedente è maggiore di 1 (saranno minori se è minore di 1, anche se quest'ultimo capita raramente, in quanto se il reward diventa minore di 1 significa che probabilmente molto presto avverrà un cambio di trend; per esempio se il reward delle posizioni long diventa minore di 1, quasi sempre subito dopo il prezzo passa sotto la 200EMA e quindi si passa ad aprire posizioni short, con il relativo reward (si ricorda che sono 2 variabili separate)).
Tuttavia, se l'upper bound per prendere il profitto rimane sempre il take profit, il lower bound non è sempre lo stop loss, ma può diventare la 200EMA. Questo contribuisce molto ad avere profitti più alti e a contenere il prezzo delle perdite, generando così, maggiore profitto rispetto alla versione senza reward (si vedano per esempio i grafici delle due implementazioni di 1 mese e 2 mesi).
