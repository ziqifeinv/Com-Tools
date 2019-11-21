import sys
import serial
import time
import serial.tools.list_ports
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor
from ui_main import Ui_ui_main

#print("%s, %s" % (sys._getframe().f_code.co_name,sys._getframe().f_lineno))

class Serial_app(QtWidgets.QMainWindow, Ui_ui_main):
    def __init__(self):
        super(Serial_app, self).__init__()  #super调用父类的构造函数，等同于下面两个步骤
        # dialog = QtWidgets.QMainWindow()
        # ui = Ui_ui_main()
        self.setupUi(self)
        self.setWindowTitle("串口工具  --by 子期非女")
        self.serial = serial.Serial()
        self.init()

    def init(self):
        print('start')
        self.color_red = QColor().red()
        print(self.color_red)
        #定义定时发送相关功能
        self.timer_list = [self.timer_1, self.timer_2, self.timer_3]
        self.timer_num_list = [self.timer_num_1, self.timer_num_2, self.timer_num_3]
        self.qtimer_1 = QTimer()
        self.qtimer_2 = QTimer()
        self.qtimer_3 = QTimer()
        self.timer_timer = [self.qtimer_1, self.qtimer_2, self.qtimer_3]
        self.qtimer_1.timeout.connect(lambda: self.func_data_send(0))
        self.qtimer_2.timeout.connect(lambda: self.func_data_send(1))
        self.qtimer_3.timeout.connect(lambda: self.func_data_send(2))
        #定义发送相关功能
        self.send_hex_list = [self.is_hex_1, self.is_hex_2, self.is_hex_3]
        self.send_data_list = [self.send_data_1, self.send_data_2, self.send_data_3]

        #用于初次选择下拉列表是刷新串口列表
        self.check_serial_counter = True
        #用于保存按钮状态，0表示串口未打开，1表示串口打开
        self.open_serial_pbt_status = False
        #字节数统计清零
        self.bit_counter_rec = 0
        self.bit_counter_send = 0
        #定义“停止显示"全局变量
        self.pause_dispaly_flag = False
        self.pause_dispaly.clicked.connect(self.func_disp_ctrl)

        # 定时器接收数据
        self.timer_rec = QTimer(self)
        self.timer_rec.timeout.connect(self.func_data_receive)

        self.open_serial.clicked.connect(self.func_open_serial)
        self.com_selete.highlighted.connect(self.func_check_serial)
        self.send_1.clicked.connect(lambda: self.func_data_send(0))
        self.send_2.clicked.connect(lambda: self.func_data_send(1))
        self.send_3.clicked.connect(lambda: self.func_data_send(2))
        self.timer_1.stateChanged.connect(lambda: self.func_timing_send(0))
        self.timer_2.stateChanged.connect(lambda: self.func_timing_send(1))
        self.timer_3.stateChanged.connect(lambda: self.func_timing_send(2))

    # 检测所有存在的串口，将信息存储在字典中
    def func_check_serial(self):
        if (self.check_serial_counter):
            print("%s, %s" % (sys._getframe().f_code.co_name,sys._getframe().f_lineno))
            self.com_dict = {}
            port_list = list(serial.tools.list_ports.comports())
            if len(port_list) <= 0:
                print("未发现串口")
                QMessageBox.warning(self,'警告','未发现串口',QMessageBox.Yes)
                return
            self.com_selete.clear()
            for port in port_list:
                self.com_dict["%s" % port[0]] = "%s" % port[1]
                self.com_selete.addItem(port[0])
            self.check_serial_counter = False
            return

    # 串口打开关闭函数
    def func_open_serial(self):
        if(self.open_serial_pbt_status):    #关闭串口
            print("%s, %s" % (sys._getframe().f_code.co_name, sys._getframe().f_lineno))
            try:
                self.serial.close()
            except:
                pass
            self.timer_rec.stop()
            self.check_bit_selete.setEnabled(True)
            self.data_bit_selete.setEnabled(True)
            self.stop_bit_selete.setEnabled(True)
            self.baud_selete.setEnabled(True)
            self.com_selete.setEnabled(True)
            self.open_serial.setText('打开串口')
            self.open_serial_pbt_status = False
            self.check_serial_counter = True
            return

        else:   #打开串口
            print("%s, %s" % (sys._getframe().f_code.co_name, sys._getframe().f_lineno))
            self.serial.port = self.com_selete.currentText()
            self.serial.baudrate = int(self.baud_selete.currentText())
            self.serial.bytesize = int(self.data_bit_selete.currentText())
            self.serial.stopbits = int(self.stop_bit_selete.currentText())
            self.serial.parity = self.check_bit_selete.currentText()

            if(self.serial.is_open):
                QMessageBox.warning(self, '警告', '拒绝访问', QMessageBox.Yes)
                return
            try:
                self.serial.open()
            except:
                print("串口打开失败")
                QMessageBox.warning(self, '警告', '串口打开失败', QMessageBox.Yes)
                return

            if (self.serial.is_open):
                self.check_bit_selete.setEnabled(False)
                self.data_bit_selete.setEnabled(False)
                self.stop_bit_selete.setEnabled(False)
                self.baud_selete.setEnabled(False)
                self.com_selete.setEnabled(False)
                self.open_serial.setText('关闭串口')
                self.open_serial_pbt_status = True
                # 打开串口接收定时器，周期为2ms
                self.timer_rec.start(200)
        return

    def func_data_receive(self):
        print("%s, %s" % (sys._getframe().f_code.co_name, sys._getframe().f_lineno))
        try:
            num = self.serial.inWaiting()
        except:
            self.open_serial_func()
            return
        if num > 0:
            rec_data = self.serial.read(num)
            num = len(rec_data)
            disp_data = ''
            # hex显示
            if self.hex_display.checkState():
                for i in range(0, len(rec_data)):
                    disp_data = disp_data + '{:02X}'.format(rec_data[i]) + ' '
            else:
                # 串口接收到的字符串为b'123',要转化成unicode字符串才能输出到窗口中去
                disp_data = rec_data.decode('utf-8')
            # 统计接收字符的数量
            self.bit_counter_rec += num
            #self.counter_rec.setText(str(self.data_num_received))
            self.counter_rec.setText(str(self.bit_counter_rec))
            #接收的显示逻辑
            if self.mask_data_type.isChecked():
                disp_data = 'RX: ' + disp_data
            if self.time_stamp.isChecked():
                temp_time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                disp_data = temp_time_stamp + ' ' + disp_data
            if (self.pause_dispaly_flag == False):
                disp_data = disp_data + '\n'
                self.rec_data.insertPlainText(disp_data)
                # 获取到text光标
                textCursor = self.rec_data.textCursor()
                # 滚动到底部
                textCursor.movePosition(textCursor.End)
                # 设置光标到text中去
                self.rec_data.setTextCursor(textCursor)
        else:
            pass
        return

    def func_data_send(self, button_num):
        if not self.serial.is_open:
            return None
        #空数据不做操作
        input_s = self.send_data_list[button_num].toPlainText()
        if input_s == '':
            return None
        input_temp = input_s
        if (self.send_hex_list[button_num].checkState()):
            #input_s = bytes.fromhex(input_s)   #该方法是将获取到的字符串转换为hex，不符合以hex获取的目的
            input_s = input_s.strip()
            send_list = []
            while input_s != '':
                try:
                    num = int(input_s[0:2], 16)
                except ValueError:
                    QMessageBox.critical(self, 'wrong data', '请输入十六进制数据，以空格分开!')
                    return None
                input_s = input_s[2:].strip()
                send_list.append(num) #在列表末尾添加成员
            input_s = bytes(send_list) #返回一个send_list同长度的初始化数组
        else:
            # ascii发送
            #input_s = (input_s + '\r\n').encode('utf-8')
            input_s = input_s.encode('utf-8')
        print("发送完成，data:",end = "")
        print(input_s)
        #发送逻辑
        num = self.serial.write(input_s)
        self.bit_counter_send += num
        self.counter_send.setText(str(self.bit_counter_send))
        #显示发送的逻辑
        if self.disp_send.isChecked():
            #self.rec_data.setTextColor(self.color_red)
            if self.mask_data_type.isChecked():
                input_temp = 'TX: ' + input_temp
            if self.time_stamp.isChecked():
                temp_time_stamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                input_temp = str(temp_time_stamp) + " " + input_temp
            if (self.pause_dispaly_flag == False):
                input_temp = input_temp + '\n'
                self.rec_data.append(input_temp)
        return None

    def func_timing_send(self, timer_num):
        if (not self.serial.is_open):
            return None
        status = self.timer_list[timer_num].isChecked()
        counter = self.timer_num_list[timer_num].displayText()
        if (counter == ""):
            counter = '1000'
            self.timer_num_list[timer_num].setText(counter)
        counter = int(counter)
        print("进入定时发送函数，参数是:%d, 状态是:%s, 对应数字是:%d " % (timer_num, str(status), counter))
        if (status and counter):
            self.timer_timer[timer_num].start(counter)
        elif (not status):
            self.timer_timer[timer_num].stop()

    def func_disp_ctrl(self):
        print("进入显示控制函数，当前标志位:%d " % self.pause_dispaly_flag)
        if (self.pause_dispaly_flag == True):
            self.pause_dispaly.setText("暂停显示")
            self.pause_dispaly_flag = False
        else:
            self.pause_dispaly.setText("继续显示")
            self.pause_dispaly_flag = True

def main():
    app = QtWidgets.QApplication(sys.argv)

    #ui.setupUi(dialog)
    myshow = Serial_app()
    myshow.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()