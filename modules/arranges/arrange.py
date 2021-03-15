from sqlalchemy.ext.automap import automap_base
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, date
from sqlalchemy.ext.hybrid import hybrid_method
from modules.workers import Worker
from modules.hardware import HardwareUse, Hardware


Base = automap_base()


class ArrangeOperation(Base):
    """
    Arrange operations types:
        1 = Принял(а)
        2 = Сдал(а)
        3 = Передал(а)
    """

    __tablename__ = 'arrange_operations'

    operation_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))


class ArrangeStatus(Base):
    """
    Hardware arrange statuses:
        1 = Свободен
        2 = Используется
    """
    __tablename__ = 'arrange_statuses'

    arr_status_id = Column(Integer, primary_key=True)
    name = Column(String(50))


class ArrangeHardware(Base):
    __tablename__ = 'arranges'

    arrange_id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    hardware_id = Column(Integer, ForeignKey('hardware.hardware_id'))
    employee_id = Column(Integer, ForeignKey('workers.worker_id'))
    operation_id = Column(Integer, ForeignKey('arrange_operations.operation_id'))
    doc_num = Column(Integer)  # Act number
    doc_date = Column(Date, default=date.today)
    worker_id = Column(Integer, ForeignKey('workers.worker_id'))
    employee2_id = Column(Integer, ForeignKey('workers.worker_id'), nullable=True)
    log_date = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    hardware = relationship(Hardware)
    employee = relationship(Worker, foreign_keys=[employee_id])
    employee2 = relationship(Worker, foreign_keys=[employee2_id])
    operation = relationship(ArrangeOperation)
    worker = relationship(Worker, foreign_keys=[worker_id])

    def __init__(self, doc_date, doc_num, hardware_id, employee_id, operation_id, worker_id, session=None, employee2_id=None):
        self.doc_date = doc_date
        self.doc_num = doc_num
        self.hardware_id = hardware_id
        self.employee_id = employee_id
        self.operation_id = operation_id
        self.worker_id = worker_id  # it worker
        self.session = session
        self.employee2_id = employee2_id

        self.hardware_use_inst = HardwareUse(hardware_id, doc_num=doc_num, session=self.session,
                                             employee_id=self.employee_id, doc_date=self.doc_date)

    @hybrid_method
    def create_missing_hardware(self):
        missing_hardware = self.hardware_use_inst.get_missing_hardware()
        if missing_hardware:
            self.hardware_use_inst.create_hardware(missing_hardware)

    @hybrid_method
    def check_hardware_availability(self):
        unavailable_hardware = self.hardware_use_inst.check_availability(self.operation_id)
        if unavailable_hardware:
            print(f'HARDWARE NOT AVAILABLE {unavailable_hardware}')
        return unavailable_hardware

    @hybrid_method
    def perform_arrange(self):
        """
        First we need to change information in the hardware_use table
        :return:
        """
        self.hardware_use_inst.update_use_info(self.operation_id, self.worker_id, self.employee2_id)
        self.arrange_to_worker()

    @hybrid_method
    def arrange_to_worker(self):
        hardware_list = []
        for hd_id in self.hardware_id:

            new_hd = ArrangeHardware(self.doc_date, self.doc_num, hd_id, self.employee_id, self.operation_id,
                                     self.worker_id, employee2_id=self.employee2_id)

            hardware_list.append(new_hd)

        self.session.add_all(hardware_list)
        self.session.commit()
