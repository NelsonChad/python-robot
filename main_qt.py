from PyQt5 import uic, QtWidgets, QtGui, QtCore, QtSvg
from concurrent.futures import process
from time import sleep
from fileinput import filename
from iqoptionapi.stable_api import IQ_Option
from datetime import datetime, timedelta
from pathlib import Path
from colorama import init, Fore, Back
import pathlib
import os
import sys
from pyqtspinner.spinner import WaitingSpinner

import sched, time, json
import threading
import subprocess #system proccess

from myToast import QToaster
from csv_file import CSV


class Window :

    init(autoreset=True) #colorama
    name =''
    spinner = None #to loading spinner

    operations = 0

    FILEPATH = None
    FILENAME = None

    OPERATED = []

    PAYOUT = 80
    MERCADO = 1
    ENTRADA = 0 # to save the entry 
    BANCA = 100 #total money
    TAKEPROFIT_PERC = 0 #percentage to risc in day $
    DAY_LOSS_TARGET = 0 #money $ to risc in day according in percentage
    SOROS_HAND = 0 #value of soros hand
    TRADE_PROFIT = 0 #profit earned trade

    TODAY_PROFIT = 0

    INROW_WINS = 0
    INROW_LOSES = 0

    WINS = 0
    LOSES = 0
    EMPATE = 0

    API = None
    
    '''
        USER INTERFACE finctions  begin here
    '''

    app = QtWidgets.QApplication([])
    tela = uic.loadUi("roboUI.ui")
    loginUI = uic.loadUi("login.ui")

    PROFILE = None
    def __init__(self):
        '''
            DEFENITIONS OF THE APP
        '''
        #self.loginUI.label_logo.setGeometry(50, 50, 50, 50)
        pixmap = QtGui.QPixmap(os.getcwd() + "/resources\logo.png")
        self.loginUI.label_logo.setPixmap(pixmap)
        self.loginUI.label_logo.resize(103,100)
        self.loginUI.label_logo.setScaledContents(True)
        print('PATH: '+os.getcwd() )

        self.disable()
        self.tela.comboBoxAccountType.addItems(['DEMO','REAL'])
        self.tela.comboBoxSorosLevel.addItems(['2','3'])
        self.loginUI.lineEditPassword.setEchoMode(QtWidgets.QLineEdit.Password)

        #Debug
        self.loginUI.textEditEmail.setText('tonnylson.chad@gmail.com')
        self.loginUI.lineEditPassword.setText('nelsonchad1234')
        self.tela.textEditStoploss.setPlainText('20')

        #Init tables
        self.tela.tableWidgetOps.setColumnCount(5)
        self.tela.tableWidgetOps.setHorizontalHeaderLabels(["PARIDADE", "EXPIRAÇÃO", "LUCRO",'DIREÇÃO','RESULTADO'])
        stylesheet = "::section{Background-color: rgb(0, 168, 132);color: rgb(255,255,255);}"
        self.tela.tableWidgetOps.horizontalHeader().setStyleSheet(stylesheet)

        '''
        self.tela.tableWidgetOps.setColumnWidth(0,215) # and also lower values
        self.tela.tableWidgetOps.setColumnWidth(1,216) # and also lower values
        self.tela.tableWidgetOps.setColumnWidth(2,216) # and also lower values
        self.tela.tableWidgetOps.setColumnWidth(3,216) # and also lower values
        self.tela.tableWidgetOps.setColumnWidth(4,216) # and also lower values
        '''

        self.tela.tableWidgetBooked.setColumnCount(3)
        self.tela.tableWidgetBooked.setHorizontalHeaderLabels(["HORÁRIO","PARIDADE", "EXPIRAÇÃO"])
        stylesheet = "::section{Background-color: rgb(0, 168, 132);color: rgb(255,255,255);}"
        self.tela.tableWidgetBooked.horizontalHeader().setStyleSheet(stylesheet)

        self.tela.tableWidgetBooked.setColumnWidth(0,200) # and also lower values
        self.tela.tableWidgetBooked.setColumnWidth(1,200) # and also lower values
        self.tela.tableWidgetBooked.setColumnWidth(2,200) # and also lower values
        self.tela.tableWidgetBooked.setColumnWidth(3,150) # and also lower values

        #BOTOES
        self.loginUI.pushButtonLogin.clicked.connect(self.loginCall)
        self.tela.pushButtonStartTrade.clicked.connect(self.startAutoTrade)
        self.tela.pushButtonOpenLogin.clicked.connect(self.loginPage)
        self.tela.pushButtonExit.clicked.connect(self.stopAutoTrade)

        self.tela.comboBoxAccountType.currentIndexChanged.connect(self.on_combobox_changed)
        self.tela.textEditStoploss.textChanged.connect(self.text_changed)

        self.updateScreen()
        self.get_uuid()

    '''
        METHODS OF THE APP
    '''
    def get_uuid(self):
        print('GETING UUID')
        windows = ""
        print('UUID- WINDOWS:', windows, ' LINUX: ', 'linux')

    def TableOps(self, i, data):
        #print('ARRAY: ', data)
        print('Par: ', data[0],' tf: ', data[1],' valr: ', data[2],' op: ', data[3],' res: ', data[4],)
        
        self.tela.tableWidgetOps.setRowCount(i+1)

        self.tela.tableWidgetOps.setItem(i,0,  QtWidgets.QTableWidgetItem(str(data[0]), 0))
        self.tela.tableWidgetOps.setItem(i,1,  QtWidgets.QTableWidgetItem('M'+data[2], 0))
        self.tela.tableWidgetOps.setItem(i,2,  QtWidgets.QTableWidgetItem("${:,.2f}".format(data[3]), 0))
        self.tela.tableWidgetOps.setItem(i,3,  QtWidgets.QTableWidgetItem(str(data[1]), 0))
        self.tela.tableWidgetOps.setItem(i,4,  QtWidgets.QTableWidgetItem(str(data[4]), 0))
        self.tela.tableWidgetOps.setColumnWidth(2,600) # and also lower values


        if data[4] == 'LOSS':
            self.tela.tableWidgetOps.item(i, 4).setBackground(QtGui.QColor(255,0,0))
        else:
            self.tela.tableWidgetOps.item(i, 4).setBackground(QtGui.QColor(0,255,0))
    
    def TableBooked(self, i, rows, data):
        self.tela.tableWidgetBooked.setRowCount(rows)
        self.tela.labelBooked.setText(str(rows))
        
        self.tela.tableWidgetBooked.setItem(i,0,  QtWidgets.QTableWidgetItem(data[0]))
        self.tela.tableWidgetBooked.setItem(i,1,  QtWidgets.QTableWidgetItem(data[1]))
        self.tela.tableWidgetBooked.setItem(i,2,  QtWidgets.QTableWidgetItem("M"+data[2]))

        self.tela.tableWidgetBooked.item(i, 1).setBackground(QtGui.QColor(100,100,150))
        self.tela.tableWidgetBooked.item(i, 0).setForeground(QtGui.QColor(0, 255, 0))
        self.tela.tableWidgetBooked.item(i, 2).setForeground(QtGui.QColor(255, 255, 255))

    def loading(self):
        self.spinner = WaitingSpinner(self.tela.qtWaitingSpinner,
                                        roundness=70.0, opacity=15.0,
                                        fade=70.0, radius=10.0, lines=13,
                                        line_length=10.0, line_width=5.0,
                                        speed=1.0, color=(0, 168, 132))
        self.spinner.start() # starts spinning

    def select_account():
        print('TESTE')

    def loginCall(self):
        #TEXT EDITS
        self.tela.label_logging.setText('Fazendo login...')

        email = self.loginUI.textEditEmail.text()
        password = self.loginUI.lineEditPassword.text()

        print('EMAIL: ',email, ' PASS: ', password)

        try:
            status, reason = self.login(email, password)

            if status:
                self.loginUI.close()
                self.enable()
                self.PROFILE = self.profile()
                self.tela.label_logging.setText('logado com sucesso')
                self.showToaster('Utilizador logado com successo!')

                #self.spinner = QtWaitingSpinner(self)

                self.setProfile(self.PROFILE)
            else:
                self.alert('Falha ao Logar', reason)
                self.tela.label_logging.setText('Falha ao Logar: '+ reason)
                print('SENNHA OU EMAIL INCORRECTOS')
        except Exception as e:
            pass
    
    def text_changed(self):
        print("text changed")
        self.updateScreen()

    def kill_thread(self):
        threading.currentThread()

    def on_combobox_changed(self, value):
        print("combobox changed", value)
        if value == 0:
            self.API.change_balance('PRACTICE')
            self.updateProfile()
        if value == 1:
            self.API.change_balance('REAL')
            self.updateProfile()

    def updateProfile(self):
        self.PROFILE = self.profile()
        self.setProfile(self.PROFILE)
        
    def setProfile(self, profile):
        self.BANCA = self.API.get_balance() #set balance 
        self.tela.labelUsername.setText(profile['name'].title())
        self.tela.labelNickname.setText(profile['nickname'])
        self.tela.labelBalance.setText("${:,.2f}".format(self.API.get_balance()))
        self.updateScreen()
        print('BANCA::: ',self.BANCA)

    def disableLogin(self):
        self.loginUI.textEditEmail.setEnabled(False)
        self.loginUI.textEditPassword.setEnabled(False)
        self.loginUI.pushButtonLogin.setEnabled(False)

    #function to sisable elements
    def disable(self):
        self.tela.pushButtonStartTrade.setVisible(False)
        self.tela.pushButtonExit.setVisible(False)

        self.tela.pushButtonStartTrade.setEnabled(False)
        self.tela.pushButtonExit.setEnabled(False)
        self.tela.comboBoxAccountType.setEnabled(False)
        self.tela.comboBoxSorosLevel.setEnabled(False)
        self.tela.textEditStoploss.setEnabled(False)

    #function to enable elements
    def enable(self):
        self.tela.pushButtonOpenLogin.setVisible(False)
        self.tela.pushButtonStartTrade.setVisible(True)
        self.tela.pushButtonExit.setVisible(True)

        self.tela.pushButtonStartTrade.setEnabled(True)
        self.tela.pushButtonExit.setEnabled(True)
        self.tela.comboBoxAccountType.setEnabled(True)
        self.tela.comboBoxSorosLevel.setEnabled(True)
        self.tela.textEditStoploss.setEnabled(True)

    def dialog(title, message):
        dlg = QtWidgets.QDialog()
        dlg.setWindowTitle(message)
        dlg.exec()

    def alert(self, title, message):
        alert = QtWidgets.QMessageBox()
        alert.setIcon(QtWidgets.QMessageBox.Warning)
        alert.setWindowTitle(title)
        alert.setText(message)
        x = alert.exec_()  # this will show our messagebox

    def showToaster(self, message):
        desktop = True
        corner = QtCore.Qt.Corner(3)
        QToaster.showMessage(self.tela, message, corner=corner, desktop=desktop)

    def loginPage(self):
        print('AT LOGIN FUNCTION')
        self.loginUI.exec()

    def catalog(self):
        pass

    def updateScreen(self):
        self.TAKEPROFIT_PERC = self.tela.textEditStoploss.toPlainText()
        print('PPP: ',self.TAKEPROFIT_PERC)
        money = (float(self.TAKEPROFIT_PERC)/100) * self.BANCA
        self.DAY_LOSS_TARGET = money

        #TODAY_PROFIT
        self.tela.label_logging.setText('Robo iniciado...')
        self.tela.labelProfit.setText("${:,.2f}".format(self.DAY_LOSS_TARGET))
        self.tela.label_stop.setText("${:,.2f}".format(money))
        #self.tela.label_sl.setText(self.TAKEPROFIT_PERC+'%')

    #DEBUG
    def startAutoTrade(self):
        self.tela.pushButtonStartTrade.setEnabled(False)
        self.tela.pushButtonStartTrade.setVisible(False)
        self.tela.comboBoxAccountType.setEnabled(False)

        self.loading() #call loading
        #self.start_catalog()
        # DEBUG
        '''
        self.management(3)
        self.schedule_with_File('signals_2022-05-21_1M.txt')
        '''

        #PRODUCTION
        thread = threading.Thread(target=self.start_catalog, args=())
        thread.daemon = True
        thread.start()
        
    def stopAutoTrade(self):
        print('STOPPING TRADING...')
        self.tela.pushButtonStartTrade.setEnabled(True) 
        self.tela.pushButtonStartTrade.setVisible(True) 
        self.spinner.stop() # stops spinning  

        #self.kill_thread()   


    '''
        ROBOT Functions begin here ...
    '''
    #login
    def login(self, email, password) :
        print('**************LOG**************')
        try:
            self.API = IQ_Option(email, password)

            #check = API.connect()
            check, reason= self.API.connect()#connect to iqoption
            print(check, reason)

            if check:
                self.API.change_balance('PRACTICE') #12770216'=
                print("####connect successfully####")
                return (True, None)
            else:
                print("####connect failed####")
                return (False, reason)
        except Exception as e:
            print('=============ERROR: ', e)
            print("Oops!", e.__class__, "occurred.")
            self.alert("Oops!", 'Um erro ocorreu ao tentar logar \n verifique a sua conexao')
            #ATIVOS = API.get_all_open_time()
        except ValueError as ve:
            print('Error::: ',ve)
        
    #####
    def config_robo(self, TAKEPROFIT_PERC, DAY_LOSS_TARGET, SOROS_HAND):
        pass

    #-----------------------------SIGMAL DATA------------------------
    def profile(self):
        prof = json.loads(json.dumps(self.API.get_profile_ansyc()))
        return prof

    #--------------------------------IQ------------------------------
    def getData(self): 
        x = self.profile()
        #print('PROFILE:', x)
        print('>>>>>CONTA: ', x['name'])
        print('>>>>>NICK: ', x['nickname'])
        print('>>>>>SALDO: '+ str(self.API.get_balance())+'$')
        print('>>>>>CRIADO EM: ', x['created'])

        print('\a')

    #-----------------------------CATALOGADOR-------------------------
    def cataloga(self, par, dias, per_cal, per_put, timeframe):
        data = []
        datas_testadas = []
        sair = False
        time_ = time.time()
        qty_candles = 1000
        try:
            while sair == False:
                candles = self.API.get_candles(par, (timeframe*60), qty_candles, time_)
                candles.reverse()

                #print('VELAS: ',candles)

                for candle in candles:
                    
                    '''
                    print('Ativo: '+par+' ABERTURA: ',candle["open"], ' FEIXAMENTO: ',candle["close"], ' FROM: ',candle["from"])
                    print(' DATA::: ' + datetime.fromtimestamp(candle['from']).strftime('%Y-%m-%d')+' ::: ')
                    '''

                    if datetime.fromtimestamp(candle['from']).strftime('%Y-%m-%d') not in datas_testadas:
                        datas_testadas.append(datetime.fromtimestamp(candle['from']).strftime('%Y-%m-%d'))
                    if len(datas_testadas) <= dias:
                        candle.update({'cor':'verde' if candle['open'] < candle['close'] else 'vermelha' if candle['open'] > candle['close'] else 'doji' }) 
                        data.append(candle)
                        #print('datas_testadas: ',datas_testadas) #to remove
                    else: 
                        sair = True
                        break
                time_ = int(candles[-1]['from'] - 1)

            analise = {}
            for candles in data:
                horario = datetime.fromtimestamp(candles['from']).strftime('%H:%M') #get the candle time

                if horario not in analise:
                    analise.update({ horario: {'verde':0, 'vermelha':0, 'doji':0, '%':0, 'dir':''}})
                
                analise[horario][candles['cor']] += 1

                try:
                    analise[horario]['%'] = round(100 * (analise[horario]['verde'] / (analise[horario]['verde'] + analise[horario]['vermelha'] + analise[horario]['doji'])))
                except:
                    pass

            for horario in analise:
                if analise[horario]['%'] > 50 : analise[horario]['dir'] = 'CALL'
                if analise[horario]['%'] < 50 : analise[horario]['dir'], analise[horario]['%'] = 'PUT', (100 - analise[horario]['%'])

            return analise
        except TypeError as e:
            print('ERRO AO CATALOGAR: ', e.with_traceback)
            self.alert('ERRO AO GERAR SINAIS: ', e)
            
    #start catalogation
    def start_catalog(self):
        try:
            print('INICIANDO CATALOGACAO')
            self.tela.label_logging.setText('gerando sinais, por favor espere ...')

            timeframe = 5
            dias = 10
            percentage = 80
            soros = 3

            per_call = abs(percentage) #abs modulo
            per_put = abs(100 - percentage)

            P = self.API.get_all_open_time() #Get all actives

            catalogacao = {}
            for par in P['digital']:
                if P['digital'][par]['open'] == True: #or binary
                    timer = int(time.time()) #get the duration of process

                    cat = 'CATALOGANDO '+ par + '... '
                    self.tela.label_logging.setText(cat)
                    print(Fore.GREEN + '*' + Fore.RESET + cat, end='')

                    #set to log window element
                    catalogacao.update({par: self.cataloga(par, dias, per_call, per_put, timeframe)})

                    print('finalizado em '+ str(int(time.time())- timer) + 'segundos')
            print('\n_____________________RESULTADOS______________________')

            total_sinais = 0
            canShed = False

            filename = 'signals_'+ (datetime.now()).strftime('%Y-%m-%d')+ '_'+str(timeframe)+'M.txt'
            open(filename,'w').write('')

            self.FILEPATH = str(pathlib.Path().resolve()) + filename
            toStoreTime = []

            for par in catalogacao:
                for horario in sorted(catalogacao[par]):
                    ok = False
                    msg = ''

                    if catalogacao[par][horario]['%'] >= percentage:
                        ok = True
                        total_sinais += 1
                    else:
                        ok = False

                    if ok == True:
                        msg = Fore.YELLOW + par + Fore.RESET + ' - '+ horario + ' - ' + (Fore.GREEN if catalogacao[par][horario]['dir'] == 'CALL' else Fore.RED) + catalogacao[par][horario]['dir'] + Fore.RESET + ' - ' + str(catalogacao[par][horario]['%']) + '% - ' + Back.GREEN + Fore.BLACK + str(catalogacao[par][horario]['verde']) + Back.RED + str(catalogacao[par][horario]['vermelha']) + Back.RESET + Back.RESET + str(catalogacao[par][horario]['doji'])
                        print(msg)

                        canShed =True
                        if horario in toStoreTime:
                            pass
                        else:
                            open(filename,'a').write(horario + ',' + par + ','+ catalogacao[par][horario]['dir'].strip() + ','+ str(timeframe) +'\n') #10:00,EURUSD,CALL
                        
                        toStoreTime.append(horario) #add each time to array
                            
            print('\nTOTAL DE SINAIS: ', Fore.GREEN + str(total_sinais))
            self.management(soros)

            if canShed:
               self.schedule_with_File(filename)
        except TypeError as e:
            print('ERRO AO CATALOGAR: ', e.with_traceback)
            self.alert('ERRO AO GERAR SINAIS: ', e)

    #buy method
    def buyBinaryListFile(self, Entrada,Paridade,Direcao,Duracao,Hora):
        print('***************SINAL**************')

        sys.stdout.write('\a')
        #print('INROW_WINS GLOBAL: ', INROW_WINS, ' INROW_LOSES GLOBAL: ', INROW_LOSES)

        isOperated = False
        inTrend = True
        stt = False
        id = 0
        _lucro = 0

        self.PAYOUT_B = float(self.PAYOUT)/100
        self.API.subscribe_strike_list(Paridade, int(Duracao))

        while inTrend and isOperated == False:
            #data = API.get_digital_current_profit(Paridade, int(Duracao))
            d = self.API.get_all_profit()

            #print(d["CADCHF"]["turbo"])
            pay = d[Paridade]["binary"]
            print('PAYOUT DICT', pay, ' Paridade: ', Paridade)

            if(self.DAY_LOSS_TARGET < self.ENTRADA):
                Entrada = self.ENTRADA - (self.ENTRADA - self.DAY_LOSS_TARGET)

            if((self.ENTRADA > 1)): #Caso o payout esteja bom
            #if(int(pay) >= int(self.PAYOUT_B)): #Caso o payout esteja bom
                print('OPERANDO... ')
                self.tela.label_logging.setText('OPERANDO:  Paridade: '+Paridade+' Opc: '+Direcao+' Timeframe: M'+str(Duracao)+' VALOR: '+str(Entrada))

                if(self.INROW_WINS >= 1):
                    print('SOROS: Entrada='+str(Entrada + self.TRADE_PROFIT)+' Paridade= '+Paridade+' Dir= '+Direcao+' Duracao= '+str(Duracao))
                    stt, id = self.API.buy(float(self.soros(self.TRADE_PROFIT)), Paridade, str(Direcao).lower(), int(Duracao))
                else:
                    print('Entrada='+str(Entrada)+' Paridade= '+Paridade+' Dir= '+Direcao+' Duracao= '+str(Duracao))
                    stt, id = self.API.buy(float(Entrada), Paridade, str(Direcao).lower(), int(Duracao))
                
                print('=======ID:',id, ' STATUS: ',stt)
                if stt != False:

                    print("start check win please wait")
                    status,lucro = self.API.check_win_v4(id) #pega o status da operacao
                    #print('=======OP STATUS: ', status)
                    isOperated = True

                    if status == 'loose':
                        print(Fore.RED+"Voce perdeu "+str(lucro)+"$")
                        self.tela.label_logging.setText("Voce perdeu "+str(lucro)+"$")

                        op = [Paridade, Direcao, str(Duracao), lucro, 'LOSS']
                        self.TableOps(self.operations, op)
                        CSV.save_csv(CSV, datetime.now(), Paridade, Direcao, Duracao, lucro, 'LOSS') #save to csv

                        self.LOSES += 1

                        #check in row loses
                        self.INROW_LOSES += 1
                        self.INROW_WINS = 0
                        
                        #updated money
                        self.DAY_LOSS_TARGET += lucro
                        self.TRADE_PROFIT = 0
                        self.SOROS_HAND = float(Entrada) #reset the soros to 1th hand
                        print('SALDO ACTUAL: ', self.DAY_LOSS_TARGET)
                    else:
                        print(Fore.GREEN+"Voce ganhou "+str(lucro)+"$")
                        self.tela.label_logging.setText("Voce ganhou "+str(lucro)+"$")
                        #self.tela.listWidgetTrades.addItem(Paridade+'  '+Direcao+'  M'+str(Duracao)+'  '+str(Entrada)+'$' + ' WIN') #add to ListView

                        op = [Paridade, Direcao, str(Duracao), lucro, 'WIN']
                        self.TableOps(self.operations, op)
                        CSV.save_csv(CSV, datetime.now(), Paridade, Direcao, Duracao, lucro, 'WIN') #save to csv

                        self.WINS += 1

                        #check in row wins
                        self.INROW_WINS += 1
                        self.INROW_LOSES = 0

                        #updated money
                        self.DAY_LOSS_TARGET += lucro
                        self.TRADE_PROFIT += lucro
                        print('SALDO ACTUAL: ', self.DAY_LOSS_TARGET)
                    
                    self.operations+=1
                    self.tela.labelOperated.setText(str(self.operations))
                    self.tela.labelProfit.setText("${:,.2f}".format(self.DAY_LOSS_TARGET))

                    break
                else:
                    print(Fore.RED+"Por favor, tente novamente: ",id,''+ Fore.RESET)
                    self.tela.label_logging.setText("Por favor, tente novamente: "+str(id))
                    break
                    # Fim IF
            else:
                print('NAO OPERAVEL ' + str(self.PAYOUT))
                self.tela.label_logging.setText("Erro, Payout ou valor de entrada insuficiente")
        
        self.tela.labelWins.setText(str(self.WINS))
        self.tela.labelLoses.setText(str(self.LOSES))
        self.tela.labelBalance.setText("${:,.2f}".format(self.API.get_balance())) #update balance

        self.OPERATED.append(Paridade+'  '+Direcao+'  M'+str(Duracao)+'  '+str(Entrada)+'$') #append to list

        print('WINS: '+ Fore.GREEN + str(self.WINS) + Fore.RESET + ' LOSES: ' + Fore.RED + str(self.LOSES)+ Fore.RESET)
        print('\nINROW WINS: '+ Fore.GREEN + str(self.INROW_WINS) + Fore.RESET + ' INROW LOSES: ' + Fore.RED + str(self.INROW_LOSES)+ Fore.RESET)

        if self.INROW_WINS >= 3:
            print( Fore.GREEN +'!!! META BATIDA !!!')
            #print ("KILL MAIN THREAD: %s" % threading.current_thread().ident)
            os._exit(1)
            return
        if self.INROW_LOSES >= 3:
            print( Fore.RED +'!!! ESTOPADO !!!')
            #print ("KILL MAIN THREAD: %s" % threading.current_thread().ident)
            os._exit(1)
            return
        if round(self.DAY_LOSS_TARGET) <= 0 :
            print( Fore.RED +'!!! ESTOPADO !!!')
            os._exit(1)
            return

        print('|=================================================================|')

    #soros method
    def soros(self, won):
        self.SOROS_HAND = self.SOROS_HAND + won
        print('MAO DE SOROS',float(self.SOROS_HAND))
        return float(self.SOROS_HAND)

    #managment method
    def management(self, _soros):
        try:
            percent = (self.BANCA * float(self.TAKEPROFIT_PERC))/100
            self.ENTRADA = round(percent/_soros, 2)
            print('Entrada: $', self.ENTRADA)

            self.DAY_LOSS_TARGET = percent
            self.SOROS_HAND = self.ENTRADA
            self.tela.labelEntrys.setText(str(self.ENTRADA))

        except TypeError:
            print('UM ERRO OCORREU: ')
    
    #schedule signals
    def schedule_with_File(self, filename):
        Entrada = self.ENTRADA
        i = 0

        self.FILENAME = filename
        self.MERCADO = 1
        signals_list = []

        job = []
        now = datetime.now()
        print("::::::::::::::::::::::::::::::::HOJE:::::::::::::::::::::::::::::::::::")
        print(":::::::::::::::::::: ", now ," :::::::::::::::::::::")
        print(":::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::")

        arquivo = open(filename, 'r')
        
        for line in sorted(arquivo):
            i +=1
            signal = line.split(',')

            print('HORA: ' + Fore.YELLOW + str(signal[0]) + Fore.RESET + ' ACTIVO: ' + signal[1] + ' OPT: '+signal[2] + ' TEMPO: M' + signal[3])

            split_time = signal[0].split(':')
            split_date = ((datetime.now()).strftime('%Y-%m-%d')).split('-')

            if self.MERCADO == 1:    
                time_tuple = now.timetuple()
                
                #tupla year (four digits, e.g. 1998) month (1-12), day (1-31), hours (0-23), minutes (0-59), seconds (0-59), weekday (0-6, Monday is 0), Julian day (day in the year, 1-366), DST (-1, 0 or 1)
                t1 = (int(split_date[0]), int(split_date[1]), int(split_date[2]), int(split_time[0]), int(split_time[1]), 0, time_tuple[6], time_tuple[7], -1)

                Paridade = signal[1]
                Duracao = signal[3]
                Direcao = signal[2]
                hora = signal[0]      

                result = time.asctime(t1)
            
            time_sec = time.mktime(t1) 

            # datetime object containing current date and time
            time_sec_now = time.mktime(now.timetuple())
            #print('*******TIME NOW: ', time_sec_now,' TOME SIG: ',time_sec)

            if time_sec_now >= time_sec:
                print('STATUS: '+Fore.RED+' Sinal Ultrapassado')
                print('|----------------------------------------------------------------------|')
            else:
                x = threading.Thread(target=self.run, args=(Entrada,Paridade,Direcao,Duracao,time_sec)) 
                print('STATUS: '+Fore.GREEN+'Agendado')
                print('|----------------------------------------------------------------------|')

                job.append(x)
                signals_list.append(signal)
            i = i + 1

        print('************************ ',len(signals_list),' Sinais Agendados**************************')
            
        for j in job:
            j.start()

        # to fill List view
        for index, signal in enumerate(signals_list):
            op = [signal[0], signal[1], signal[3], 'LOSS']
            self.TableBooked(index, len(signals_list), op)

        #check if theres a signals
        if len(signals_list) == 0 :
            self.alert('Aviso','Do momento, sem sinais disponiveis por operar!')
            self.stopAutoTrade()
        else:
            self.showToaster('Robo em processo, aguarde!')

        return signals_list
   
    #do the job
    def run(self, Entrada,Paridade,Direcao,Duracao,Hora):
        sch = sched.scheduler(time.time, time.sleep)
        sch.enterabs(Hora, 1, self.buyBinaryListFile, (Entrada,Paridade,Direcao,Duracao,Hora))
        sch.run()

    def stopJods(self):
        sched.scheduler.cancel(e3)

#main method
def main():
    window = Window()
    '''
    RUN OF THE APP
    '''
    window.tela.show()
    window.app.exec()

if __name__ == '__main__':
    main()