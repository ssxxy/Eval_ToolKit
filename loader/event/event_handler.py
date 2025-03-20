try : 
    from PySide2.QtWidgets import QApplication, QLabel, QMessageBox, QWidget, QHBoxLayout, QTableWidgetItem, QAbstractItemView
    from PySide2.QtGui import QPixmap, QPainter, QColor, Qt
except Exception :
    from PySide6.QtWidgets import QApplication, QLabel, QMessageBox, QWidget, QHBoxLayout, QTableWidgetItem, QAbstractItemView
    from PySide6.QtGui import QPixmap, QPainter, QColor, Qt
    
import maya.cmds as cmds
import maya.utils as mu
import os, sys
from loader.shotgrid_user_task import ClickedTask
from loader.event.custom_dialog import NewFileDialog
from loader.shotgrid_user_task import UserInfo
from loader.ui.loader_ui import UI as loaderUIClass
from loader.core.add_new_task import *
from systempath import SystemPath
from shotgridapi import ShotgridAPI

from loader.ui.loading_ui import LoadingDialog
from loader.shotgrid_user_task import TaskInfoThread

root_path = SystemPath().get_root_path()
sg = ShotgridAPI().shotgrid_connector()

class LoaderEvent : 
    
    @staticmethod
    def on_login_clicked(ui_instance):                        # 1번 실행중
        """
        로그인 버튼 실행 시 발생하는 이벤트 처리
        """
        user = UserInfo()

        name = ui_instance.name_input.text()
        email = ui_instance.email_input.text()

        if name and email: #이름과 이메일에 값이 있을 때
            is_validate = user.is_validate(email, name)
            if not is_validate:
                popup = QMessageBox()
                popup.setIcon(QMessageBox.Warning)
                popup.setWindowTitle("Failure")
                popup.setText("아이디 또는 이메일이 일치하지 않습니다")
                popup.exec()

            else:  # 로그인 성공!
                ui_instance.close()

                # 로딩창 먼저 띄우기
                ui_instance.loading_window = LoadingDialog()
                ui_instance.loading_window.show()
                QApplication.processEvents()  # UI 즉시 업데이트

                ui_instance.task_thread = TaskInfoThread(user.id)
                ui_instance.task_thread.start()
                ui_instance.task_thread.finished_signal.connect(
                    lambda task_info: LoaderEvent.show_loader_ui(user, name, ui_instance.loading_window, task_info)
                )

        else: # 이름과 이메일에 값이 없을 때
            popup = QMessageBox()
            popup.setIcon(QMessageBox.Warning)
            popup.setWindowTitle("Failure")
            popup.setText("이름과 이메일을 입력해주세요")
            popup.exec()
            
    @staticmethod
    def on_cell_clicked(ui_instance, row, _):
        '''
        task table cell 클릭 발생하는 이벤트 처리 
        '''
        if not ui_instance:
            return
        clicked_task_id = int(ui_instance.task_table.item(row, 2).text()) # SG task id
        
        prev_task_data, current_task_data = ui_instance.task_info.on_click_task(clicked_task_id)
        LoaderEvent.update_prev_work(ui_instance, prev_task_data)

        ct = ClickedTask(current_task_data) # Clicked Task 객체 생성. (클릭 시 마다 갱신)
        pub_path = ct.set_deep_path("pub")
        work_path = ct.set_deep_path("work")
        pub_list = ct.get_dir_items(pub_path)
        work_list = ct.get_dir_items(work_path)
        LoaderEvent.update_pub_table(ui_instance, pub_list) # pub table 업데이트
        LoaderEvent.update_work_table(ui_instance, work_list) # work table 업데이트 
        
        try:
            ui_instance.work_table.cellDoubleClicked.disconnect()
        except Exception as e:
            print(e)
            pass  # 연결된 핸들러가 없을 경우 예외 발생할 수 있음, 무시해도 됨
        
        ui_instance.work_table.cellDoubleClicked.connect(lambda row, col: LoaderEvent.on_work_cell_clicked(ui_instance,ui_instance.work_table, row, col, ct, work_path))
        
    @staticmethod
    def update_pub_table(ui_instance, pub_list):
        '''
        pub table 값 업데이트 함수
        '''
        ui_instance.pub_table.setRowCount(0) # 초기화
        
        for file_info in pub_list:
            LoaderEvent.add_file_to_table(ui_instance.pub_table, file_info)
            
    def update_work_table(ui_instance, work_list):
        '''
        work table 값 업데이트 함수
        '''
        ui_instance.work_table.setRowCount(0)  # Clear existing rows

        for file_info in work_list:
            LoaderEvent.add_file_to_table(ui_instance.work_table, file_info)

    @staticmethod
    def add_file_to_table(table_widget, file_info):
        '''
        각 테이블 위젯에 파일의 정보를 추가하는 함수
        '''
        row = table_widget.rowCount()
        table_widget.insertRow(row)
        
        table_widget.setHorizontalHeaderLabels(["", "파일 이름", "최근 수정일"])
        table_widget.setSelectionBehavior(QAbstractItemView.SelectRows) 
        table_widget.setColumnWidth(0, 30) 
        table_widget.setColumnWidth(1, 330)  
        table_widget.setColumnWidth(2,150)
        table_widget.verticalHeader().setDefaultSectionSize(30)
        table_widget.horizontalHeader().setVisible(True) 
        table_widget.verticalHeader().setVisible(False)

        image_label = QLabel()
        pixmap = QPixmap(file_info[0]).scaled(25, 25)
        image_label.setPixmap(pixmap) # DCC 아이콘
        image_label.setAlignment(Qt.AlignCenter)
        table_widget.setCellWidget(row, 0, image_label)

        # File name or message
        file_item = QTableWidgetItem(file_info[1]) # 파일이름
        table_widget.setItem(row, 1, file_item)

        time_item = QTableWidgetItem(file_info[2]) # 최근 수정일
        table_widget.setItem(row, 2, time_item)

    @staticmethod
    def on_work_cell_clicked(ui_instance, table_widget, row, col, ct, path):
        '''
        work table cell 클릭 발생하는 이벤트 처리.
        파일이 없을 시 NewFileDialog 호출 , 있을 시 파일을 열고 SideWidget를 실행하는 함수가 실행됨.
        '''
        from widget.ui.widget_ui import add_widget_to_tab

        item = table_widget.item(row, 1)

        if item.text() == "No Dir No File":
            is_dir, is_created = False, False
            if not is_created :
                dialog = NewFileDialog(path, is_dir, is_created, ct)
                dialog.exec()
                # mainwindow 종료
                ui_instance.close()

        elif item.text() ==  "No File" :
            is_dir, is_created = True, False
            if not is_created :
                dialog = NewFileDialog(path, is_dir,is_created, ct)
                dialog.exec()
                ui_instance.close()

        else :
            full_path = f"{path}/{item.text()}"
            cmds.file(full_path, open=True, force=True)
            ui_instance.close()

            add_widget_to_tab(path, ct)
        
