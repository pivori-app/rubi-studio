//+------------------------------------------------------------------+
//|                                        RubiStudioConnector.mq5   |
//|                        Copyright 2025, Rubi Studio               |
//|                                      https://rubi-studio.com     |
//+------------------------------------------------------------------+
#property copyright "Copyright 2025, Rubi Studio"
#property link      "https://rubi-studio.com"
#property version   "3.00"
#property description "Connecteur MT5 pour Rubi Studio Backend"
#property strict

//--- Includes
#include <Trade\Trade.mqh>
#include <JAson.mqh>

//+------------------------------------------------------------------+
//| Configuration du Backend                                          |
//+------------------------------------------------------------------+
input group "=== Backend Configuration ==="
input string BackendURL = "https://api.rubi-studio.com";  // URL du backend
input string APIToken = "";                                // Token API (obligatoire)
input int RequestTimeout = 10000;                         // Timeout requête (ms)

input group "=== Trading Configuration ==="
input int CheckInterval = 5000;                           // Intervalle de vérification (ms)
input bool EnableAutoTrading = true;                      // Activer le trading automatique
input double MaxRiskPercent = 2.0;                        // Risque maximum par trade (%)
input int MaxOpenPositions = 5;                           // Nombre max de positions ouvertes
input bool SendSignalsOnly = false;                       // Mode signaux uniquement (pas d'exécution)

input group "=== Logging Configuration ==="
input bool EnableDetailedLogs = true;                     // Logs détaillés
input bool LogToFile = true;                              // Sauvegarder les logs dans un fichier

//+------------------------------------------------------------------+
//| Variables globales                                                |
//+------------------------------------------------------------------+
CTrade trade;
datetime lastCheck = 0;
datetime lastPing = 0;
int fileHandle = INVALID_HANDLE;
bool isConnected = false;
string sessionId = "";

// Statistiques
int totalSignalsSent = 0;
int totalSignalsReceived = 0;
int totalOrdersExecuted = 0;
int totalErrors = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                    |
//+------------------------------------------------------------------+
int OnInit()
{
   //--- Vérifier le token API
   if(StringLen(APIToken) == 0)
   {
      Alert("ERREUR: APIToken non configuré!");
      Print("ERREUR: Veuillez configurer votre token API dans les paramètres");
      return(INIT_FAILED);
   }
   
   //--- Vérifier la connexion internet
   if(!TerminalInfoInteger(TERMINAL_CONNECTED))
   {
      Alert("ERREUR: Pas de connexion internet!");
      return(INIT_FAILED);
   }
   
   //--- Vérifier que le trading automatique est autorisé
   if(EnableAutoTrading && !TerminalInfoInteger(TERMINAL_TRADE_ALLOWED))
   {
      Alert("ATTENTION: Le trading automatique n'est pas autorisé dans le terminal!");
      Print("Veuillez activer 'Autoriser le trading automatique' dans les options");
   }
   
   //--- Ouvrir le fichier de log
   if(LogToFile)
   {
      string filename = "RubiStudio_" + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)) + "_" + 
                        TimeToString(TimeCurrent(), TIME_DATE) + ".log";
      fileHandle = FileOpen(filename, FILE_WRITE|FILE_TXT|FILE_ANSI);
      if(fileHandle != INVALID_HANDLE)
      {
         WriteLog("=== Rubi Studio Connector Started ===");
         WriteLog("Account: " + IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN)));
         WriteLog("Broker: " + AccountInfoString(ACCOUNT_COMPANY));
         WriteLog("Backend URL: " + BackendURL);
      }
   }
   
   //--- Initialiser la connexion avec le backend
   if(!ConnectToBackend())
   {
      Print("ERREUR: Impossible de se connecter au backend");
      WriteLog("ERROR: Failed to connect to backend");
      return(INIT_FAILED);
   }
   
   //--- Configuration du trade manager
   trade.SetExpertMagicNumber(20251023);
   trade.SetDeviationInPoints(10);
   trade.SetTypeFilling(ORDER_FILLING_FOK);
   
   Print("✅ Rubi Studio Connector initialized successfully");
   WriteLog("Connector initialized successfully");
   WriteLog("Auto Trading: " + (EnableAutoTrading ? "ENABLED" : "DISABLED"));
   WriteLog("Max Risk: " + DoubleToString(MaxRiskPercent, 2) + "%");
   WriteLog("Max Positions: " + IntegerToString(MaxOpenPositions));
   
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                  |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   //--- Envoyer les statistiques finales
   SendDisconnectNotification();
   
   //--- Afficher les statistiques
   Print("=== Session Statistics ===");
   Print("Signals Sent: ", totalSignalsSent);
   Print("Signals Received: ", totalSignalsReceived);
   Print("Orders Executed: ", totalOrdersExecuted);
   Print("Errors: ", totalErrors);
   
   WriteLog("=== Session Statistics ===");
   WriteLog("Signals Sent: " + IntegerToString(totalSignalsSent));
   WriteLog("Signals Received: " + IntegerToString(totalSignalsReceived));
   WriteLog("Orders Executed: " + IntegerToString(totalOrdersExecuted));
   WriteLog("Errors: " + IntegerToString(totalErrors));
   WriteLog("=== Rubi Studio Connector Stopped ===");
   
   //--- Fermer le fichier de log
   if(fileHandle != INVALID_HANDLE)
   {
      FileClose(fileHandle);
      fileHandle = INVALID_HANDLE;
   }
   
   Print("Rubi Studio Connector stopped. Reason: ", GetUninitReasonText(reason));
}

//+------------------------------------------------------------------+
//| Expert tick function                                              |
//+------------------------------------------------------------------+
void OnTick()
{
   //--- Vérifier l'intervalle de temps
   if(TimeCurrent() - lastCheck < CheckInterval / 1000)
      return;
   
   lastCheck = TimeCurrent();
   
   //--- Ping le backend toutes les 30 secondes
   if(TimeCurrent() - lastPing >= 30)
   {
      PingBackend();
      lastPing = TimeCurrent();
   }
   
   //--- Envoyer les positions ouvertes au backend
   SendPositionsToBackend();
   
   //--- Vérifier les nouveaux signaux depuis le backend
   if(EnableAutoTrading && !SendSignalsOnly)
   {
      CheckNewSignals();
   }
   
   //--- Mettre à jour les statistiques du compte
   UpdateAccountInfo();
}

//+------------------------------------------------------------------+
//| Connecter au backend                                              |
//+------------------------------------------------------------------+
bool ConnectToBackend()
{
   CJAVal json;
   json["account_number"] = IntegerToString(AccountInfoInteger(ACCOUNT_LOGIN));
   json["broker"] = AccountInfoString(ACCOUNT_COMPANY);
   json["server"] = AccountInfoString(ACCOUNT_SERVER);
   json["balance"] = AccountInfoDouble(ACCOUNT_BALANCE);
   json["equity"] = AccountInfoDouble(ACCOUNT_EQUITY);
   json["currency"] = AccountInfoString(ACCOUNT_CURRENCY);
   
   string response;
   int httpCode = SendHTTPRequest("POST", "/api/v1/mt5/connect", json.Serialize(), response);
   
   if(httpCode == 200 || httpCode == 201)
   {
      CJAVal responseJson;
      if(responseJson.Deserialize(response))
      {
         sessionId = responseJson["session_id"].ToStr();
         isConnected = true;
         Print("✅ Connected to backend. Session ID: ", sessionId);
         WriteLog("Connected to backend. Session ID: " + sessionId);
         return true;
      }
   }
   
   Print("❌ Failed to connect to backend. HTTP Code: ", httpCode);
   WriteLog("ERROR: Failed to connect. HTTP Code: " + IntegerToString(httpCode));
   return false;
}

//+------------------------------------------------------------------+
//| Ping le backend                                                   |
//+------------------------------------------------------------------+
void PingBackend()
{
   CJAVal json;
   json["session_id"] = sessionId;
   json["timestamp"] = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
   json["balance"] = AccountInfoDouble(ACCOUNT_BALANCE);
   json["equity"] = AccountInfoDouble(ACCOUNT_EQUITY);
   json["margin_free"] = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   
   string response;
   int httpCode = SendHTTPRequest("POST", "/api/v1/mt5/ping", json.Serialize(), response);
   
   if(httpCode == 200)
   {
      if(EnableDetailedLogs)
         WriteLog("Ping successful");
   }
   else
   {
      WriteLog("WARNING: Ping failed. HTTP Code: " + IntegerToString(httpCode));
      isConnected = false;
      // Tenter de se reconnecter
      ConnectToBackend();
   }
}

//+------------------------------------------------------------------+
//| Envoyer les positions au backend                                  |
//+------------------------------------------------------------------+
void SendPositionsToBackend()
{
   int total = PositionsTotal();
   
   if(total == 0)
      return;
   
   CJAVal positions;
   positions["session_id"] = sessionId;
   positions["timestamp"] = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
   positions["positions"].Add(NULL);  // Initialiser le tableau
   
   for(int i = 0; i < total; i++)
   {
      ulong ticket = PositionGetTicket(i);
      if(ticket > 0)
      {
         CJAVal position;
         position["ticket"] = IntegerToString(ticket);
         position["symbol"] = PositionGetString(POSITION_SYMBOL);
         position["type"] = PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY ? "BUY" : "SELL";
         position["volume"] = PositionGetDouble(POSITION_VOLUME);
         position["open_price"] = PositionGetDouble(POSITION_PRICE_OPEN);
         position["current_price"] = PositionGetDouble(POSITION_PRICE_CURRENT);
         position["sl"] = PositionGetDouble(POSITION_SL);
         position["tp"] = PositionGetDouble(POSITION_TP);
         position["profit"] = PositionGetDouble(POSITION_PROFIT);
         position["swap"] = PositionGetDouble(POSITION_SWAP);
         position["commission"] = 0.0;  // MT5 ne fournit pas la commission directement
         position["open_time"] = TimeToString((datetime)PositionGetInteger(POSITION_TIME), TIME_DATE|TIME_SECONDS);
         
         positions["positions"].Add(position);
      }
   }
   
   string response;
   int httpCode = SendHTTPRequest("POST", "/api/v1/trading/positions/update", positions.Serialize(), response);
   
   if(httpCode == 200 || httpCode == 201)
   {
      if(EnableDetailedLogs)
         WriteLog("Positions updated: " + IntegerToString(total) + " positions sent");
   }
   else
   {
      WriteLog("ERROR: Failed to update positions. HTTP Code: " + IntegerToString(httpCode));
      totalErrors++;
   }
}

//+------------------------------------------------------------------+
//| Vérifier les nouveaux signaux                                     |
//+------------------------------------------------------------------+
void CheckNewSignals()
{
   string response;
   int httpCode = SendHTTPRequest("GET", "/api/v1/trading/signals/pending?session_id=" + sessionId, "", response);
   
   if(httpCode != 200)
      return;
   
   CJAVal signals;
   if(!signals.Deserialize(response))
      return;
   
   int signalCount = ArraySize(signals["signals"]);
   
   for(int i = 0; i < signalCount; i++)
   {
      CJAVal signal = signals["signals"][i];
      
      string symbol = signal["symbol"].ToStr();
      string signalType = signal["signal_type"].ToStr();
      double volume = signal["volume"].ToDbl();
      double entryPrice = signal["entry_price"].ToDbl();
      double sl = signal["stop_loss"].ToDbl();
      double tp = signal["take_profit"].ToDbl();
      int signalId = signal["id"].ToInt();
      
      //--- Exécuter le signal
      bool success = ExecuteSignal(signalId, symbol, signalType, volume, entryPrice, sl, tp);
      
      if(success)
      {
         totalOrdersExecuted++;
         totalSignalsReceived++;
         WriteLog("Signal executed: " + symbol + " " + signalType + " " + DoubleToString(volume, 2));
      }
      else
      {
         totalErrors++;
         WriteLog("ERROR: Failed to execute signal: " + symbol + " " + signalType);
      }
   }
}

//+------------------------------------------------------------------+
//| Exécuter un signal                                                |
//+------------------------------------------------------------------+
bool ExecuteSignal(int signalId, string symbol, string signalType, double volume, 
                   double entryPrice, double sl, double tp)
{
   //--- Vérifier le nombre de positions ouvertes
   if(PositionsTotal() >= MaxOpenPositions)
   {
      WriteLog("WARNING: Max positions reached. Signal ignored.");
      NotifySignalStatus(signalId, "REJECTED", "Max positions reached");
      return false;
   }
   
   //--- Vérifier le symbole
   if(!SymbolInfoInteger(symbol, SYMBOL_SELECT))
   {
      WriteLog("ERROR: Symbol not found: " + symbol);
      NotifySignalStatus(signalId, "REJECTED", "Symbol not found");
      return false;
   }
   
   //--- Calculer le volume avec risk management
   double calculatedVolume = CalculateVolume(symbol, sl, MaxRiskPercent);
   if(calculatedVolume > 0 && calculatedVolume < volume)
      volume = calculatedVolume;
   
   //--- Normaliser le volume
   double minVolume = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MIN);
   double maxVolume = SymbolInfoDouble(symbol, SYMBOL_VOLUME_MAX);
   double volumeStep = SymbolInfoDouble(symbol, SYMBOL_VOLUME_STEP);
   
   volume = MathMax(minVolume, MathMin(maxVolume, volume));
   volume = MathFloor(volume / volumeStep) * volumeStep;
   
   //--- Exécuter l'ordre
   bool success = false;
   ulong ticket = 0;
   
   if(signalType == "BUY")
   {
      success = trade.Buy(volume, symbol, 0, sl, tp, "RubiStudio #" + IntegerToString(signalId));
      ticket = trade.ResultOrder();
   }
   else if(signalType == "SELL")
   {
      success = trade.Sell(volume, symbol, 0, sl, tp, "RubiStudio #" + IntegerToString(signalId));
      ticket = trade.ResultOrder();
   }
   else if(signalType == "CLOSE_BUY" || signalType == "CLOSE_SELL")
   {
      success = ClosePositionBySymbol(symbol);
   }
   
   //--- Notifier le backend
   if(success)
   {
      NotifySignalStatus(signalId, "EXECUTED", "Order ticket: " + IntegerToString(ticket));
      Print("✅ Signal executed: ", symbol, " ", signalType, " Volume: ", volume, " Ticket: ", ticket);
   }
   else
   {
      string error = "Error: " + IntegerToString(GetLastError()) + " - " + trade.ResultRetcodeDescription();
      NotifySignalStatus(signalId, "REJECTED", error);
      Print("❌ Failed to execute signal: ", symbol, " ", signalType, " Error: ", error);
   }
   
   return success;
}

//+------------------------------------------------------------------+
//| Calculer le volume avec risk management                           |
//+------------------------------------------------------------------+
double CalculateVolume(string symbol, double sl, double riskPercent)
{
   if(sl <= 0)
      return 0;
   
   double balance = AccountInfoDouble(ACCOUNT_BALANCE);
   double riskAmount = balance * riskPercent / 100.0;
   
   double ask = SymbolInfoDouble(symbol, SYMBOL_ASK);
   double slDistance = MathAbs(ask - sl);
   
   if(slDistance == 0)
      return 0;
   
   double tickValue = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_VALUE);
   double tickSize = SymbolInfoDouble(symbol, SYMBOL_TRADE_TICK_SIZE);
   
   double volume = riskAmount / (slDistance / tickSize * tickValue);
   
   return volume;
}

//+------------------------------------------------------------------+
//| Fermer une position par symbole                                   |
//+------------------------------------------------------------------+
bool ClosePositionBySymbol(string symbol)
{
   for(int i = PositionsTotal() - 1; i >= 0; i--)
   {
      ulong ticket = PositionGetTicket(i);
      if(PositionGetString(POSITION_SYMBOL) == symbol)
      {
         return trade.PositionClose(ticket);
      }
   }
   return false;
}

//+------------------------------------------------------------------+
//| Notifier le statut du signal                                      |
//+------------------------------------------------------------------+
void NotifySignalStatus(int signalId, string status, string message)
{
   CJAVal json;
   json["signal_id"] = signalId;
   json["status"] = status;
   json["message"] = message;
   json["timestamp"] = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
   
   string response;
   SendHTTPRequest("POST", "/api/v1/trading/signals/" + IntegerToString(signalId) + "/status", json.Serialize(), response);
}

//+------------------------------------------------------------------+
//| Mettre à jour les informations du compte                          |
//+------------------------------------------------------------------+
void UpdateAccountInfo()
{
   static datetime lastUpdate = 0;
   
   // Mettre à jour toutes les 60 secondes
   if(TimeCurrent() - lastUpdate < 60)
      return;
   
   lastUpdate = TimeCurrent();
   
   CJAVal json;
   json["session_id"] = sessionId;
   json["balance"] = AccountInfoDouble(ACCOUNT_BALANCE);
   json["equity"] = AccountInfoDouble(ACCOUNT_EQUITY);
   json["margin"] = AccountInfoDouble(ACCOUNT_MARGIN);
   json["margin_free"] = AccountInfoDouble(ACCOUNT_MARGIN_FREE);
   json["margin_level"] = AccountInfoDouble(ACCOUNT_MARGIN_LEVEL);
   json["profit"] = AccountInfoDouble(ACCOUNT_PROFIT);
   
   string response;
   SendHTTPRequest("POST", "/api/v1/mt5/account/update", json.Serialize(), response);
}

//+------------------------------------------------------------------+
//| Envoyer une notification de déconnexion                           |
//+------------------------------------------------------------------+
void SendDisconnectNotification()
{
   CJAVal json;
   json["session_id"] = sessionId;
   json["timestamp"] = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
   json["total_signals_sent"] = totalSignalsSent;
   json["total_signals_received"] = totalSignalsReceived;
   json["total_orders_executed"] = totalOrdersExecuted;
   json["total_errors"] = totalErrors;
   
   string response;
   SendHTTPRequest("POST", "/api/v1/mt5/disconnect", json.Serialize(), response);
}

//+------------------------------------------------------------------+
//| Envoyer une requête HTTP                                          |
//+------------------------------------------------------------------+
int SendHTTPRequest(string method, string endpoint, string jsonData, string &response)
{
   char data[];
   char result[];
   string headers;
   string url = BackendURL + endpoint;
   
   //--- Convertir le JSON en tableau de bytes
   if(StringLen(jsonData) > 0)
      StringToCharArray(jsonData, data, 0, StringLen(jsonData));
   
   //--- Préparer les headers
   headers = "Content-Type: application/json\r\n";
   headers += "Authorization: Bearer " + APIToken + "\r\n";
   headers += "User-Agent: MT5-RubiStudio-Connector/3.0\r\n";
   
   //--- Envoyer la requête
   ResetLastError();
   int httpCode = WebRequest(
      method,
      url,
      headers,
      RequestTimeout,
      data,
      result,
      headers
   );
   
   //--- Convertir la réponse
   if(ArraySize(result) > 0)
      response = CharArrayToString(result);
   
   //--- Gérer les erreurs
   if(httpCode == -1)
   {
      int error = GetLastError();
      Print("WebRequest error: ", error);
      WriteLog("ERROR: WebRequest failed. Error code: " + IntegerToString(error));
      
      if(error == 4060)  // ERR_FUNCTION_NOT_ALLOWED
      {
         Print("ERREUR: WebRequest non autorisé. Ajoutez l'URL dans Tools -> Options -> Expert Advisors");
         Alert("WebRequest non autorisé! Ajoutez ", BackendURL, " dans les options");
      }
      
      totalErrors++;
   }
   
   return httpCode;
}

//+------------------------------------------------------------------+
//| Écrire dans le fichier de log                                     |
//+------------------------------------------------------------------+
void WriteLog(string message)
{
   if(!LogToFile || fileHandle == INVALID_HANDLE)
      return;
   
   string timestamp = TimeToString(TimeCurrent(), TIME_DATE|TIME_SECONDS);
   FileWrite(fileHandle, timestamp + " | " + message);
   FileFlush(fileHandle);
}

//+------------------------------------------------------------------+
//| Obtenir le texte de la raison de désinitialisation                |
//+------------------------------------------------------------------+
string GetUninitReasonText(int reason)
{
   switch(reason)
   {
      case REASON_PROGRAM:     return "Expert stopped by user";
      case REASON_REMOVE:      return "Expert removed from chart";
      case REASON_RECOMPILE:   return "Expert recompiled";
      case REASON_CHARTCHANGE: return "Chart symbol or period changed";
      case REASON_CHARTCLOSE:  return "Chart closed";
      case REASON_PARAMETERS:  return "Input parameters changed";
      case REASON_ACCOUNT:     return "Account changed";
      case REASON_TEMPLATE:    return "Template applied";
      case REASON_INITFAILED:  return "Initialization failed";
      case REASON_CLOSE:       return "Terminal closed";
      default:                 return "Unknown reason";
   }
}
//+------------------------------------------------------------------+

