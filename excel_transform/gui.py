import sys
import threading
import time
from datetime import datetime

from PyQt5 import QtWidgets

from excel_transform import transform_spreadsheets, logger
from excel_transform.main_window import Ui_MainWindow


def get_qlist_items(qlist):
    return [qlist.item(i).text() for i in range(qlist.count())]


class MainWindow(Ui_MainWindow):
    def setupUi(self, QMainWindow):
        super().setupUi(QMainWindow)
        self.select_source_files_button.clicked.connect(self.select_source_files)
        self.select_mapping_file_button.clicked.connect(self.select_mapping_file)
        self.select_dest_file_button.clicked.connect(self.select_dest_file)
        self.process_files_button.clicked.connect(self.process_files)
        self.clear_messages_button.clicked.connect(self.clear_messages)

    def select_source_files(self):
        file_names, _ = QtWidgets.QFileDialog.getOpenFileNames(None, 'Select Excel files', '', 'Excel Files (*xlsx)')
        self.select_source_files_view.clear()
        self.select_source_files_view.addItems(file_names)

    def select_mapping_file(self):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(None, "Select JSON files", '', 'JSON Files (*json)')
        self.select_mapping_file_view.clear()
        self.select_mapping_file_view.addItem(file_name)

    def select_dest_file(self):
        file_name, _ = QtWidgets.QFileDialog.getSaveFileName(None, 'File Name', '', 'Excel Files (*.xlsx)')
        self.select_dest_file_view.clear()
        self.select_dest_file_view.addItem(file_name)

    def process_files(self):
        self.toggle_input(False)
        message = 'Missing information for the following:'
        error = False
        sources = get_qlist_items(self.select_source_files_view)
        mapping = get_qlist_items(self.select_mapping_file_view)
        output = get_qlist_items(self.select_dest_file_view)
        if not sources:
            message += '\nSource Files'
            error = True
        if not mapping:
            message += '\nMapping File'
            error = True
        if not output:
            message += '\nDestination File'
            error = True
        if error:
            self.write_system_message(message)
            self.toggle_input(True)
        else:
            self.write_system_message('started processing')
            worker_thread = threading.Thread(target=transform_spreadsheets,
                                             args=(sources, mapping[0], output[0]))
            watchdog_thread = threading.Thread(target=self.thread_watchdog, args=(worker_thread,))
            worker_thread.start()
            watchdog_thread.start()

    def clear_messages(self):
        self.message_view.clear()
        self.write_system_message('messages cleared')

    def thread_watchdog(self, thread):
        original_text = self.process_files_button.text()
        text_prefix = 'PROCESSING'
        counter = 0
        while thread.is_alive():
            time.sleep(1)
            counter += 1
            self.process_files_button.setText(f'{text_prefix}' + '.' * (counter % 4))
        self.process_files_button.setText(original_text)
        self.write_system_message('completed processing')
        self.toggle_input(True)

    def toggle_input(self, state):
        self.process_files_button.setEnabled(state)
        self.select_source_files_button.setEnabled(state)
        self.select_mapping_file_button.setEnabled(state)
        self.select_dest_file_button.setEnabled(state)
        self.clear_messages_button.setEnabled(state)

    def write_system_message(self, message):
        current_time = datetime.now().strftime("%H:%M:%S")
        self.message_view.addItem(f'{current_time}:-{message}')
        logger.info(message)


def launch_gui():
    app = QtWidgets.QApplication(sys.argv)
    main_window = QtWidgets.QMainWindow()
    ui = MainWindow()
    ui.setupUi(main_window)
    main_window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    launch_gui()


