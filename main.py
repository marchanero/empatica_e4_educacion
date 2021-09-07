import pyqtgraph as pg
import main_designer3
import sys
import multiprocessing
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import SIGNAL

import datetime
from collections import deque
import socket
import time
import math
import os, shutil



pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

# Variables globales para el intercambio de informacion entre clases
global therapist_id
global patient_id
global session_id
global path_dir

# Creacion del directorio raiz
#grabacion=os.mkdir("Sesiones",0o777)

import pytz
global contador

UNIX_EPOCH_naive = datetime.datetime(1970, 1, 1, 0, 0)  # offset-naive datetime
UNIX_EPOCH_offset_aware = datetime.datetime(1970, 1, 1, 0, 0, tzinfo=pytz.utc)  # offset-aware datetime
UNIX_EPOCH = UNIX_EPOCH_naive

TS_MULT_us = 1e6


def now_timestamp(ts_mult=TS_MULT_us, epoch=UNIX_EPOCH):
    return (int((datetime.datetime.utcnow() - epoch).total_seconds() * ts_mult))


def int2dt(ts, ts_mult=TS_MULT_us):
    return (datetime.datetime.utcfromtimestamp(float(ts) / ts_mult))


def int2td(ts, ts_mult=TS_MULT_us):
    return (datetime.timedelta(seconds=float(ts) / ts_mult))


class TimeAxisItem(pg.AxisItem):
    def __init__(self, *args, **kwargs):
        #  super().__init__(*args, **kwargs)
        super(TimeAxisItem, self).__init__(*args, **kwargs)

    # fuencion de  te devuelve el timestamp desde el formato epoch hasta el formato  del sistema
    def tickStrings(self, values, scale, spacing):
        # PySide's QTime() initialiser fails miserably and dismisses args/kwargs
        return [int2dt(value).strftime("%H:%M:%S.%f") for value in values]
        # return [int2dt(value).strftime("%H:%M:%S") for value in values]


def empaticaconnection(queue, queue2):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.01)
    host = '127.0.0.1'
    port = 8181
    addr = (host, port)

    ################ intentamos conectar
    while True:
        try:
            s.connect(addr)
            connected = True
            #mac = 'B404BC' #Pulsera de Arturo
            #mac = '7E9418'  # Pulsera Rober
            #mac = '09048A' #pulsera de Alvaro 2
            mac = '1C14C6' #pulsera de Alvaro 1
            queue.put('R canal_comunicaciones OK\n')
            break
        except socket.timeout:
            queue.put('R encienda el servidor Empatica!')
            time.sleep(5)

        except:  # por si apareciera otro tipo de error
            pass

    cmd = {
        'connect': 'device_connect ' + mac + '\r\n',
        'disconnect': 'device_disconnect\r\n',
        'lista': 'device_list\r\n',
        'status': 'server_status\r\n',
        'pausa_on': 'pause ON\r\n',
        'pausa_off': 'pause OFF\r\n',
        'gsr_on': 'device_subscribe gsr ON\r\n',
        'gsr_off': 'device_subscribe gsr OFF\r\n',
        'acc_on': 'device_subscribe acc ON\r\n',
        'acc_off': 'device_subscribe acc OFF\r\n',
        'bvp_on': 'device_subscribe bvp ON\r\n',
        'bvp_off': 'device_subscribe bvp OFF\r\n',
        'ibi_on': 'device_subscribe ibi ON\r\n',
        'ibi_off': 'device_subscribe ibi OFF\r\n',
        'tmp_on': 'device_subscribe tmp ON\r\n',
        'tmp_off': 'device_subscribe tmp OFF\r\n',
        'bat_on': 'device_subscribe bat ON\r\n',
        'bat_off': 'device_subscribe bat OFF\r\n',
    }

    ######## MAIN BUCLE

    while connected:

        try:  # miramos en cada ciclo si hubiera algun mensaje proveniente del interface
            if not queue2.empty():  # si hay un mensaje esperando
                msg = queue2.get(False)
                print(msg)
                if msg == 'apaga':  # salgo de la aplicacion
                    print('estoy apagando')
                    connected = False
                else:
                    s.send(cmd[msg])
        except:
            time.sleep(0.5)
            pass

        # miramos si hay algo desde el servidor, y lo mandamos a la interface
        # todo: Se queda en este bucle una vez apagado el servidor, pq no llegan datos y ya no atiende . Hay que pensar en otra cosa.

        raw = ''
        try:
            while not raw.endswith('\n'):
                raw += s.recv(1)  # si aqui no hay dato deberia saltar una excepcion timeout
                if not raw:  # obligo a salir si no hay nada en el buffer
                    time.sleep(0.1)
                    break
        except:
            pass
        if raw:
            queue.put(raw)
    print('adios')




class MyMainWindow(QtGui.QMainWindow, main_designer3.Ui_MainWindow):
    global contador
    def __init__(self, parent=None):
        global contador
        contador=0
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)

        # Desactivacion de los botones hasta que no se le de al boton de conectar.
        self.eda_button.setDisabled(True)
        self.eda_button.setStyleSheet("color: black; background-color: white")
        self.eda_button.setText("EDA")
        self.ibi_button.setDisabled(True)
        self.ibi_button.setStyleSheet("color: black; background-color: white")
        self.ibi_button.setText("Inter-Beat")
        self.bvp_button.setDisabled(True)
        self.bvp_button.setStyleSheet("color: black; background-color: white")
        self.bvp_button.setText("Blood Volume Pressure")
        self.acc_button.setDisabled(True)
        self.acc_button.setStyleSheet("color: black; background-color: white")
        self.acc_button.setText("Acceleration")
        self.tmp_button.setDisabled(True)
        self.tmp_button.setStyleSheet("color: black; background-color: white")
        self.tmp_button.setText("Temperature")
        self.pause_button.setDisabled(True)
        self.pause_button.setStyleSheet("color: black; background-color: white")
        self.pause_button.setText("Pause")

        self.event_button.setDisabled(True)
        self.event_button.setStyleSheet("color: black; background-color: white")

        self.select_al_channels_button.setDisabled(True)
        self.select_al_channels_button.setStyleSheet("color: black; background-color: white")

        #self.start_button_record.hide()
        self.start_button_record.setDisabled(True)
        self.start_button_record.setStyleSheet("color: black; background-color: white")

        #self.System_value_groupbox.hide()
        self.menubar.hide()
        #Esconder  los indicadores de las variables


        self.process_data = {
            'R': self.process_server_data,
            'E4_Gsr': self.update_EDA_data,
            'E4_Bvp': self.update_BVP_data,
            'E4_Acc': self.update_ACC_data,
            'E4_Temperature': self.update_TMP_data,
            'E4_Ibi': self.update_IBI_data,
            'E4_Battery': self.update_BAT_data
        }

        # inicializamos el semaforo a rojo
        self.color_semaforo(1)

        
        # establecemos la barra de status
        # cadena = "Patient Id: " + patient_id + "   " + "Session Id: " + session_id
        # self.statusBar.showMessage(cadena)

        # arrancamos procesos paralelos (entrada de datos desde socket

        self.queue = multiprocessing.Queue()
        self.queue2 = multiprocessing.Queue()

        # TIMER DEL UPDATE DE PARAMETROS
        self.timer2 = pg.QtCore.QTimer()
        self.timer2.timeout.connect(self.update_params)
        self.timer2.start(2000)


        ##################################################################################
        #####################    botones y settings
        ##################################################################################
        # Menu de la ventana

        # ventana About
        # self.actionAbout_this_app.triggered.connect(self.open_window_about)


        # connect
        self.connect_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")
        self.connect_button.setCheckable(True)
        self.connect_button.clicked.connect(self.on_connect_button)

        # status
        self.status_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")
        self.status_button.clicked.connect(self.on_status_button)

        # list of devices
        self.devices_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")
        self.devices_button.clicked.connect(self.on_devices_button)

        # pause
        self.pause_button.setCheckable(True)
        self.pause_button.clicked.connect(self.on_pause_button)

        #start 
        self.start_button_record.setCheckable(True)
        self.start_button_record.clicked.connect(self.on_start_recording)

        # eda
        self.eda_button.setCheckable(True)
        self.eda_button.clicked.connect(self.on_eda_button)

        # bvp
        self.bvp_button.setCheckable(True)
        self.bvp_button.clicked.connect(self.on_bvp_button)

        # ibi
        self.ibi_button.setCheckable(True)
        self.ibi_button.clicked.connect(self.on_ibi_button)

        # acc
        self.acc_button.setCheckable(True)
        self.acc_button.clicked.connect(self.on_acc_button)

        # tmp
        self.tmp_button.setCheckable(True)
        self.tmp_button.clicked.connect(self.on_tmp_button)

        #Event
        self.event_button.setCheckable(True)
        self.event_button.clicked.connect(self.on_eve_button)

        #Select all channel
        self.select_al_channels_button.setCheckable(True)
        self.select_al_channels_button.clicked.connect(self.on_select_al_channels)

########################################################################################################################
####################### PLOTS ##########################################################################################
########################################################################################################################

        # Creo el objeto pyqtgraph
        self.win = pg.GraphicsWindow()
        self.signal_layout.addWidget(self.win)

        # TIMER DEL update de plots

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(10)

        # arrancamos procesos paralelos (entrada de datos desde socket
        self.p = multiprocessing.Process(target=empaticaconnection, args=(self.queue, self.queue2))
        self.p.start()

        #self.show()

        # CANVAS DEL EDA
    def canvas_eda(self):
        self.eda_time = deque(maxlen=200)  # lista de x
        self.eda_datay = deque(maxlen=200)  # lista de y
        self.p1 = self.win.addPlot(title='Electro-Dermal Activity', axisItems={'bottom': TimeAxisItem(orientation='bottom')},row=0,col=0)
        self.curve1 = self.p1.plot(pen={'color': (255, 0, 0), 'width': 2})

        # CANVAS DEL IBI
    def canvas_ibi(self):
        #self.win.nextRow()

        self.ibi_time = deque(maxlen=100)  # lista de x
        self.ibi_datay = deque(maxlen=100)  # lista de y , antes habia 100 a ver si escribe antes en disco
        self.p2 = self.win.addPlot(title="Inter-Beat Interval", axisItems={'bottom': TimeAxisItem(orientation='bottom')}, row=2,col=0)
        self.curve2 = self.p2.plot(pen={'color': (0, 170, 0), 'width': 2})

        # CANVAS DEL BVP
    def canvas_BVP(self):
        #self.win.nextRow()
        self.bvp_time = deque(maxlen=1000)  # lista de x
        self.bvp_datay = deque(maxlen=1000)  # lista de y
        self.p3 = self.win.addPlot(title="Blood Volume Pressure", axisItems={'bottom': TimeAxisItem(orientation='bottom')},row=1, col=0)
        self.curve3 = self.p3.plot(pen={'color': (0, 0, 255), 'width': 2})

        # CANVAS DEL ACC
    def canvas_acc(self):
        #self.win.nextRow()

        self.acc_time = deque(maxlen=1000)
        self.acc_datax = deque(maxlen=1000)  # lista de x
        self.acc_datay = deque(maxlen=1000)  # lista de y
        self.acc_dataz = deque(maxlen=1000)  # lista de z
        self.p4 = self.win.addPlot(title="Acceleration", axisItems={'bottom': TimeAxisItem(orientation='bottom')},row=3, col=0)
        self.curve4 = self.p4.plot(pen={'color': (255, 0, 255), 'width': 2})
        self.curve5 = self.p4.plot(pen={'color': (0, 255, 255), 'width': 2})
        self.curve6 = self.p4.plot(pen={'color': (255, 127, 80), 'width': 2})

        # CANVAS DEL TMP
    def canvas_tmp(self):
        #self.win.nextRow()
        self.tmp_time = deque(maxlen=200)
        self.tmp_datay = deque(maxlen=200)
        self.p5 = self.win.addPlot(title="Temperature", axisItems={'bottom': TimeAxisItem(orientation='bottom')},row=4,col=0)
        self.curve7 = self.p5.plot(pen={'color': (128, 0, 255), 'width': 2})

        # CANVAS DEL EVENTOS
    def canvas_event(self):
        #self.win.nextRow()
        self.eve_time = deque(maxlen=100)
        self.eve_datay = deque(maxlen=100)
        self.p6 = self.win.addPlot(title="Event (Please, press 'e' to register)", axisItems={'bottom': TimeAxisItem(orientation='bottom')},row=5, col=0)
        self.curve8 = self.p6.plot(pen={'color': (0, 0, 0), 'width': 2})


    # def open_window_about(self):
    #     window=ventana_about(self)
    #     window.show()

    def open_window(self):
        self.dialog.show()

    def close_app(self):
        sys.exit(app.exec_())

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Space:
            self.update_EVE_data()
        if e.key() == QtCore.Qt.Key_Enter:
            self.update_EVE_data()
        if e.key() == QtCore.Qt.Key_E:
            self.update_EVE_data()

    def closeEvent(self, *args, **kwargs):
        self.queue2.put('apaga')
        # cierro ficheros de datos
        self.eda_file.close()
        self.bvp_file.close()
        self.acc_file.close()
        self.eve_file.close()
        self.tmp_file.close()
        self.ibi_file.close()

    ################################################################
    # CALLBACKS DE LOS BUTTONS
    ################################################################

    def on_connect_button(self):
        if self.connect_button.isChecked():
            self.eda_button.setText("Electro-Dermal Activity")
            self.eda_button.setDisabled(False)
            self.eda_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")

            self.ibi_button.setText("Inter-Beat interval")
            self.ibi_button.setDisabled(False)
            self.ibi_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")

            self.bvp_button.setText("Beats Per Minute")
            self.bvp_button.setDisabled(False)
            self.bvp_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")

            self.acc_button.setText("Acceleration")
            self.acc_button.setDisabled(False)
            self.acc_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")

            self.tmp_button.setText("Temperature")
            self.tmp_button.setDisabled(False)
            self.tmp_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")

            self.pause_button.setText("Pause")
            self.pause_button.setDisabled(False)
            self.pause_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")

            self.start_button_record.setText("Start")
            self.start_button_record.setDisabled(False)
            self.start_button_record.setStyleSheet("color: white; background-color: rgb(128,128,128)")

            self.event_button.setDisabled(False)
            self.event_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")

            self.select_al_channels_button.setDisabled(False)
            self.select_al_channels_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")

            self.queue2.put('connect')
            self.connect_button.setStyleSheet("color: black")
            self.connect_button.setText('Disconnect')
            self.queue2.put('bat_on')  # le indico que me manda mensajes de bateria nada mas conectar

        else:
            self.queue2.put('disconnect')
            self.connect_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")
            self.connect_button.setText('Connect')

    def on_select_al_channels(self):
        if self.select_al_channels_button.isChecked():
            #self.win.clear()
            self.eda_button.setChecked(True)
            self.on_eda_button()
            self.ibi_button.setChecked(True)
            self.on_ibi_button()
            self.bvp_button.setChecked(True)
            self.on_bvp_button()
            self.acc_button.setChecked(True)
            self.on_acc_button()
            self.tmp_button.setChecked(True)
            self.on_tmp_button()
            self.event_button.setChecked(True)
            self.on_eve_button()

        else:
            self.select_al_channels_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")
            self.eda_button.setChecked(False)
            self.on_eda_button()
            self.ibi_button.setChecked(False)
            self.on_ibi_button()
            self.bvp_button.setChecked(False)
            self.on_bvp_button()
            self.acc_button.setChecked(False)
            self.on_acc_button()
            self.tmp_button.setChecked(False)
            self.on_tmp_button()
            self.event_button.setChecked(False)
            self.on_eve_button()




    def on_status_button(self):
        self.queue2.put('status')

    def on_devices_button(self):
        self.queue2.put('lista')

    def on_pause_button(self):
        if self.pause_button.isChecked():
            self.queue2.put('pausa_on')

            self.pause_button.setStyleSheet("color: black")
        else:
            self.queue2.put('pausa_off')
            self.pause_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")


    ####################################################################################
    # CREACION DEL DIRECTORIO DE GUARDADO
    ##################################################################################################
    def dir_folder_create(self):
        if not os.path.exists('Sesiones'):
            os.mkdir("Sesiones",0o777)
            print ("Creacion de la carpeta Sesiones")
        else:
            print("No se ha creado la carpeta sesiones")

    def create_file_in_folder(self, id_participante):
        #definimos los ficheros de texto para grabar los datos
        print ("Creacion de los ficheros de guardado")
        self.eda_file = open('Sesiones' + '/' + id_participante + '_' + 'eda_data.csv', 'wb')
        self.bvp_file = open('Sesiones' + '/' + id_participante + '_' + 'bvp_data.csv', 'a')
        self.acc_file = open('Sesiones' + '/' + id_participante + '_' +'acc_data.csv', 'wb')
        self.eve_file = open('Sesiones' + '/' + id_participante + '_' + 'eve_data.csv', 'wb')
        self.tmp_file = open('Sesiones' + '/' + id_participante + '_' + 'tmp_data.csv', 'wb')
        self.ibi_file = open('Sesiones' + '/' + id_participante + '_' + 'ibi_data.csv', 'wb')
        
    def write_values_in_file(self):
        pass

###############################################################################################################################
#Creacion de la funcion de guardado de los datos 
###############################################################################################################################
    def on_start_recording(self):
        if self.start_button_record.isChecked():
            self.setStyleSheet("color: black")
            self.dir_folder_create()
            id_participante_str=self.id_participante.toPlainText()
            print(id_participante_str)
            self.create_file_in_folder(id_participante_str)
            self.id_participante.setDisabled(True)
            self.start_button_record.setText("Stop")
            ########################################################################################################################
            #Funcion de guardado. 


        else:
            self.start_button_record.setStyleSheet("color: white; background-color: rgb(128,128,128)")


###############################################################################################################################
#Botones de los canales.
###############################################################################################################################

    def on_eda_button(self):
        if self.eda_button.isChecked():
            self.canvas_eda()
            self.queue2.put('gsr_on')
            self.eda_button.setStyleSheet("color: black")
        else:
            self.win.removeItem(self.p1)
            self.queue2.put('gsr_off')
            self.eda_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")

    def on_bvp_button(self):
        if self.bvp_button.isChecked():
            self.queue2.put('bvp_on')
            self.canvas_BVP()
            self.bvp_button.setStyleSheet("color: black")
        else:
            self.queue2.put('bvp_off')
            self.win.removeItem(self.p2)
            self.bvp_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")

    def on_ibi_button(self):
        if self.ibi_button.isChecked():
            self.queue2.put('ibi_on')
            self.canvas_ibi()
            self.ibi_button.setStyleSheet("color: black")
        else:
            self.queue2.put('ibi_off')
            self.win.removeItem(self.p3)
            self.ibi_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")

    def on_acc_button(self):
        if self.acc_button.isChecked():
            self.queue2.put('acc_on')
            self.canvas_acc()
            self.acc_button.setStyleSheet("color: black")
        else:
            self.queue2.put('acc_off')
            self.win.removeItem(self.p4)
            self.acc_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")

    def on_tmp_button(self):
        if self.tmp_button.isChecked():
            self.queue2.put('tmp_on')
            self.canvas_tmp()
            self.tmp_button.setStyleSheet("color: black")
        else:
            self.queue2.put('tmp_off')
            self.win.removeItem(self.p5)
            self.tmp_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")

    def on_eve_button(self):
        if self.event_button.isChecked():
            self.canvas_event()
            self.event_button.setStyleSheet("color: black")
        else:
            self.win.removeItem(self.p6)
            self.event_button.setStyleSheet("color: white; background-color: rgb(128,128,128)")


    # System states (semaforos)
    def color_semaforo(self, status):

        if status == 1:
            self.semaforo_widget.setStyleSheet("background:rgb(255, 30, 30)")
            self.semaforo_label_msg.setText("Please, turn on the Empatica server")

        if status == 2:
            self.semaforo_widget.setStyleSheet("background-color:rgb(240, 240, 0)")
            self.semaforo_label_msg.setText("System waiting to connect with the wristband.")

        if status == 3:
            self.semaforo_widget.setStyleSheet("background-color:rgb(0, 204, 0)")
            self.semaforo_label_msg.setText("System ready!!! Select the channel(s) you want to record.")

    ##################################################################################################
    ############################################ PROCCESSING AND PLOTTING DATA########################
    ##################################################################################################

    def update_data(self):
        try:
            while True:
                data = self.queue.get_nowait()  # cola no bloqueante
                data = data.split(' ')
                self.process_data[data[0]](data)  # gestionado a traves de un dictionary
        except Exception as inst:  # no hay elementos que sacar de la cola
            pass
    #
    def update_params(self):
        return 0
    #
    #     # TODO: Parecec ser que es mucho mas eficjente hacer un ring loop con numpy que con deque.
    #
    #     if self.eda_datay:
    #         last_eda = self.eda_datay[-1]
    #         self.EDA_value_2.setText(str(round(last_eda, 2)) + ' uS')
    #
    #     if self.ibi_datay:
    #         last_ibi = self.ibi_datay[-1]
    #         self.IBI_value.setText(str(round(last_ibi, 2)) + ' s')
    #         self.BPM_value.setText(str(round(60 / last_ibi, 2)) + ' bpm')
    #
    #     if self.acc_datax:
    #         last_acc = math.sqrt(self.acc_datax[-1] ** 2 + self.acc_datay[-1] ** 2 +
    #                              self.acc_datax[-1] ** 2)
    #         self.ACC_value.setText(str(round(last_acc, 2)) + ' m/s^2')
    #
    #     if self.tmp_datay:
    #         last_tmp = self.tmp_datay[-1]
    #         self.TMP_value.setText(str(round(last_tmp, 2)) + "g")
    #



    def process_server_data(self, data):
        if data[1] == 'canal_comunicaciones' and data[2][0:-1] == 'OK':
            print('activado el canal de comunicaciones')
            self.color_semaforo(2)
        elif data[1] == 'device_connect' and data[2][0:-1] == 'OK':
            print('activada la conexion')
            self.color_semaforo(3)
        elif data[1] == 'device_disconnect' and data[2][0:-1] == 'OK':
            self.color_semaforo(2)

        self.SYS_value.setText(" ".join(data))

    def update_BAT_data(self, data):
        f = float(data[2][0:-2].replace(',', '.'))
        print(f)
        if f > 0.05:
            self.battery_progressBar.setValue(int(f * 100))

    def update_EDA_data(self, data):
        d = data[1].replace(',', '')
        while len(d) < 16:  # a veces el timestamp viene con un numero distinto de decimales. Hay que normalizar a 16
            d += '0'
        self.eda_time.append(int(d))  # storing data on eda_time
        f = data[2][0:-2].replace(',', '.')
        self.eda_datay.append(float(f))  # storing eda value on eda_datay
        self.curve1.setData(x=list(self.eda_time), y=list(self.eda_datay))  # plotting
        self.eda_file.write(d + ';' + f + '\n')  # recording eda value on file

    def update_IBI_data(self, data):
        d = data[1].replace(',', '')
        while len(d) < 16:  # a veces el timestamp viene con un numero distinto de decimales. Hay que normalizar a 16
            d += '0'
        d = int(d)
        self.ibi_time.append(d)
        self.ibi_datay.append(float(data[2][0:-2].replace(',', '.')))
        print("Date_epoch=" + str(d) + " Valor de ib = " + data[2])
        self.ibi_file.write(str(d) + ';' + data[2] + '\n')
        self.curve2.setData(x=list(self.ibi_time), y=list(self.ibi_datay))

    def update_BVP_data(self, data):
        d = data[1].replace(',', '')
        while len(d) < 16:  # a veces el timestamp viene con un numero distinto de decimales. Hay que normalizar a 16
            d += '0'
        self.bvp_time.append(int(d))
        f = data[2][0:-2].replace(',', '.')
        self.bvp_datay.append(float(f))
        self.curve3.setData(x=list(self.bvp_time), y=list(self.bvp_datay))
        self.bvp_file.write(d + ';' + f + '\n')  # recording bvp value on file

    def update_ACC_data(self, data):
        d = data[1].replace(',', '')
        while len(d) < 16:  # a veces el timestamp viene con un numero distinto de decimales. Hay que normalizar a 16
            d += '0'
        d = int(d)

        self.acc_time.append(d)
        self.acc_datax.append(int(data[2]))
        self.acc_datay.append(int(data[3]))
        self.acc_dataz.append(int(data[4][0:-2]))

        self.curve4.setData(x=list(self.acc_time), y=list(self.acc_datax))
        self.curve5.setData(x=list(self.acc_time), y=list(self.acc_datay))
        self.curve6.setData(x=list(self.acc_time), y=list(self.acc_dataz))
        self.acc_file.write(str(d) + ';' + data[2] + ';' + data[3] + ';' + data[4] + '\r')

    def update_TMP_data(self, data):
        d = data[1].replace(',', '')
        while len(d) < 16:  # a veces el timestamp viene con un numero distinto de decimales. Hay que normalizar a 16
            d += '0'
        d = int(d)

        self.tmp_time.append(d)
        self.tmp_datay.append(float(data[2][0:-2].replace(',', '.')))
        self.curve7.setData(x=list(self.tmp_time), y=list(self.tmp_datay))
        self.tmp_file.write(str(d) + ';' + str(data[2]) + '\n')


    def update_EVE_data(self):
        # voy a crear un pulso
        global  contador
        d = now_timestamp()
        d0 = d - 100
        d1 = d + 100
        global contador
        self.eve_time.append(d0)
        self.eve_time.append(d)
        self.eve_time.append(d1)

        self.eve_datay.append(0)
        self.eve_datay.append(1)
        self.eve_datay.append(0)

        self.eve_file.write(str(d) + ";" + str(contador)+'\n')
        self.curve8.setData(x=list(self.eve_time), y=list(self.eve_datay))
        contador=contador+1
        self.EVE_value.setText(str(contador))
        print(contador)

    def write_data(self, filename, data):
        pass



if __name__ == "__main__":
    multiprocessing.freeze_support()
    app = QtGui.QApplication(sys.argv)
    ui = MyMainWindow()
    #ui = seleccion_paciente()
    ui.show()
    sys.exit(app.exec_())
